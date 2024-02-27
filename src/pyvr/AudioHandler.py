"""
... RAW:: html

    <h3 class="cls_header">AudioRecorder</h3>
    <div class="highlight cls_author">
        <pre>
        Author: Jeffery Alkire
        Date:   October 2023</pre>
    </div>
"""
from abc import abstractmethod

import logging as log
import threading as thr
import time

from .AudioInput import AudioInput
from .configuration import load_config, AudioCfg


class AudioHandler:
    """
    An AudioRecorder object will start a thread that will monitor and record
    chunks of audio frames supplied by a
    :py:class:`AudioInput<pyvr.AudioInput.AudioInput>`
    object.

    ... SEEALSO:: Code snippet from :py:func:`record(...)<pyvr.record>`
    """
    def __init__(self, audio_input: AudioInput):
        """
        :about: AudioRecorder constructor
        :param audio_input:
        """
        # MEMBERS USED TO INTERACT WITH THE AUDIO HARDWARE
        self.audio_input = audio_input

        self.time_to_sleep = (self.audio_input.buffer_size/self.audio_input.sample_rate) / 250
        self.processing = False
        self.process_thread = None

    def start_processing(self) -> None:
        """
        :about: Start a new thread and use it to record (write to disk) the audio
                data retrieved from the AudioInput object.
        """
        log.info("Start processing audio.")
        # capture (record) the input from the audio input device and play on default speakers.
        if not self.processing:
            self.processing = True
            self.process_thread = thr.Thread(name="audio-process-thread", target=self.process)
            self.process_thread.start()

    @abstractmethod
    def before_processing(self):
        pass

    @abstractmethod
    def after_processing(self):
        pass

    @abstractmethod
    def check_buffer(self):
        pass

    def process(self):
        self.before_processing()

        while self.processing:
            self.check_buffer()

        self.after_processing()

    def stop_processing(self) -> None:
        """
        :about: Complete recording and stop the thread doing it.
        """
        log.info("Stop processing audio.")
        self.processing = False
        self.process_thread.join()

    def __enter__(self):
        """ __enter__ and __exit__ allow objects of this class to use the with notation."""
        self.start_processing()
        return self

    def __exit__(self, exc_type, exc_val, exc_traceback):
        """ __enter__ and __exit__ allow objects of this class to use the with notation."""
        self.stop_processing()
        return exc_type is None
