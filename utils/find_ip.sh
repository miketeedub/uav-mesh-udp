#!/bin/bash

for conns in eth0 bat0 wlan0 wlp
do
    address=$(ifconfig | grep -A1 $conns | grep inet | tr -d 'inet' | sed 's/.mask.*//' | tr -d  ' ')   
    if [ -z  $address ]; then
	echo "None" >> "ip.txt"
    else
	echo $address >> "ip.txt"
    fi
done

echo hostname >> "ip.txt"