#! /bin/bash

echo "Checking and installing dependencies for the T-UGS"
sudo apt-get install portaudio19-dev libatlas-base-dev python3-scipy -y 
pip install pyaudio pylabs matplotlib seaborn smbus mpu6050-raspberrypi

### Notes regarding audio ###
# Note 1:
# It is very important to install pyadio versio >=0.2.12 as older versions are not working correctly with newer python versions
# Check with `pip show pyaudio`
# Note 2:
# Our microphone gets initialized with a very low gain in alsa; Check input levels and adjust to 100% with alsamixer or pavucontrol (GUI; available in the repos)