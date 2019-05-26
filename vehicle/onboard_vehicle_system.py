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

import argparse

TELEM_PORT = 55001
GCS_INSTRUCTIONS_PORT = 55002

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

	'''
	param vehicle_type: string for vehicle type e.g. MULTI_ROTOR
	param network_type: string for type of network connetion e.g. silvus, batman, wifi..
	param display: for future i2c display. not used now
	param kill: for sigterm kill object. not used now
	param measuring: not used.

	'''

	def __init__(self, vehicle_type, name, network_type, display, kill):

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
		self.update_rate = 1

		self.network_type = network_type
		self.kill = kill
		self.agent_lock = threading.Lock()
		self.agents = {}
		self.identify_peripherals()


	def identify_peripherals(self):
		''' need to redo this since no longer using ACM'''

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
		self.gcs_listening_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
		self.gcs_listening_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.gcs_listening_sock.bind((self.ip, GCS_INSTRUCTIONS_PORT))

	def connect_to_flight_controller(self):
		'''method for connecting to flight controller. must be connecting to flight controller via UART to telemetry port'''
		
		try:
			print(">>> Connecting to flight controller.")
			#connected object from dronekit library stored in uav
			self.uav = connect("/dev/ttyS0", wait_ready=True, baud=57600)		
		except:
			self.uav = "dummy"
		self.lon, self.lat, self.alt = self.update_uav_gps()


	def update_uav_gps(self):
		'''method for grabbing gps from flight controller'''
		if self.uav == "dummy":
			return (0, 0, 0)
		else:
			global_loc = self.uav.location.global_frame
		return (global_loc.lon, global_loc.lat, global_loc.alt)

	def broadcast_telem(self):
		''' 
		method for taking gps from flight controller, formatting data in JSON,
		and sending a UDP broadcast to all TELEM_PORTs on network
		'''
		
		while not self.kill.kill:

			tic = time.time()
			self.lon, self.lat, self.alt = self.update_uav_gps()
			#msg format used for telemetry broadcasts
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
		'''method for recieving direct messages from gcs. gcs sends instructions.'''
		
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
				elif _instructions[0] == 'measure_throughput':
					print("Measuring network performance.")
					#gcs will create a iperf3 client and try to connect to uav to measure performance, we need to create a iperf3 server
					self.start_iperf3_server()
			except Exception as e:
				print(e)
				pass

	def start_iperf3_server(self):
		#creates an iperf3 server. only lasts for one measurement. putting in a while 1 causes udp problems
		print("Starting iperf server for throughput")
		server = iperf3.Server()
		server.bind_address = self.ip 
		server.port = 6969
		server.verbose = False
		server.run()


	def vehicle_to_vehicle(self):
		'''
		method for listening to other telemetry udp broadcasts
		currently doesnt do anything other than store information in an agents dictonary, but 
		additional logic can easily be added
		'''
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
		self.vehicle_to_vehicle_telem_sock.close()

	def init_flight(self, new_flight, addr):
		'''method for adding new flights to agents dict'''
		
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

