from MPUStepDetector import MPUStepDetector
from microphone import microphoneDetector
import time



def micCallback(stepDuration): # callback function
    print("mic with duration: ",stepDuration)

def mpuCallback(stepDuration): # callback function
    print("mpu with duration: ",stepDuration)


print("starting MPU...")
mpuDetector = MPUStepDetector(0x68)
mpuDetector.enableFilter(False)
mpuDetector.calibrate()
mpuDetector.setCallback(mpuCallback)
mpuDetector.startAsync()

print("starting MIC...")
micDetector = microphoneDetector(filter=True)
micDetector.setCallback(micCallback)
micDetector.calibrate()
micDetector.startAsync()

print("done")
time.sleep(60)
mpuDetector.stopAsync()#signal stop event after 60s to exit thread in library
micDetector.stopAsync()#signal stop event after 60s to exit thread in library

#micDetector.stopAsync