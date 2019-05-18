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
from vehicle.v2v import V2V
from vehicle import led_display
import _thread
import threading
import signal

class UAV(Vehicle)

	def __init__(self, *args):

        super(UAV, self).__init__(*args)
        self.sendDict = {}

    def toJSON(self):
        #Why do I even have this??
        return json.dumps(self.sendDict, default=lambda o: o.__dict__)

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

class OVS:

	def __init__(self):

		self.telem_broadcast_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
		self.telem_broadcast_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
		self.telem_broadcast_sock.settimeout(0.2)
		self.telem_broadcast_sock.bind(("", 55000))

	def connect_to_vehicle(self):

		try:
			self.uav = connect("/dev/ttyS0", wait_ready=True, baud=57600, vehicle_class=UAV)		
		except:
			self.uav = DummyDrone()	
		self.lon, self.lat, self.alt = self.uav.updateUAVGPS()

	def broadcast_telem(self):
		

		self.lon, self.lat, self.alt = self.uav.updateUAVGPS()
		_msg = {
				"lon" : self.lon,
				"lat" : self.lat,
				"alt" : self.alt
				}
		self.telem_broadcast_sock.sendto(_msg, ('<broadcast>', LISTENING_TELEM_PORT))

	def recieve_gcs_message(self):
		#recieve stuff



def main():
	ovs = OVS()

if __name__ == '__main__':
	LISTENING_TELEM_PORT = 55001
	main() 