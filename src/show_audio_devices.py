import pyaudio as pa

from pyvr.configuration import load_audio_config, AudioCfg

# audio_config = load_audio_config()
# audio_library_name: str = audio_config[AudioCfg.AUDIO_LIBRARY]
# audio_lib: str = audio_library_name.lower()
# if audio_lib == "pyaudio":



p = pa.PyAudio()
for i in range(p.get_device_count()):
    device: dict = p.get_device_info_by_index(i)
    if device['maxInputChannels'] > 0:
        print(f'{device["name"]} ({device["maxInputChannels"]})')

