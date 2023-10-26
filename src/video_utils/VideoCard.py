from collections import namedtuple
from typing import Self

import cv2
import threading as thr
import time

VideoReadSpecs = namedtuple("VideoReadSpecs", "device height width")
def_read_specs = VideoReadSpecs("/dev/video0", 720, 1280)


class VideoCard:
    """ Class to interact with a web-camera or other recording device. """
    def __init__(self, specs: VideoReadSpecs = def_read_specs):
        self.specs: VideoReadSpecs = specs
        self.vid_source: cv2.VideoCapture = cv2.VideoCapture(specs.device)
        self.viewing: bool = False
        self.grab_vid_thread = None
        self.latest_frame = None

    def start_viewing(self) -> None:
        if not self.viewing:
            if self.vid_source.isOpened():
                self.viewing = True
                self.grab_vid_thread = thr.Thread(name="video-watch-thread", daemon=True, target=self.frame_loader)
                self.grab_vid_thread.start()
                time.sleep(1)
            else:
                raise IOError("Video recording device is not available.")

    def frame_loader(self) -> None:
        while self.viewing:
            valid, frame = self.vid_source.read()
            if valid:
                self.latest_frame = frame

    def most_recent_frame(self):
        return self.latest_frame

    def stop_viewing(self):
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
