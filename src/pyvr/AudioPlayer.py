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
import alsaaudio as aa
import logging as log
import pyaudio as pa

from .AudioHandler import AudioHandler
from .AudioInput import AudioInput
from .configuration import load_config, AudioCfg


class AudioPlayer(AudioHandler):
    """
    An AudioRecorder object will start a thread that will monitor and record
    chunks of audio frames supplied by a
    :py:class:`AudioInput<pyvr.AudioInput.AudioInput>`
    object.

    ... SEEALSO:: Code snippet from :py:func:`record(...)<pyvr.record>`
    """
    def __init__(self, audio_input: AudioInput):
        AudioHandler.__init__(self, audio_input)

        log.info("Setup audio player.")

        self.playing: bool = False
        self.play_thread = None

        audio_config, _, _ = load_config()

        audio_library_name: str = audio_config[AudioCfg.AUDIO_LIBRARY]
        assert (audio_library_name.lower() == "pyaudio" or audio_library_name.lower() == "alsaaudio")
        self.audio_lib: str = audio_library_name.lower()
        if self.audio_lib == "pyaudio":
            self.pyaudio = True
            self.alsaaudio = False
        else:
            self.pyaudio = False
            self.alsaaudio = True

        self.audio_stream = None
        self.audio_interface = None

    def alsaaudio_start(self) -> None:
        log.info("alsaaudio-play-thread is starting.")
        self.audio_stream = aa.PCM(device="default",
                                   type=aa.PCM_PLAYBACK,
                                   mode=aa.PCM_NORMAL,
                                   rate=44100,  # Any other value causes error.
                                   channels=self.audio_input.channels,
                                   format=aa.PCM_FORMAT_S16_LE,
                                   periodsize=self.audio_input.buffer_size,
                                   periods=1
                                   )
        log.info("alsaaudio-play-thread has started.")

    def alsaaudio_stop(self) -> None:
        self.audio_stream.close()

    def pyaudio_start(self) -> None:
        """
        :about: Routine run from the AudioRecorder's thread. This thread monitors
                the status of the AudioInput device and saves the audio data as
                it becomes available.
        """
        log.info("pyaudio-play-thread is starting.")
        self.audio_interface = pa.PyAudio()
        self.audio_stream = self.audio_interface.open(rate=self.audio_input.sample_rate,
                                                      format=pa.paInt16,
                                                      channels=2,
                                                      output=True
                                                      )
        log.info("pyaudio-play-thread has started.")

    def pyaudio_stop(self) -> None:
        self.audio_stream.close()
        self.audio_interface.terminate()

    @abstractmethod
    def before_processing(self):
        self.pyaudio_start()

    @abstractmethod
    def after_processing(self):
        self.pyaudio_stop()

    def check_buffer(self) -> None:
        if self.audio_input.new_audio_sample:
            audio_buffer = self.audio_input.get_latest_audio()
            self.audio_stream.write(audio_buffer)
