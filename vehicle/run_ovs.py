#!/usr/bin/env python3

import sys, getopt
import socket
import os
import signal
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from vehicle.onboard_vehicle_system import OnboardVehicleSystem
from utils.system_killer import Killer
import threading

def main(argv):

	display = True
	batman = False
	try:
		opts, args = getopt.getopt(argv, "ewsbhn:d", ["ethernet","wifi","silvus","batman","help","name=","disableDisplay"])

	except Exception as e:
		print("-n <name> -d disables LED output")
		print(e)
		sys.exit(0)

	name = None
	network_type = None
	for opt, arg in opts:
		if opt == "-h":
			print("-n <name> -d disables LED output")
			sys.exit()
		if opt in ('-n', "--name"):
			name = arg
		if opt in ('-d', "--disableDisplay"):
			display = False
			print("LED display is disabled")
		if opt in ('-b', "--batman"):
			network_type = "batman"
		if opt == "-s":
			network_type = "silvus"
		if opt == "-w":
			network_type = "wifi"
		if opt == "-e":
			network_type = "ethernet"
	if network_type == None:
		print("Please enter -b, -w, -e, -s for network type")
		sys.exit(0)
	if name == None:
		print("Using hostname as UAV name!")
		name = socket.gethostname()


	kill = Killer()

	ovs = OnboardVehicleSystem("MULTI_ROTOR", name, network_type, display, kill)
	ovs.connect_to_flight_controller()
	threading.Thread(target=ovs.broadcast_telem).start()
	threading.Thread(target=ovs.vehicle_to_vehicle).start()
	ovs.recieve_gcs_message()
	ovs.gcs_listening_sock.close()


if __name__=="__main__":

	main(sys.argv[1:])
	print("Exiting OVS")
	sys.exit(0)