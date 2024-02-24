"""
... RAW:: html

    <h3 class="cls_header">AudioInput</h3>
    <div class="highlight cls_author">
        <pre>
        Author: Jeffery Alkire
        Date:   October 2023</pre>
    </div>
"""
import alsaaudio as aa
import enum
import logging as log
import pyaudio as pa
import sounddevice as sd
import threading as thr
import time

from typing import Self

from .configuration import load_config, AudioCfg


class SdAttr(str, enum.Enum):
    """Sound device Attribute constants"""
    INDEX = "index"
    NAME = "name"
    INPUT_CHANNELS = "max_input_channels"
    SAMPLE_RATE = "default_samplerate"


def lookup_device(name: str) -> dict | None:
    """
    :about: lookup an audio device in linux that includes the included text in its name.
    :param name: the name of the item to lookup.  Using "Pyle" will find a device
                 named "Pyle LiveGamer PLINK5"
    :returns: None if the search returned anything except 1 device.  The log will
                indicate the number of matches.  If the search is successful, then
                a dictionary is returned with the device's attributes.
    """
    try:
        return_val = sd.query_devices(device=name)
        log.debug(str(return_val))
        return return_val

    except ValueError as ve:
        log.critical(ve)
        return None


class AudioInput:
    """
    An AudioInput object will start a thread that will monitor the audio stream
    of a linux audio input device. It is designed to work with a with clause.

    ... SEEALSO:: Code snippet from :py:func:`record(...)<pyvr.record>`
    """
    def __init__(self) -> None:
        """
        :about: AudioInput constructor
        """
        log.info("Setting up audio input device configuration parameters.")

        # CONFIGURE/SETUP FOR THE AUDIO INPUT DEVICE (AKA: MICROPHONE)
        audio_config, _, _ = load_config()

        audio_library_name: str = audio_config[AudioCfg.AUDIO_LIBRARY]
        assert (audio_library_name.lower() == "pyaudio" or audio_library_name.lower() == "alsaaudio")
        self.audio_lib: str = audio_library_name.lower()
        if self.audio_lib == "pyaudio":
            self.thread_target = self.pyaudio_listen
        else:
            self.thread_target = self.alsaaudio_listen

        self.pre_start_delay = float(audio_config[AudioCfg.PRE_START_DELAY])
        self.seconds_of_buffer: float = float(audio_config[AudioCfg.SECS_OF_BUFFER])

        if audio_library_name.lower() == "pyaudio":
            log.debug(f"Audio startup delay: {self.pre_start_delay} seconds.")
            self.audio_input_device = lookup_device(audio_config[AudioCfg.DEVICE_NAME])
            if self.audio_input_device is None:
                log.critical(f'Unable to find device: {audio_config[AudioCfg.DEVICE_NAME]}')
                raise OSError(f'Audio input device {audio_config[AudioCfg.DEVICE_NAME]} not found.')

            log.debug(f'Using audio device: {self.audio_input_device[SdAttr.NAME]}')

            # LINUX'S INDEX TO THE MIC WE WILL USE
            self.audio_device_name: str = audio_config[AudioCfg.DEVICE_NAME]
            self.audio_device_idx: int = self.audio_input_device[SdAttr.INDEX]

            # SAMPLE SIZE IS THE # OF AUDIO SAMPLES TAKEN EACH SECOND.
            self.sample_rate: int = int(self.audio_input_device[SdAttr.SAMPLE_RATE])
            self.buffer_size: int = int(self.sample_rate * self.seconds_of_buffer)

            # NUMBER OF AUDIO CHANNELS TO RECORD (1=MONO, 2=STEREO, 6+=SURROUND SOUND)
            self.channels: int = self.audio_input_device[SdAttr.INPUT_CHANNELS]

        else:
            self.audio_device_name: str = audio_config[AudioCfg.DEVICE_NAME]
            self.sample_rate: int = int(audio_config[AudioCfg.SAMPLE_RATE])
            self.channels: int = int(audio_config[AudioCfg.CHANNEL_COUNT])
            self.buffer_size = int(self.channels * self.sample_rate * self.seconds_of_buffer)

        log.debug(f"    - channels    = {self.channels}")
        log.debug(f"    - sample rate = {self.sample_rate}")
        log.debug(f"    - buffer_size = {self.buffer_size}")

        # VARIABLES TO ALLOW THREAD INTERACTIONS
        self.listening: bool = False
        self.listen_thread: thr.Thread | None = None
        self.latest_audio: bytes | None = None
        self.new_audio_sample: bool = False

    def start_listening(self) -> None:
        """
        :about: Start monitoring this device and storing the audio data locally.  This will
                start a thread devoted to the process and then return.
        """
        log.info("Starting audio capture.")
        if not self.listening:
            self.listening = True
            self.listen_thread = thr.Thread(name="audio-capture-thread", daemon=True, target=self.thread_target)
            self.listen_thread.start()
            time.sleep(1)

    def alsaaudio_listen(self) -> None:
        problem_count: int = 0
        log.info("alsaaudio-capture-thread has started.")

        # mode can be aa.PCM_NONBLOCK
        audio_stream = aa.PCM(device=self.audio_device_name, type=aa.PCM_CAPTURE, mode=aa.PCM_NORMAL)
        audio_stream.setchannels(self.channels)
        audio_stream.setrate(self.sample_rate)
        audio_stream.setperiodsize(int(self.sample_rate * self.seconds_of_buffer))
        audio_stream.setformat(aa.PCM_FORMAT_S16_LE)

        while self.listening:
            size, new_audio = audio_stream.read()
            if self.new_audio_sample or size < 0:
                problem_count += 1
                log.warning(f"Trouble with audio recording. ({problem_count})")
                print(f"Trouble with audio recording. ({problem_count})")
                if problem_count >= 25:
                    exc = IOError(f"Cannot keep up with audio. ({problem_count})")
                    log.exception(exc)
                    raise exc

            self.latest_audio = new_audio
            self.new_audio_sample = True

        audio_stream.close()

    def pyaudio_listen(self) -> None:
        """
        :about: Code executed by the audio-capture-thread. Constantly examine the audio
                from the input device and save it to a file when it is available.
        """
        problem_count: int = 0
        log.info("pyaudio-capture-thread has started.")
        audio_interface = pa.PyAudio()  # Create an interface to PortAudio
        audio_stream = audio_interface.open(format=pa.paInt16,
                                            channels=self.channels,
                                            rate=self.sample_rate,
                                            frames_per_buffer=self.buffer_size,
                                            input_device_index=self.audio_device_idx,
                                            input=True
                                            )

        while self.listening:
            new_audio = audio_stream.read(self.buffer_size)
            if self.new_audio_sample:
                problem_count += 1
                log.warning(f"Trouble with audio recording. ({problem_count})")
                print(f"Trouble with audio recording. ({problem_count})")
                if problem_count >= 25:
                    exc = IOError(f"Cannot keep up with audio. ({problem_count})")
                    log.exception(exc)
                    raise exc

            self.latest_audio = new_audio
            self.new_audio_sample = True

        audio_stream.stop_stream()
        audio_stream.close()
        audio_interface.terminate()

    def new_audio_avail(self) -> bool:
        """
        :about:   determine if the recorder has unsaved data.
        :returns: TRUE if it is time to save some data, FALSE if not.
        """
        return self.new_audio_sample

    def get_latest_audio(self) -> bytes:
        """
        :about:   obtain the latest audio data the input device has provided.
        :returns: the binary audio data to be saved in the audio file.
        """
        return_val = self.latest_audio
        self.new_audio_sample = False
        return return_val

    def stop_listening(self) -> None:
        """
        :about: Complete the monitoring of audio input device and terminate the
                corresponding thread.
        """
        log.info("Ending audio capture.")
        if self.listening:
            self.listening = False
            self.listen_thread.join()

    def __enter__(self) -> Self:
        """ __enter__ and __exit__ allow objects of this class to use the with notation."""
        self.start_listening()
        return self

    def __exit__(self, exc_type, exc_val, exc_traceback) -> bool:
        """ __enter__ and __exit__ allow objects of this class to use the with notation."""
        self.stop_listening()
        return exc_type is None
