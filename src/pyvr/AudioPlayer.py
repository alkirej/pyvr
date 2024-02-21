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
import simpleaudio as sa
import threading as thr
import time

from .AudioHandler import AudioHandler
from .AudioInput import AudioInput


class AudioPlayer(AudioHandler):
    def __init__(self, audio_input: AudioInput):
        AudioHandler.__init__(self, audio_input)

        log.info("Setup audio recorder.")

        self.playing: bool = False
        self.play_thread = None

    """
    An AudioRecorder object will start a thread that will monitor and record
    chunks of audio frames supplied by a
    :py:class:`AudioInput<pyvr.AudioInput.AudioInput>`
    object.

    ... SEEALSO:: Code snippet from :py:func:`record(...)<pyvr.record>`
    """
    def start_playing(self) -> None:
        """
        :about: Start a new thread and use it to record (write to disk) the audio
                data retrieved from the AudioInput object.
        """
        log.info("Starting audio recording.")
        # capture (record) the input from the audio input device and play on default speakers.
        if not self.playing:
            self.playing = True
            self.play_thread = thr.Thread(name="audio-write-thread", target=self.play)
            self.play_thread.start()

    def stop_playing(self) -> None:
        """
        :about: Complete recording and stop the thread doing it.
        """
        log.info("Stopping audio recording.")
        if self.playing:
            self.playing = False
            self.play_thread.join()

    def play(self) -> None:
        """
        :about: Routine run from the AudioRecorder's thread. This thread monitors
                the status of the AudioInput device and saves the audio data as
                it becomes available.
        """
        log.info("audio-play-thread is starting.")
        time.sleep(self.audio_input.pre_start_delay)
        log.info("audio-play-thread has started.")

        while self.playing:
            if self.audio_input.new_audio_avail():
                # Preview the audio:
                audio_buffer = self.audio_input.get_latest_audio()
                complete_check = sa.play_buffer(audio_buffer,
                                                self.audio_input.channels,
                                                2,
                                                self.audio_input.sample_rate
                                                )
                complete_check.wait_done()

        # wav_file.close()

    def __enter__(self):
        """ __enter__ and __exit__ allow objects of this class to use the with notation."""
        self.start_playing()
        return self

    def __exit__(self, exc_type, exc_val, exc_traceback):
        """ __enter__ and __exit__ allow objects of this class to use the with notation."""
        self.stop_playing()
        return exc_type is None
