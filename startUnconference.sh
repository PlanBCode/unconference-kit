#!/bin/bash


cd /home/pi
./make_dirs.sh
rm unc.log
sleep 2
while true; do
sudo dtparam spi=off
sudo killall raspivid
sudo killall ffmpeg
sudo killall picam
sudo python unconference.py >>unc.log 2>&1

 sleep 1
done
