"""
... RAW:: html

    <h3 class="cls_header">AudioRecorder</h3>
    <div class="highlight cls_author">
        <pre>
        Author: Jeffery Alkire
        Date:   October 2023</pre>
    </div>
"""
import alsaaudio as aa
import logging as log
import pyaudio as pa
import sounddevice as sd
import threading as thr
import time

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
            self.thread_target = self.pyaudio_play
        else:
            self.thread_target = self.alsaaudio_play

    def start_playing(self) -> None:
        """
        :about: Start a new thread and use it to record (write to disk) the audio
                data retrieved from the AudioInput object.
        """
        log.info("Start playing audio.")
        # capture (record) the input from the audio input device and play on default speakers.
        if not self.playing:
            self.playing = True
            self.play_thread = thr.Thread(name="audio-write-thread", target=self.thread_target)
            self.play_thread.start()

    def stop_playing(self) -> None:
        """
        :about: Complete recording and stop the thread doing it.
        """
        log.info("Stop playing audio.")
        if self.playing:
            self.playing = False
            self.play_thread.join()

    def alsaaudio_play(self) -> None:
        log.info("alsaaudio-play-thread is starting.")
        audio_stream = aa.PCM(type=aa.PCM_PLAYBACK,
                              mode=aa.PCM_NORMAL,
                              rate=self.audio_input.sample_rate,
                              channels=self.audio_input.channels,
                              format=aa.PCM_FORMAT_S16_LE,
                              # periodsize=self.audio_input.buffer_size,
                              # periods=1
                              )
        log.info("alsaaudio-play-thread has started.")

        while self.playing:
            if self.audio_input.new_audio_sample:
                audio_buffer = self.audio_input.get_latest_audio()
                audio_stream.write(audio_buffer)
            time.sleep(self.audio_input.seconds_of_buffer / 250)

    def pyaudio_play(self) -> None:
        """
        :about: Routine run from the AudioRecorder's thread. This thread monitors
                the status of the AudioInput device and saves the audio data as
                it becomes available.
        """
        log.info("pyaudio-play-thread is starting.")
        audio_interface = pa.PyAudio()
        audio_stream = audio_interface.open(rate=48000,
                                            format=pa.paInt16,
                                            channels=2,
                                            output=True
                                            )

        log.info("pyaudio-play-thread has started.")

        while self.playing:
            if self.audio_input.new_audio_sample:
                audio_buffer = self.audio_input.get_latest_audio()
                sd.playrec(data=audio_buffer,channels=2,samplerate=48000)
                # sd.play(audio_buffer, 48000)
                sd.wait()
                # audio_stream.write(audio_buffer)
            # time.sleep(self.audio_input.seconds_of_buffer / 250)

        audio_stream.close()
        audio_interface.terminate()

    def __enter__(self):
        """ __enter__ and __exit__ allow objects of this class to use the with notation."""
        self.start_playing()
        return self

    def __exit__(self, exc_type, exc_val, exc_traceback):
        """ __enter__ and __exit__ allow objects of this class to use the with notation."""
        self.stop_playing()
        return exc_type is None
