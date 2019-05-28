#!/usr/bin/env bash

sudo apt-get upgrade &&
sudo apt-get dist-upgrade &&
sudo setxkbmap us &&
sudo apt-get install python-dev &&
sudo apt-get install libxml2 ;
sudo apt-get install libxml2-dev libxslt-dev ;
sudo apt-get install libzbar-dev libzbar0 ;
sudo apt-get install python3-lxml &&
sudo pip3 install lxml &&
sudo apt-get install batmand &&
sudo apt-get install batctl &&
sudo pip3 install dronekit &&
#dronekit uses an older version of pymavlink that has a python3 issue
sudo pip3 uninstall pymavlink &&
sudo pip3 install pymavlink &&
sudo pip3 install Adafruit-SSD1306 &&
sudo apt-get install -y i2c-tools &&
sudo apt-get install python-imaging python-smbus &&
sudo apt-get install iperf3 &&
sudo pip3 install iperf3
