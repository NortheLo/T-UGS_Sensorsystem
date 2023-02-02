from microphone import microphoneDetector
import time
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

i=0
f,ax = plt.subplots(2)

x = np.arange(10000)
y = np.random.randn(10000)

li, = ax[0].plot(x, y)
ax[0].set_xlim(0,1000)
ax[0].set_ylim(-5000,5000)
ax[0].set_title("Raw Audio Signal", loc='center', wrap=True)

li2, = ax[1].plot(x, y)
ax[1].set_xlim(0, 2e3)
ax[1].set_ylim(0,100)
ax[1].set_title("Fast Fourier Transform", loc='center', wrap=True)

plt.pause(0.001)
plt.tight_layout()

def update():
    global li
    global li2
    li.set_xdata(np.arange(len(mic1.audio_data))*10.)
    li.set_ydata(mic1.audio_data)


def testCallback(timeDelta):
    print("Time deltas in Callback: ", timeDelta)

mic1 = microphoneDetector()
mic1.startAsync()
#mic1.setCallback(testCallback)

animation = FuncAnimation(f, update, interval=1, repeat=False)
plt.show()
