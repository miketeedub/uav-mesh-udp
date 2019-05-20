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

	def __init__(self, vehicle_type, name, network_type, display, kill):

		#socket for broadcasting telemetry to gcs
		self.telem_broadcast_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
		self.telem_broadcast_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
		self.telem_broadcast_sock.settimeout(0.2)
		self.telem_broadcast_sock.bind(("", 55000))
		
		self.vehicle_type = vehicle_type
		self.name = name
		self.update_rate = 5

		self.network_type = network_type
		self.kill = kill
		self.identify_peripherals()

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

		#socket for listening to gcs commands
		self.gcs_listening_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
		self.gcs_listening_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.gcs_listening_sock.bind((self.ip, GCS_INSTRUCTIONS_PORT))

	def connect_to_vehicle(self):
		
		try:
			self.uav = connect("/dev/ttyS0", wait_ready=True, baud=57600, vehicle_class=UAV)		
		except:
			self.uav = DummyDrone()	
		self.lon, self.lat, self.alt = self.uav.updateUAVGPS()

	def broadcast_telem(self):
		
		while not self.kill.kill:

			tic = time.time()
			self.lon, self.lat, self.alt = self.uav.updateUAVGPS()
			_msg = {
					"name" : self.name,
					"vehicle_type" : self.vehicle_type,
					"lon" : self.lon,
					"lat" : self.lat,
					"alt" : self.alt
					}
			self.telem_broadcast_sock.sendto(json.dumps(_msg).encode("utf-8"), ('<broadcast>', TELEM_PORT))
			toc = time.time() - tic
			try:
				time.sleep((1 / self.update_rate)  - toc)
			except:
				pass

	def recieve_gcs_message(self):
		while not self.kill.kill:
			try:
				_data = self.gcs_listening_sock.recv(1024)
				data = json.loads(_dat.decode("utf-8"))

				if data["update_rate"]:			
					self.update_rate = data["update_rate"]
				if data["capture_network_performance"]:
					self.measure_network_performance()
			except Exception as e:
				print(e)
				pass

	def measure_network_performance(self):
		pass

