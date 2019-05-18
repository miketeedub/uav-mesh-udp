#!/usr/bin/env python3
import socket
import time



def main():

	gcs_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	gcs_client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
	gcs_client.bind(("", 55001))
	
	while True:
		data, addr = gcs_client.recvfrom(1024)
		print(data.decode("utf-8"))

if __name__ == '__main__':
	main()