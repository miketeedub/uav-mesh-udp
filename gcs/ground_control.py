#!/usr/bin/env python3
import socket
import time

def main():

	client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
	client.bind(("", 55001))
	while True:
		data, addr = client.recvfrom(1024)
		print(data.decode("utf-8"))

if __name__ == '__main__':
	main()