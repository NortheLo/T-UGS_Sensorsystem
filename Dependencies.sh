#! /bin/bash

echo "Checking and installing dependencies for the T-UGS"
sudo apt-get install portaudio19-dev -y 
pip install pyaudio pylabs matplotlib scipy seaborn smbus mpu6050-raspberrypi