import logging as log
import pyaudio as pa
import sounddevice as sd
import threading as thr
import time

from typing import Self

def lookup_device(name: str) -> dict | None:
    try:
        return sd.query_devices(device=name)

    except ValueError as ve:
        log.critical(ve)
        return None


class AudioInput:
    def __init__(self, input_name: str = "Pyle", split_dur: int = 1, sample_size: int = pa.paInt16) -> None:
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
        log.info("Starting audio capture.")
        if not self.listening:
            self.listening = True
            self.listen_thread = thr.Thread(name="audio-capture-thread", daemon=True, target=self.listen)
            self.listen_thread.start()
            time.sleep(1)

    def listen(self) -> None:
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
        return self.new_audio_sample

    def get_latest_audio(self) -> bytes:
        return_val = self.latest_audio
        self.new_audio_sample = False
        return return_val

    def stop_listening(self) -> None:
        log.info("Ending audio capture.")
        if self.listening:
            self.listening = False
            self.listen_thread.join()

    def __enter__(self) -> Self:
        self.start_listening()
        return self

    def __exit__(self, exc_type, exc_val, exc_traceback) -> bool:
        self.stop_listening()
        return exc_type is None
