"""
... RAW:: html

    <h3 class="cls_header">AudioRecorder</h3>
    <div class="highlight cls_author">
        <pre>
        Author: Jeffery Alkire
        Date:   October 2023</pre>
    </div>
"""
import logging as log
import threading as thr
import time
import wave

from .AudioHandler import AudioHandler
from .AudioInput import AudioInput


class AudioRecorder(AudioHandler):
    """
    An AudioRecorder object will start a thread that will monitor and record
    chunks of audio frames supplied by a
    :py:class:`AudioInput<pyvr.AudioInput.AudioInput>`
    object.

    ... SEEALSO:: Code snippet from :py:func:`record(...)<pyvr.record>`
    """
    def __init__(self, audio_input: AudioInput, filename: str):
        AudioHandler.__init__(self, audio_input)
        assert filename.endswith(".wav")

        log.info("Setup audio recorder.")

        # MEMBERS USED TO COMMUNICATE TO THE RECORD THREAD
        self.recording: bool = False
        self.record_thread = None

        # MEMBERS USED TO INTERACT WITH THE DISK
        self.filename = filename

        log.debug(f"    - Audio output sent to {self.filename}")

    def start_recording(self) -> None:
        """
        :about: Start a new thread and use it to record (write to disk) the audio
                data retrieved from the AudioInput object.
        """
        log.info("Starting audio recording.")
        if not self.recording:
            self.recording = True
            self.record_thread = thr.Thread(name="audio-write-thread", target=self.record)
            self.record_thread.start()

    def stop_recording(self) -> None:
        """
        :about: Complete recording and stop the thread doing it.
        """
        log.info("Stopping audio recording.")
        if self.recording:
            self.recording = False
            self.record_thread.join()

    def record(self) -> None:
        """
        :about: Routine run from the AudioRecorder's thread. This thread monitors
                the status of the AudioInput device and saves the audio data as
                it becomes available.
        """
        log.info("audio-write-thread is starting.")
        time.sleep(self.audio_input.pre_start_delay)
        log.info("audio-write-thread has started.")

        wav_file = wave.open(self.filename, 'wb')
        wav_file.setnchannels(self.audio_input.channels)
        wav_file.setsampwidth(2)
        wav_file.setframerate(self.audio_input.sample_rate)

        while self.recording:
            if self.audio_input.new_audio_sample:
                current_audio_splice = self.audio_input.get_latest_audio()
                wav_file.writeframes(current_audio_splice)
            time.sleep(self.time_to_sleep)

        wav_file.close()

    def __enter__(self):
        """ __enter__ and __exit__ allow objects of this class to use the with notation."""
        self.start_recording()
        return self

    def __exit__(self, exc_type, exc_val, exc_traceback):
        """ __enter__ and __exit__ allow objects of this class to use the with notation."""
        self.stop_recording()
        return exc_type is None
