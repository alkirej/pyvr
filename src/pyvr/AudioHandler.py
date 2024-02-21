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

from .AudioInput import AudioInput


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

        #  WAKE UP 5 TIMES BETWEEN EACH DISK WRITE
        self.time_to_sleep = (self.audio_input.buffer_size/self.audio_input.sample_rate) / 5

    @abstractmethod
    def __enter__(self):
        """ __enter__ and __exit__ allow objects of this class to use the with notation."""
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_traceback):
        """ __enter__ and __exit__ allow objects of this class to use the with notation."""
        pass
