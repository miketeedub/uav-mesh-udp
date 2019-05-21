#!/usr/bin/env python3
import sys, getopt
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import socket
import time
import json
from gcs.onesky_api import OneSkyAPI
import threading


TELEM_PORT = 55001
GCS_INSTRUCTIONS_PORT = 55002

class GroundControl:

	def __init__(self, onesky_api, host_ip):
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
		#ip address for sending commands to vehicles
		self.gcs_send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
		self.user_input = None
		
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
				
				if data["name"] not in self.agents:
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
				_temp_agent_dict = self.agents
				_temp_agent_dict_2 = self.agents
			for uav in _temp_agent_dict:	

				self.onesky.updateTelemetry(_temp_agent_dict_2[uav]["gufi"], _temp_agent_dict_2[uav]["lon"], 
											_temp_agent_dict_2[uav]["lat"], _temp_agent_dict_2[uav]["alt"])

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
					_temp_agent_dict = self.agents
				try:
					_user_input = self.user_input.split(" ")
					if _user_input[0] == 'quit':					
						self.kill.kill = True					
					if _user_input[0] == 'agents':
						for uav in _temp_agent_dict:
							print(">>> {} : {}".format(uav, _temp_agent_dict[uav]["ip"]))
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
		self.gcs_send_sock.sendto(json.dumps({"change": [parameter, new_value]}).encode("utf-8"),(_ip, GCS_INSTRUCTIONS_PORT))	
	

def main():

	with open("mwalton.token", "r") as toke:
		token = toke.read()
	onesky_api = OneSkyAPI(token)
	gcs = GroundControl(onesky_api)
	threading.Thread(target=gcs.listen).start()
	gcs.update_telemetry()

if __name__ == '__main__':
	
	main()