#!/usr/bin/env python3

import socket
import time

def main(ip):
	server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
	server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)


	server.settimeout(0.2)
	server.bind(("", 55000))
	while True:
		msg = ("hello buddy").encode("utf-8")
		server.sendto(msg, ('<broadcast>', 55001))
		time.sleep(1)
if __name__ == '__main__':
	main()