#! /bin/bash

echo "Checking and installing dependencies for the T-UGS"
sudo apt-get install portaudio19-dev libatlas-base-dev python3-scipy -y 
pip install pyaudio pylabs matplotlib seaborn smbus mpu6050-raspberrypi librosa 
