
# uav-mesh-udp

This project acts as a UAV fleet management system that interfaces with [OneSky's](https://onesky.xyz/) USS using mesh networking. 

## Getting Started

The project is based into two systems: the on board vehicle system, and the ground control station.
The onboard vehicle system runs on a Raspberry Pi, and connects to the Pixhawk's telemetry port

## Setting up the Rasperry Pi

We'll need some dependencies to run the on board vehicle software. The shell script, "install_client.sh" is intended to be ran 
following a fresh raspbian install, and will update apt-get and install the necessary dependencies.

The Raspberry Pi will connect to the Pixhawk telemetry port 2, and instructions to do so can be found on the ardupilot website [here](http://ardupilot.org/dev/docs/raspberry-pi-via-mavlink.html). 

If running a Raspberry Pi 3b+, ignore the directions regarding /boot/cmdline.txt





