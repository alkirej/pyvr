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
import time
import wave

from .AudioHandler import AudioHandler
from .AudioInput import AudioInput

ALSA_RECORD_RATE = 48000


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
        self.wav_file = None

        log.info(f"    - Audio output sent to {self.filename}")

    def before_processing(self) -> None:
        log.info(f"audio-write-thread is starting. delay={self.audio_input.pre_start_delay}")
        time.sleep(self.audio_input.pre_start_delay)
        log.info("audio-write-thread has started.")

        self.wav_file = wave.open(self.filename, 'wb')
        self.wav_file.setnchannels(self.audio_input.channels)
        self.wav_file.setsampwidth(2)
        self.wav_file.setframerate(self.audio_input.sample_rate)

        silence = b'\x00' * int(self.audio_input.sample_rate *
                                self.audio_input.channels *
                                self.audio_input.pre_start_delay
                                )
        print(f"Bytes of silence: {len(silence)}")
        self.wav_file.setnframes(self.audio_input.buffer_size)
        self.wav_file.writeframesraw(silence)

    def after_processing(self) -> None:
        self.wav_file.close()

    def check_buffer(self) -> None:
        if self.audio_input.new_audio_sample:
            audio_buffer = self.audio_input.get_latest_audio()
            self.wav_file.writeframesraw(audio_buffer)
