from MPUStepDetector import MPUStepDetector
from microphone import microphoneDetector
import datetime
import time

###Settings###
TIME_TOLERANCE_DURATION = 100 #ms
TIME_TOLERANCE_DELAY = 100 #ms
MODE="AND"
##############

tsMic=datetime.datetime.now()
tsMpu=datetime.datetime.now()
dMic=0
dMpu=0
lastStep=datetime.datetime.now()
countMic=0
countMpu=0
countCombined=0

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'



def micCallback(stepDuration): # callback function
    global tsMic,countMic
    print(bcolors.OKBLUE+"mic with duration: " + str(stepDuration) + bcolors.ENDC)
    tsMic=datetime.datetime.now()
    countMic+=1
    StepDetected(durationMic=stepDuration)

def mpuCallback(stepDuration): # callback function
    global tsMpu,countMpu
    print(bcolors.OKGREEN+"mpu with duration: " + str(stepDuration) + bcolors.ENDC)
    tsMpu=datetime.datetime.now()
    countMpu+=1
    StepDetected(durationMpu=stepDuration)

def StepDetected(durationMic=0,durationMpu=0):
    global dMic,dMpu,lastStep,countCombined,countMpu,countMic

    timeError=abs((tsMic-tsMpu).total_seconds())*1000

    if MODE == "AND":
        if(durationMic!=0):
            dMic=durationMic
        if(durationMpu!=0):
            dMpu=durationMpu
        print(timeError)
        if(timeError > TIME_TOLERANCE_DELAY):
            return
        if(dMpu > 0 and dMic > 0):
            print(abs(dMic-dMpu))
            if(abs(dMic-dMpu) < TIME_TOLERANCE_DURATION):
                print(bcolors.FAIL+"step detected!"+bcolors.ENDC)
                countCombined+=1
            dMic=0
            dMpu=0
    
    if MODE == "OR":
        delta=abs((datetime.datetime.now()-lastStep).total_seconds())*1000
        #print(delta)
        if delta>TIME_TOLERANCE_DELAY:
            print(bcolors.FAIL+"step detected!"+bcolors.ENDC)
            countCombined+=1
        lastStep=datetime.datetime.now()
    print("micC:%i||mpuC=%i||combinedC=%i",countMic,countMpu,countCombined)


print("starting MPU...")
mpuDetector = MPUStepDetector(0x68)
mpuDetector.enableFilter(True)
mpuDetector.calibrate()
mpuDetector.setCallback(mpuCallback)
mpuDetector.startAsync()

print("starting MIC...")
micDetector = microphoneDetector(filter=True)
micDetector.setCallback(micCallback)
micDetector.calibrate()
print("5sec")
time.sleep(5)

micDetector.startAsync()
countMic=0
countMpu=0
countCombined=0
print("done")
time.sleep(6000)
mpuDetector.stopAsync()#signal stop event after 60s to exit thread in library
micDetector.stopAsync()#signal stop event after 60s to exit thread in library

#micDetector.stopAsync
