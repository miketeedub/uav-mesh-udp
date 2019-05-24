#!/usr/bin/env python3
import sys, getopt
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import socket
import time
import json
from gcs.onesky_api import OneSkyAPI
import threading
import iperf3
import requests

TELEM_PORT = 55001
GCS_INSTRUCTIONS_PORT = 55002

class GroundControl:

	def __init__(self, onesky_api, host_ip, measuring, silvus_ip):
		#client for listening to incoming broadcasts from UAVS
		self.gcs_recv_telem_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.gcs_recv_telem_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
		self.gcs_recv_telem_sock.bind(("", TELEM_PORT))
		#agents dictionary for keeping track of what UAVs are broadcasting
		self.agents = {}
		#onesky api obj
		self.onesky = onesky_api
		#create lock for agents dictionary
		self.agent_lock = threading.Lock()
		#create lock for using sending socket
		self.udp_send_lock = threading.Lock()
		#ip address for sending commands to vehicles
		self.gcs_send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)#, socket.IPPROTO_UDP)
		self.user_input = None
		self.ip = host_ip
		#this is for measuring throughput with iperf3
		self.silvus_ip = silvus_ip
		if silvus_ip:
			self.init_silvus_requests()
		


	


				
	def run(self):

		threading.Thread(target=self.listen).start()
		threading.Thread(target=self.user_input_loop).start()
		threading.Thread(target=self.user_interface).start()
		threading.Thread(target=self.update_telemetry).start()	

	def listen(self):

		while True:
			try:
				_data, addr = self.gcs_recv_telem_sock.recvfrom(1024)
				data = json.loads((_data).decode("utf-8"))
				with self.agent_lock:
					_temp_agent_dict = self.agents.copy()
				if data["name"] not in _temp_agent_dict:
						self.init_flight(data, addr)
				with self.agent_lock:				
					self.agents[data["name"]]["lon"] = data["lon"]
					self.agents[data["name"]]["lat"] = data["lat"]
					self.agents[data["name"]]["alt"] = data["alt"]												
			except Exception as e:
				print(e)
				pass


	def init_flight(self, new_flight, addr):
		#init that flight boi
		gufi = self.onesky.createPointFlight(new_flight["name"], new_flight["lon"], new_flight["lat"], new_flight["alt"])		
		with self.agent_lock:
			self.agents[new_flight["name"]] = {
													"lon" : new_flight["lon"],
													"lat" : new_flight["lat"],
													"alt" : new_flight["alt"],
													"vehicle_type" : new_flight["vehicle_type"],
													"ip" : addr[0],
													"gufi" : gufi
												}
		self.send_instructions(new_flight["name"], 'gufi', gufi)
		print("\n>>> " + new_flight["name"] + " connected at " + addr[0] + "\n>>> ", end = '')

	def update_telemetry(self):

		while True:
			with self.agent_lock:
				_temp_agent_dict = self.agents.copy()
			v = [value for key, value in _temp_agent_dict.items()]	
			for uav in v:
				self.onesky.updateTelemetry(uav["gufi"], uav["lon"], uav["lat"], uav["alt"])

	def user_input_loop(self):

		while True:
			try:  
				self.user_input = input(">>> ")  
				time.sleep(.01)
			except EOFError:
				pass

	def user_interface(self):
		
		while True:
			if self.user_input:
				with self.agent_lock:
					_temp_agent_dict = self.agents.copy()
				try:
					_user_input = self.user_input.split(" ")
					if _user_input[0] == 'quit':					
						self.kill.kill = True					
					if _user_input[0] == 'agents':
						for uav in _temp_agent_dict:
							print(">>> {} : {}".format(uav, _temp_agent_dict[uav]["ip"]))
					if _user_input[0] == 'measure':
						if _user_input[1] in _temp_agent_dict:			
							self.measure_connection_performance(_user_input[1],_temp_agent_dict[_user_input[1]]["ip"])
					if _user_input[0] in _temp_agent_dict:
						if _user_input[1] == 'ip':
							print(">>> " + _temp_agent_dict[_user_input[0]]["ip"])
						if _user_input[1] == 'type':
							print(">>> " + _temp_agent_dict[_user_input[0]]["vehicle_type"])												
					if _user_input[0] == 'set' and len(_user_input) == 4:
									            # name          #parameter       #newvalue
						self.send_instructions(_user_input[1], _user_input[2], _user_input[3])		
				except Exception as e:
					print(e)

				self.user_input = None

	def send_instructions(self, name, parameter, new_value):
		
		with self.agent_lock:
			_ip = self.agents[name]["ip"]
		with self.udp_send_lock:
			self.gcs_send_sock.sendto(json.dumps({"change": [parameter, new_value]}).encode("utf-8"),(_ip, GCS_INSTRUCTIONS_PORT))	
	


	def init_silvus_requests(self):
		
		self.silvus_session = requests.Session()
		self.streamscape_uri = "http://"+self.silvus_ip+"/streamscape_api"
		self.silvus_snr_measurment_msg = '''{"jsonrpc":"2.0", "method" : "network_status","id":"0"}'''


	def init_iperf3_client(self, ip):

		iperf_client = iperf3.Client()
		iperf_client.duration = 1
		iperf_client.server_hostname = ip
		iperf_client.port = 6969
		iperf_client.protocol = 'udp'

		return iperf_client




	def measure_connection_performance(self, name, ip):

		#TODO: need to include the silvus id# in this later to target specific radios, since there's only one radio its not a problem
		print(">>> Recording throughput and SNR from {} at {} \n>>> ".format(name,ip), end = '')	

		while True:
			#I can't figure out how to reuse the same client so we're just remaking it every time
			client = self.init_iperf3_client(ip)
			try:
				response = self.silvus_session.post(self.streamscape_uri, data=self.silvus_snr_measurment_msg, stream=True)
				data = json.loads(response.content.decode("utf-8"))
				snr = int(data["result"][2])
				print(snr)
			except:
				pass
			try:				
				result = client.run()
				throughput = result.Mbps
				print(throughput)
			except Exception as e:
				print("this is the exception:")
				print(e)

			#it has to be removed from memory for some reason
			client = None
			time.sleep(2)




def main():

	with open("mwalton.token", "r") as toke:
		token = toke.read()
	onesky_api = OneSkyAPI(token)
	gcs = GroundControl(onesky_api)
	threading.Thread(target=gcs.listen).start()
	gcs.update_telemetry()

if __name__ == '__main__':
	
	main()