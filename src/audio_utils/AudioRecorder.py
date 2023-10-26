import threading as thr

from .AudioInput import AudioInput

class AudioRecorder:
    def __init__(self, filename: str, audio_input: AudioInput):
        self.filename = filename
        self.audio_input = audio_input
        self.recording = False
        self.record_thread = None

    def start_recording(self) -> None:
        if not self.recording:
            self.recording = True
            self.record_thread = thr.Thread(name="audio-write-thread", target=self.record)
            self.record_thread.start()

    def stop_recording(self) -> None:
        if self.recording:
            self.recording = False
            self.record_thread.join()

    def record(self) -> None:
        while self.recording:
            if self.audio_input.new_audio_sample():
                current_audio_splice = self.audio_input.get_latest_audio()

    def __enter__(self):
        self.start_recording()
        return self

    def __exit__(self, exc_type, exc_val, exc_traceback):
        self.stop_recording()
        return exc_type is None
