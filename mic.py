from microphone import microphoneDetector
import time

def testCallback(timeDelta):
    print("Time deltas in Callback: ", timeDelta)

mic1 = microphoneDetector(filter=True)
mic1.startAsync()
mic1.setCallback(testCallback)
time.sleep(60)
mic1.stopAsync
