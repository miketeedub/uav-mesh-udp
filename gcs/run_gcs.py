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
	ethernet_ip, batman_ip, wlan0 = ips[2], ips[3], ips[4]

	opts, args = getopt.getopt(argv, "ebws", ["ethernet", "batman", "wifi", "silvus"])

	host = ""
	for opt, arg in opts:
		if opt == '-e' or opt == '-s':
			host = ethernet_ip
		if opt == '-b':
			host = batman_ip
		if opt == '-w':
			host = wlan0
	if host == "":
		print("Please select ethernet, silvus, batman, or wifi with -e, -s, -b, -w")
		sys.exit(0)


	onesky = OneSkyAPI(token)
	gcs = GroundControl(onesky, host)
	gcs.run()

if __name__ == '__main__':
	main(sys.argv[1:])