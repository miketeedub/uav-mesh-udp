#!/bin/bash

sudo rm "sysdisc.txt"
#Find out what type of flight controller and which ttyACM it's on
for VARIABLE in 0 1 2 3 4 5 6
do
    if udevadm info --query=all --name=/dev/ttyACM$VARIABLE | grep --q "Arduino_Mega"; then
    touch "sysdisc.txt"
    echo "/dev/ttyACM""$VARIABLE" >> "sysdisc.txt"
    echo "ardupilot" >> "sysdisc.txt"
    break
    elif udevadm info --query=all --name=/dev/ttyACM$VARIABLE | grep --q "3D_Robotics_PX4"; then
    touch "sysdisc.txt"
    echo "/dev/ttyACM""$VARIABLE" >> "sysdisc.txt"
    echo "pixhawk" >> "sysdisc.txt"
    break
    fi
    

    if [ $VARIABLE == 6 ]; then
    echo -e $"None\nNone" >> "sysdisc.txt"
    fi
done
#Pull all the IP address 
for conns in eth0 bat0 wlan0 wlp
do
    address=$(ifconfig | grep -A1 $conns | grep inet | tr -d 'inet' | sed 's/.mask.*//' | tr -d  ' ')   
    if [ -z  $address ]; then
	echo "None" >> "sysdisc.txt"
    else
	echo $address >> "sysdisc.txt"
    fi
done

echo hostname >> "sysdisc.txt"

