#!/usr/bin/env python3
import socket
import time
import json
from onesky_api import OneSkyAPI
import threading
import sys, getopt
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
class GroundControl:

	def __init__(self, onesky_api):
		#client for listening to incoming broadcasts from UAVS
		self.gcs_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.gcs_client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
		self.gcs_client.bind(("", TELEM_PORT))
		#agents dictionary for keeping track of what UAVs are broadcasting
		self.agents = {}
		#onesky api obj
		self.onesky = onesky_api

	def listen(self):

		while True:
			try:
				_data, addr = self.gcs_client.recvfrom(1024)
				data = json.loads((_data).decode("utf-8"))
				if data["name"] not in self.agents:
					self.init_flight(data)
				
				self.agents[data["name"]]["lon"] = data["lon"]
				self.agents[data["name"]]["lat"] = data["lat"]
				self.agents[data["name"]]["alt"] = data["alt"]
												
			except Exception as e:
				print(e)
				pass

	def init_flight(self, new_flight):
		#init that flight boi
		gufi = self.onesky.createPointFlight(new_flight["name"], new_flight["lon"], new_flight["lat"], new_flight["alt"])
		self.agents[new_flight["name"]] = {
												"lon" : new_flight["lon"],
												"lat" : new_flight["lat"],
												"alt" : new_flight["alt"],
												"vehicle_type" : new_flight["vehicle_type"],
												"gufi" : gufi
											}
	def update_telemetry(self):

		while True:
			for uav in self.agents:			
				print(self.agents[uav])
				self.onesky.updateTelemetry(self.agents[uav]["gufi"], self.agents[uav]["lon"], 
											self.agents[uav]["lat"], self.agents[uav]["alt"])

def main():
	with open("mwalton.token", "r") as toke:
		token = toke.read()
	onesky_api = OneSkyAPI(token)
	gcs = GroundControl(onesky_api)
	threading.Thread(target=gcs.listen).start()
	threading.Thread(target=gcs.update_telemetry).start()

if __name__ == '__main__':
	TELEM_PORT = 55001
	GCS_INSTRUCTIONS_PORT = 55002
	main()