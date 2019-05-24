#!/usr/bin/env python3


import sys, getopt
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import multiprocessing as mp
import threading
from gcs.ground_control import GroundControl
from gcs.onesky_api import OneSkyAPI
from utils.system_killer import Killer
import subprocess



def main(argv):
	with open("mwalton.token", "r") as toke:
		token = toke.read()
	subprocess.call(['../utils/./find_ip.sh'])
	ips = [line.rstrip('\n') for line in open('ip.txt')] 
	ethernet_ip, batman_ip, wlan0 = ips[0], ips[1], ips[2]
	opts, args = getopt.getopt(argv, "ebwsmr:", ["ethernet", "batman", "wifi", "silvus", "measure", "radioIP"])
	host = ""
	measuring = False
	silvus_ip = None
	silv = False
	for opt, arg in opts:
		if opt == '-e': 
			host = ethernet_ip
		if opt == '-s':
			host = ethernet_ip
			silv = True
		if opt == '-b':	
			host = batman_ip
		if opt == '-w':
			host = wlan0
		if opt == '-m':
			measuring = True
		if opt == '-r':
			silvus_ip = arg
	if silv and measuring and not silvus_ip:
		print("Please include the IP address on the back of the radio when using silvus if measuring network performance")
		sys.exit(0)
	if host == "":
		print("Please select ethernet, silvus, batman, or wifi with -e, -s, -b, -w")
		sys.exit(0)


	onesky = OneSkyAPI(token)
	gcs = GroundControl(onesky, host, measuring, silvus_ip)
	gcs.run()

if __name__ == '__main__':

	main(sys.argv[1:])