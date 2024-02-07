import pyaudio
import sounddevice as sd

pa = pyaudio.PyAudio()
num = pa.get_device_count()

print(num)

for idx in range(num):
    info = pa.get_device_info_by_index(idx)
    if info.get("maxInputChannels") > 0:
        print(info)


print( sd.query_devices() )