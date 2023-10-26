import logging as log
import pyaudio as pa
import threading as thr
import time
import wave

from .AudioInput import AudioInput


class AudioRecorder:
    def __init__(self, audio_input: AudioInput, filename: str = "recording-output.wav"):
        log.info("Setup audio recorder.")
        self.filename = filename
        self.audio_input = audio_input
        self.recording = False
        self.record_thread = None
        self.time_to_sleep = (self.audio_input.buffer_size/self.audio_input.sample_rate) / 5

        log.debug(f"    - Audio output sent to {self.filename}")

    def start_recording(self) -> None:
        log.info("Starting audio recording.")
        if not self.recording:
            self.recording = True
            self.record_thread = thr.Thread(name="audio-write-thread", target=self.record)
            self.record_thread.start()

    def stop_recording(self) -> None:
        log.info("Stopping audio recording.")
        if self.recording:
            self.recording = False
            self.record_thread.join()

    def record(self) -> None:
        log.info("audio-write-thread has started.")
        audio_interface = pa.PyAudio()  # Create an interface to PortAudio

        wav_file = wave.open(self.filename, 'wb')
        wav_file.setnchannels(self.audio_input.channels)
        wav_file.setsampwidth(audio_interface.get_sample_size(self.audio_input.sample_size))
        wav_file.setframerate(self.audio_input.sample_rate)

        while self.recording:
            if self.audio_input.new_audio_avail():
                current_audio_splice = self.audio_input.get_latest_audio()
                wav_file.writeframes(current_audio_splice)
            time.sleep(self.time_to_sleep)

        wav_file.close()

    def __enter__(self):
        self.start_recording()
        return self

    def __exit__(self, exc_type, exc_val, exc_traceback):
        self.stop_recording()
        return exc_type is None
