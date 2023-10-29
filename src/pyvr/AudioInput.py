"""
.. RAW:: html

    <h3 class="cls_header">AudioInput</h3>
    <div class="highlight cls_author">
        <pre>
        Author: Jeffery Alkire
        Date:   October 2023</pre>
    </div>
"""
import logging as log
import pyaudio as pa
import sounddevice as sd
import threading as thr
import time

from typing import Self


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

    .. SEEALSO:: Code snippet from :py:func:`record(...)<pyvr.record>`
    """
    def __init__(self, input_name: str = "Pyle", split_dur: int = 1, sample_size: int = pa.paInt16) -> None:
        """
        :about: AudioInput constructor
        :param input_name:  name of the microphone or other audio input device. It is
                            a string that should match the name linux refers to the
                            device as.
        :param split_dur:   how many seconds of sound to record between disk writes.
        :param sample_size: how many bits to use for each sample.  This value should be
                            a pulse audio constant (paInt8, paInt16, paInt24, paInt32).
                            Passing 16 will probably not get you a 16-bit sample size.
        """
        log.info("Setting up audio input device configuration parameters.")
        self.listening: bool = False
        self.listen_thread = None
        self.latest_audio: bytes | None = None
        self.audio_devices = sd.default.device
        self.new_audio_sample = False
        self.latest_sample = None
        self.sample_size = sample_size

        audio_input_device = lookup_device(input_name)
        log.debug(f'Using audio device: {audio_input_device["name"]}')
        if audio_input_device is not None:
            self.audio_devices[0] = audio_input_device["index"]
            self.channels = audio_input_device["max_input_channels"]
            self.sample_rate = int(audio_input_device["default_samplerate"])
        else:
            self.channels = 2
            self.sample_rate = 48000

        self.buffer_size = int(split_dur * self.sample_rate)

        log.debug(f"    - audio device index = {self.audio_devices[0]}")
        log.debug(f"    - channels    = {self.channels}")
        log.debug(f"    - sample rate = {self.sample_rate}")
        log.debug(f"    - sample_size = {self.sample_size}")
        log.debug(f"    - buffer_size = {self.buffer_size}")

    def start_listening(self) -> None:
        """
        :about: Start monitoring this device and storing the andio data locally.  This will
                start a thread devoted to the process and then return.
        """
        log.info("Starting audio capture.")
        if not self.listening:
            self.listening = True
            self.listen_thread = thr.Thread(name="audio-capture-thread", daemon=True, target=self.listen)
            self.listen_thread.start()
            time.sleep(1)

    def listen(self) -> None:
        """
        :about: Code executed by the audio-capture-thread. Constantly examine the audio
                from the input device and save it to a file when it is available.
        """
        log.info("audio-capture-thread has started.")
        audio_interface = pa.PyAudio()  # Create an interface to PortAudio
        audio_stream = audio_interface.open(format=self.sample_size,
                                            channels=self.channels,
                                            rate=self.sample_rate,
                                            frames_per_buffer=self.buffer_size,
                                            input_device_index=self.audio_devices[0],
                                            input=True
                                            )

        while self.listening:
            new_audio = audio_stream.read(self.buffer_size)
            if self.new_audio_sample:
                exc = IOError("Cannot keep up with audio.")
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
