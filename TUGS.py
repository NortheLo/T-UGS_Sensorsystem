import time
import sys
import os
import pyaudio
import numpy as np
import pylab
import matplotlib.pyplot as plt
from scipy import signal
from scipy.fft import fftshift
import scipy.fftpack
from scipy.ndimage import shift

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 2048
FIFO_WINDOW = 128

FIFO = np.zeros((CHUNK, CHUNK*FIFO_WINDOW), dtype=np.int16)

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

    # Butterworth bandpass  filter for filtering the high noised hissing from the cheap USB mic and the low end garbage
    # Butterworth bandstop to focus on the interesting frequencies for the step detection (~40Hz and ~600-700HZ)
    sos_bp = signal.butter(10, [10, 900], 'bp', fs=RATE, output='sos')
    sos_bs = signal.butter(10, [50, 600], 'bs', fs=RATE, output='sos')
    audio_data_bp = signal.sosfilt(sos_bp, audio_data)
    audio_data_bs = signal.sosfilt(sos_bs, audio_data_bp)
    
    # Blackman window function as it has the wide main lobe and surpresses more the side lobes 
    audio_data_window = audio_data_bs * np.blackman(len(audio_data_bs))

    # FFT in dB drom the windowed audio signal, using all cores of the host
    dfft = 20* np.log10(np.abs(scipy.fftpack.rfft(audio_data_window)))
    
    # Adding values to the FIFO 
    FIFO[:, 0] = dfft
    # Shifting the FFTs along the second dimension
    FIFO = shift(FIFO, (0, 1), cval=np.NaN)
    
    # Spectrogram from the windowed audio
    #freq, times, spectrogram = signal.spectrogram(audio_data, RATE, window='blackman')

    # Subplot with spectrogram
    #spec_mesh = ax[2].pcolormesh(times, freq, 10.*np.log10(spectrogram), shading='gouraud')

    # Bar for seeing the db color relation
    #bar = plt.colorbar(spec_mesh, ax=ax[2])
    #bar.set_label('Amplitude (dB)')

    x_axis_fft = np.arange(len(audio_data))
    li.set_xdata(x_axis_fft)
    li.set_ydata(audio_data)
    li2.set_xdata(np.arange(len(dfft))*10.)
    li2.set_ydata(dfft)
    
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