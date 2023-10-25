from collections import namedtuple
import threading
import time
import cv2

VideoReadSpecs = namedtuple("VideoReadSpecs", "device height width")
def_read_specs = VideoReadSpecs("/dev/video0", 1280, 720)


class VideoCard:
    """ Class to interact with a web-camera or other recording device. """
    def __init__(self, specs: VideoReadSpecs = def_read_specs):
        self.specs: VideoReadSpecs = specs
        self.vid_source: cv2.VideoCapture = cv2.VideoCapture(specs.device)
        self.recording: bool = False
        self.grab_vid_thread = None
        self.latest_frame = None

    def start_viewing(self) -> None:
        if not self.recording:
            if self.vid_source.isOpened():
                self.recording = True
                self.grab_vid_thread = threading.Thread(name="capture", daemon=True, target=self.frame_loader)
                self.grab_vid_thread.start()
                time.sleep(1)
            else:
                raise IOError("Recording device is not available.")
    def frame_loader(self) -> None:
        while self.recording:
            valid, frame = self.vid_source.read()
            if valid:
                self.latest_frame = frame

    def most_recent_frame(self):
        return self.latest_frame

    def stop_viewing(self):
        if self.recording:
            self.recording = False
            self.grab_vid_thread.join()
            self.vid_source.release()

    def __enter__(self):
        self.start_viewing()
        return self

    def __exit__(self, exc_type, exc_val, exc_traceback):
        self.stop_viewing()
        return  exc_type is None
