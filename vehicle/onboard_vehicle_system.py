#!/usr/bin/env python3

import socket
import time
import sys, getopt
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import json
import time
from dronekit import Vehicle, connect
import select
import subprocess
import _thread
import threading
import signal
import iperf3

TELEM_PORT = 55001
GCS_INSTRUCTIONS_PORT = 55002


class UAV(Vehicle):


	def __init__(self, *args):

		super(UAV, self).__init__(*args)
		self.sendDict = {}

	def updateUAVGPS(self):
		#grabs the GPS stuff from the flight controller
		self.global_loc = self.location.global_frame
		return (self.global_loc.lon, self.global_loc.lat, self.global_loc.alt)

class DummyDrone:
	'''
	just for testing purposes
	'''
	def __init__(self):
		self.lon = 0
		self.lat = 0
		self.alt = 0

	def updateUAVGPS(self):
		return (self.lon, self.lat, self.alt)

class OnboardVehicleSystem:

	def __init__(self, vehicle_type, name, network_type, display, kill, measuring):

		#socket for broadcasting telemetry to gcs
		self.telem_broadcast_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
		self.telem_broadcast_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
		self.telem_broadcast_sock.settimeout(0.4)
		self.telem_broadcast_sock.bind(("", 55000))

		#socket for listening to other vehicle telemetry
		self.vehicle_to_vehicle_telem_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.vehicle_to_vehicle_telem_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
		self.vehicle_to_vehicle_telem_sock.bind(("", TELEM_PORT))
		
		self.vehicle_type = vehicle_type
		self.name = name
		self.gufi = ""
		self.update_rate = 5

		self.network_type = network_type
		self.kill = kill
		self.agent_lock = threading.Lock()
		self.agents = {}
		self.identify_peripherals()

		if measuring:
			threading.Thread(target=self.start_iperf3_server).start()

	def start_iperf3_server(self):

		print("Starting iperf server for throughput")
		server = iperf3.Server()
		server.bind_address = self.ip 
		server.port = 6969
		server.verbose = False
		while True:
			try:
				server.run()
			except:
				self.start_iperf3_server()

	def identify_peripherals(self):

		print("Connecting to Flight Controller")
		subprocess.call(['../utils/./sysinfo.sh'])
		self.peripherals = [line.rstrip('\n') for line in open('sysdisc.txt')]
		self.ethernet_ip = self.peripherals[2]
		self.batman_ip = self.peripherals[3]
		self.wlan0 = self.peripherals[4]

		if self.network_type == "batman":
			self.ip = self.batman_ip
		elif self.network_type =="silvus":
			self.ip = self.ethernet_ip
		elif self.network_type == "wifi":
			self.ip = self.wlan0
		elif self.network_type == "ethernet":
			self.ip = self.ethernet_ip
		print(self.ip, self.network_type)


		#socket for listening to gcs commands
		self.gcs_listening_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)#, socket.IPPROTO_UDP)
		# self.gcs_listening_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.gcs_listening_sock.bind((self.ip, GCS_INSTRUCTIONS_PORT))

	def connect_to_flight_controller(self):
		self.uav = DummyDrone()	
		self.lon, self.lat, self.alt = self.uav.updateUAVGPS()
		# try:
		# 	print(">>> Connecting to flight controller.")
		# 	self.uav = connect("/dev/ttyS0", wait_ready=True, baud=57600, vehicle_class=UAV)		
		# except:
		# 	self.uav = DummyDrone()	
		# self.lon, self.lat, self.alt = self.uav.updateUAVGPS()

	def broadcast_telem(self):
		
		while not self.kill.kill:

			tic = time.time()
			self.lon, self.lat, self.alt = self.uav.updateUAVGPS()
			_msg = {
					"name" : self.name,
					"vehicle_type" : self.vehicle_type,
					"gufi" : self.gufi,
					"lon" : self.lon,
					"lat" : self.lat,
					"alt" : self.alt
					}
			try:
				self.telem_broadcast_sock.sendto(json.dumps(_msg).encode("utf-8"), ('<broadcast>', TELEM_PORT))
			except:
				pass
			toc = time.time() - tic
			try:
				time.sleep((1 / self.update_rate)  - toc)
			except:
				pass

	def recieve_gcs_message(self):
		
		while not self.kill.kill:
			try:
				_data = self.gcs_listening_sock.recv(10240*2)
				data = json.loads(_data.decode("utf-8"))
				_instructions = data['change']
				if _instructions[0] == 'rate':
					self.update_rate = _instructions[1]
					print("Adjusted update rate to {}.".format(_instructions[1]))
				elif _instructions[0] == 'gufi':
					self.gufi = _instructions[1]
					print(">>> GUFI set to " + self.gufi)
				elif _instructions[0] == 'measure_conn':
					print("Measuring network performance.")
					self.measure_network_performance()
			except Exception as e:
				print(e)
				pass

	def vehicle_to_vehicle(self):

		while not self.kill.kill:
			
			_data, addr = self.vehicle_to_vehicle_telem_sock.recvfrom(1024)
			data = json.loads((_data).decode("utf-8"))
			try:
				if data["name"] != self.name:
					if data["name"] not in self.agents:
						self.init_flight(data, addr)
					
					self.agents[data["name"]]["lon"] = data["lon"]
					self.agents[data["name"]]["lat"] = data["lat"]
					self.agents[data["name"]]["alt"] = data["alt"]
					self.agents[data["name"]]["gufi"] = data["gufi"]
													
			except Exception as e:
				print(e)
				pass

	def init_flight(self, new_flight, addr):
		#init that flight boi
		
		self.agents[new_flight["name"]] = {
												"lon" : new_flight["lon"],
												"lat" : new_flight["lat"],
												"alt" : new_flight["alt"],
												"vehicle_type" : new_flight["vehicle_type"],
												"gufi" : new_flight["gufi"],
												"ip" : addr[0],
											}
		print("\n>>> " + new_flight["name"] + " connected at " + addr[0] + "\n>>> ", end = '')

	def measure_network_performance(self):
		pass

