import threading
import time
import cv2
from .VideoCard import VideoCard

class VideoRecorderSpecs:
    def __init__(self,
                 device=0,
                 height: int = 720,
                 width: int = 1280,
                 fps: int = 30,
                 codec: str = "mp4v"
                 ):
        assert (len(codec) == 4)

        self.device = device
        self.height = height
        self.width = width
        self.fps = fps
        self.codec = codec


class VideoRecorder:
    def __init__(self, filename: str, card: VideoCard, specs: VideoRecorderSpecs = VideoRecorderSpecs()):
        self.specs = specs
        self.start = time.time
        self.written_frames = 0
        self.recording = False
        self.record_thread = None
        self.new_frame_avail = False
        self.frame = None
        self.frame_count = 0
        self.time_per_frame = 1 / specs.fps
        self.time_to_sleep = self.time_per_frame / 5
        self.card = card

        fourcc = cv2.VideoWriter.fourcc(*"mp4v")
        self.writer = cv2.VideoWriter(filename, fourcc, specs.fps, (specs.width, specs.height))

    def start_recording(self) -> None:
        if not self.recording:
            self.recording = True
            self.record_thread = threading.Thread(name="file-write", target=self.record)
            self.record_thread.start()

    def stop_recording(self) -> None:
        if self.recording:
            self.recording = False
            self.record_thread.join()

    def ready_for_new_frame(self) -> bool:
        return not self.new_frame_avail

    def next_frame(self, frame) -> bool:
        if self.ready_for_new_frame():
            self.frame = frame
            self.new_frame_avail = True
            return True

        return False

    def record(self):
        print("file-write thread started.")
        start_time = time.monotonic()
        while self.recording:
            record_at = self.record_next_frame_at(start_time)
            while record_at > time.monotonic():
                time.sleep(self.time_to_sleep)

            self.next_frame(self.card.most_recent_frame())

            if self.new_frame_avail:
                self.writer.write(self.frame)
                self.new_frame_avail = False
                self.frame_count += 1
            else:
                raise IOError("Unable to record at", self.specs.fps, "frames/second.")

        tm = time.monotonic() - start_time
        calc_fps = round(self.frame_count / tm, 3)

        print("Recorded", self.frame_count, "frames in", round(tm, 1), "seconds. (", calc_fps,")")
        self.writer.release()

    def record_next_frame_at(self, start) -> float:
        return start + self.frame_count / self.specs.fps

    def __enter__(self):
        self.start_recording()
        return self

    def __exit__(self, exc_type, exc_val, exc_traceback):
        self.stop_recording()
        return exc_type is None
