from MPUStepDetector import MPUStepDetector
import time



def testCallback(stepDuration): # callback function
    print("step with duration: ",stepDuration)


mpuDetector = MPUStepDetector(0x68)
mpuDetector.setCallback(testCallback)
mpuDetector.calibrate()
mpuDetector.startAsync()#start thread in library
time.sleep(60)
mpuDetector.stopAsync()#signal stop event after 60s to exit thread in library