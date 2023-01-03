import pyaudio
import numpy as np
import pylab
import matplotlib.pyplot as plt
from scipy.io import wavfile
import time
import sys

FORMAT = pyaudio.paInt16 # We use 16bit format per sample
CHANNELS = 1
RATE = 44100
CHUNK = 1024 # 1024bytes of data red from a buffer
RECORD_SECONDS = 0.1

i=0
f,ax = plt.subplots(2)

# Prepare the Plotting Environment with random starting values
x = np.arange(10000)
y = np.random.randn(10000)

# Plot 0 is for raw audio data
li, = ax[0].plot(x, y)
ax[0].set_xlim(0,1000)
ax[0].set_ylim(-5000,5000)
ax[0].set_title("Raw Audio Signal")
# Plot 1 is for the FFT of the audio
li2, = ax[1].plot(x, y)
ax[1].set_xlim(0,5000)
ax[1].set_ylim(-100,100)
ax[1].set_title("Fast Fourier Transform")
# Show the plot, but without blocking updates
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
    # get and convert the data to float
    audio_data = np.frombuffer(in_data, np.int16)
    # Fast Fourier Transform, 10*log10(abs) is to scale it to dB
    # and make sure it's not imaginaryi
    dfft = 10.*np.log10(abs(np.fft.rfft(audio_data)))
    print("--- %s seconds ----" % (time.time()- time_t1)) # latency for recording
    
    li.set_xdata(np.arange(len(audio_data)))
    li.set_ydata(audio_data)
    li2.set_xdata(np.arange(len(dfft))*10.)
    li2.set_ydata(dfft)

    # Show the updated plot, but without blocking 
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
                    input=selectMic())#,
                    #frames_per_buffer=CHUNK)

global keep_going
keep_going = True

# Open the connection and start streaming the data
stream.start_stream()
print ("\n+---------------------------------+")
print ("| Press Ctrl+C to Break Recording |")
print ("+---------------------------------+\n")

# Loop so program doesn't end while the stream callback's
# itself for new data
while keep_going:
    try:
        time_t1 = time.time()
        plot_data(stream.read(CHUNK))
    except KeyboardInterrupt:
        keep_going=False
    except:
        pass

# Close up shop (currently not used because KeyboardInterrupt
# is the only way to close)
stream.stop_stream()
stream.close()

audio.terminate()
