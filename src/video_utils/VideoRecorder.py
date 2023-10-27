import cv2
import logging as log
import time
import threading

from .VideoCard import VideoCard


class VideoRecorderSpecs:
    def __init__(self,
                 fps: int = 30,
                 codec: str = "mp4v"
                 ):
        assert (len(codec) == 4)
        self.fps = fps
        self.codec = cv2.VideoWriter.fourcc(*codec)


class VideoRecorder:
    def __init__(self, filename: str, card: VideoCard, specs: VideoRecorderSpecs = VideoRecorderSpecs()):
        assert filename.endswith(".mp4")

        log.info("Setup video recorder.")
        self.write_specs = specs
        self.read_specs = card.specs
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
        self.filename = filename

        log.debug(f"    - codec = {self.write_specs.codec}")
        log.debug(f"    - fps   = {self.write_specs.fps}")
        log.debug(f"    - size  = {self.read_specs.width} x {self.read_specs.height}")
        self.writer = cv2.VideoWriter(self.filename,
                                      self.write_specs.codec,
                                      self.write_specs.fps,
                                      (self.read_specs.width, self.read_specs.height)
                                      )

    def start_recording(self) -> None:
        log.info("Starting video recording.")
        if not self.recording:
            self.recording = True
            self.record_thread = threading.Thread(name="video-write-thread", target=self.record)
            self.record_thread.start()

    def stop_recording(self) -> None:
        log.info("Stopping video recording.")
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
        log.info("video-write-thread has started.")
        time.sleep(0.05)
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
                exc = IOError(f"Unable to record at {self.write_specs.fps} frames/second.")
                log.exception(exc)
                raise exc

        tm = time.monotonic() - start_time
        calc_fps = round(self.frame_count / tm, 3)

        log.info(f"Recorded {self.frame_count} frames in {round(tm, 1)} seconds. ({calc_fps} frames/second)")
        self.writer.release()

    def record_next_frame_at(self, start) -> float:
        return start + self.frame_count / self.write_specs.fps

    def __enter__(self):
        self.start_recording()
        return self

    def __exit__(self, exc_type, exc_val, exc_traceback):
        self.stop_recording()
        return exc_type is None
