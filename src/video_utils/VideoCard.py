from collections import namedtuple
from typing import Self

import cv2
import logging as log
import threading as thr
import time

VideoReadSpecs = namedtuple("VideoReadSpecs", "device height width")
def_read_specs = VideoReadSpecs("/dev/video0", 720, 1280)


class VideoCard:
    """ Class to interact with a web-camera or other recording device. """
    def __init__(self, specs: VideoReadSpecs = def_read_specs):
        log.info("Setting up Video Card object")
        self.specs: VideoReadSpecs = specs
        self.vid_source: cv2.VideoCapture = cv2.VideoCapture(specs.device)
        self.viewing: bool = False
        self.grab_vid_thread = None
        self.latest_frame = None
        log.debug(f"    - device = {self.specs.device}")
        log.debug(f"    - size   = {self.specs.width} x {self.specs.height}")

    def start_viewing(self) -> None:
        log.info("Starting video capture.")
        if not self.viewing:
            if self.vid_source.isOpened():
                self.viewing = True
                self.grab_vid_thread = thr.Thread(name="video-capture-thread", daemon=True, target=self.frame_loader)
                self.grab_vid_thread.start()
                time.sleep(1)
            else:
                exc = IOError("Video recording device is not available.")
                log.exception(exc)
                raise exc

    def frame_loader(self) -> None:
        log.info("video-capture-thread has started.")
        while self.viewing:
            valid, frame = self.vid_source.read()
            if valid:
                self.latest_frame = frame

    def most_recent_frame(self):
        return self.latest_frame

    def stop_viewing(self):
        log.info("Ending video capture.")
        if self.viewing:
            self.viewing = False
            self.grab_vid_thread.join()
            self.vid_source.release()

    def __enter__(self) -> Self:
        self.start_viewing()
        return self

    def __exit__(self, exc_type, exc_val, exc_traceback) -> bool:
        self.stop_viewing()
        return exc_type is None
