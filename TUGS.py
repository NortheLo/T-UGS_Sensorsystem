import pyaudio
import numpy as np
import pylab
import matplotlib.pyplot as plt
from scipy.io import wavfile
import time
import sys
from scipy import signal
from scipy.fft import fftshift

FORMAT = pyaudio.paInt16 # We use 16bit format per sample
CHANNELS = 1
RATE = 44100
CHUNK = 1024 
RECORD_SECONDS = 0.1

i=0
f,ax = plt.subplots(2)

x = np.arange(10000)
y = np.random.randn(10000)

li, = ax[0].plot(x, y)
ax[0].set_xlim(0,1000)
ax[0].set_ylim(-5000,5000)
ax[0].set_title("Raw Audio Signal")

li2, = ax[1].plot(x, y)
ax[1].set_xlim(0,5000)
ax[1].set_ylim(-100,100)
ax[1].set_title("Fast Fourier Transform")

plt.pause(0.01)
plt.tight_layout()

def selectMic():
    p = pyaudio.PyAudio()
    info = p.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')

    for i in range(0, numdevices):  
         if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
             print("Input Device id ", i, " - ", p.get_device_info_by_host_api_device_index(0, i).get('name'))

    print("Select microphone by id: ")
    return int(input())

def plot_data(in_data):
    audio_data = np.frombuffer(in_data, np.int16)

    dfft = 10.*np.log10(abs(np.fft.rfft(audio_data)))
    print("--- %s seconds ----" % (time.time()- time_t1)) # latency for recording
    
    dfft = 10.*np.log10(abs(np.fft.rfft(audio_data)))

    #for interests sake I tested a simple lp filter; maybe needed later on
    #sos = signal.butter(10, 300, 'low', fs=RATE, output='sos')
    #filtered = signal.sosfilt(sos, audio_data)
    #dfft_filtered = 10.*np.log10(abs(np.fft.rfft(filtered)))
    f, t, Sxx = signal.spectrogram(dfft, RATE/4)
    plt.pcolormesh(t, f, Sxx, shading='gouraud')
    print(type(f))
    
    #li.set_xdata(np.arange(len(audio_data)))
    #li.set_ydata(audio_data)
    #li2.set_xdata(np.arange(len(dfft))*10.)
    #li2.set_ydata(dfft)

    plt.pause(0.01)
    if keep_going:
        return True
    else:
        return False


audio = pyaudio.PyAudio()

# start Recording
stream = audio.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=selectMic(),
                    frames_per_buffer=CHUNK)

global keep_going
keep_going = True

stream.start_stream()
print ("\n+---------------------------------+")
print ("| Press Ctrl+C to Break Recording |")
print ("+---------------------------------+\n")


while keep_going:
    try:
        time_t1 = time.time()
        plot_data(stream.read(CHUNK))
    except KeyboardInterrupt:
        keep_going=False
    except:
        pass

stream.stop_stream()
stream.close()

audio.terminate()