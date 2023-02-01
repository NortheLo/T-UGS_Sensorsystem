from microphone import microphoneDetector
import time

def testCallback(timeDelta):
    print("Time deltas: ", timeDelta)

mic1 = microphoneDetector()
mic1.startAsync()
mic1.setCallback(testCallback)
time.sleep(60)
mic1.stopAsync