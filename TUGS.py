import time
import sys
import pyaudio
import numpy as np
import pylab
import matplotlib.pyplot as plt
from scipy import signal
from scipy.fft import fftshift
import scipy.fftpack
import librosa

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 2048

i=0
f,ax = plt.subplots(3)

x = np.arange(10000)
y = np.random.randn(10000)

#plt.grid()

li, = ax[0].plot(x, y)
ax[0].set_xlim(0,1000)
ax[0].set_ylim(-5000,5000)
ax[0].set_title("Raw Audio Signal", loc='center', wrap=True)

li2, = ax[1].plot(x, y)
ax[1].set_xlim(0,5000)
ax[1].set_ylim(0,100)
ax[1].set_title("Fast Fourier Transform", loc='center', wrap=True)

ax[2].set_title("Spectrogram", loc='center', wrap=True)
ax[2].set_xlabel('Time (s)')
ax[2].set_ylabel('Frequencies (Hz)')


plt.pause(0.001)
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
    audio_data = np.frombuffer(in_data, dtype=np.int16)

    # !!! Measure steps !!!

    # For interests sake I tested a simple lp filter; maybe needed later on
    # sos = signal.butter(10, 300, 'low', fs=RATE, output='sos')
    # audio_data = signal.sosfilt(sos, audio_data)
    
    # Blackman window function as it has the wide main lobe and surpresses more the side lobes 
    audio_data_window = audio_data * np.blackman(len(audio_data))
    dfft = 20* np.log10(np.abs(scipy.fftpack.rfft(audio_data_window)))
    
    # To be tested: mode and window
    freq, times, spectrogram = signal.spectrogram(audio_data, RATE, window='blackman')
    spec_mesh = ax[2].pcolormesh(times, freq, 10.*np.log10(spectrogram), shading='gouraud')
        
    # Bar for seeing the db color relation
    #bar = plt.colorbar(spec_mesh, ax=ax[2])
    #bar.set_label('Amplitude (dB)')

    li.set_xdata(np.arange(len(audio_data)))
    li.set_ydata(audio_data)
    li2.set_xdata(np.arange(len(dfft))*10.)
    li2.set_ydata(dfft)
    
    # Experimental
    # Try to detect steps by extracting the bps and if it fits into the step range we will take it as a step
    tempo, beats = librosa.beat.beat_track(y=audio_data, sr=RATE)   
    print("Your steps dance with a BPM of " + tempo)
    
    print("--- %s seconds ----" % (time.time() - time_t1))
    
    plt.pause(0.001)
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
