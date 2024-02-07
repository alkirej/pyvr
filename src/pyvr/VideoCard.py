"""
.. RAW:: html

    <h3 class="cls_header">VideoCard</h3>
    <div class="highlight cls_author">
        <pre>
        Author: Jeffery Alkire
        Date:   October 2023</pre>
    </div>
"""
from collections import namedtuple
from typing import Self

import cv2
import logging as log
import threading as thr
import time

from .configuration import load_config, VideoCfg

VideoReadSpecs = namedtuple("VideoReadSpecs", "device height width")
"""
**Named tuple** used to pass the necessary information about the
video device to the :py:class:`VideoCard<pyvr.VideoCard.VideoCard>`
object so that it can properly retrieve the video data.
"""

# default device specifications in case none are supplied.
def_read_specs = VideoReadSpecs("/dev/video0", 720, 1280)


class VideoCard:
    """
    A VideoCard object will start a thread that will monitor the video stream
    of a linux video device. It is designed to work with a with clause.

    .. SEEALSO:: Code snippet from :py:func:`record(...)<pyvr.record>`
    """
    def __init__(self) -> None:
        """
        :about: VideoCard object constructor.
        """
        _, video_config, _ = load_config()

        log.info("Setting up Video Card object")

        # MEMBERS DESCRIBING THE VIDEO INPUT DEVICE'S SETUP
        self.width: int = int(video_config[VideoCfg.WIDTH])
        self.height: int = int(video_config[VideoCfg.HEIGHT])
        self.device: str = video_config[VideoCfg.DEVICE]

        self.vid_source: cv2.VideoCapture = cv2.VideoCapture(self.device)
        self.vid_source.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.vid_source.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)

        # MEMBERS FOR INTER-THREAD COMMUNICATION
        self.viewing: bool = False
        self.grab_vid_thread = None
        self.latest_frame = None

        log.debug(f"    - device = {self.device}")
        log.debug(f"    - size   = {self.width} x {self.height}")

    def start_viewing(self) -> None:
        """
        :about: Start monitoring this device and storing the video images locally.  This will
                start a thread devoted to the process and then return.
        """
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
        """
        :about: Code executed by the video-capture-thread. Constantly examine the video from the
                card and store it locally.
        """
        log.info("video-capture-thread has started.")
        while self.viewing:
            valid, frame = self.vid_source.read()
            if valid:
                self.latest_frame = frame

    def most_recent_frame(self) -> bytes:
        """
        :about: Get the most recently captured frame from the video capture device.  Used to
                view or record the contents of the video stream.
        :return: binary image as captured by the video capture device.
        """
        return self.latest_frame

    def stop_viewing(self) -> None:
        """
        :about: Complete the monitoring of video capture device and terminate the
                corresponding thread..
        """
        log.info("Ending video capture.")
        if self.viewing:
            self.viewing = False
            self.grab_vid_thread.join()
            self.vid_source.release()

    def __enter__(self) -> Self:
        """ __enter__ and __exit__ allow objects of this class to use the with notation."""
        self.start_viewing()
        return self

    def __exit__(self, exc_type, exc_val, exc_traceback) -> bool:
        """ __enter__ and __exit__ allow objects of this class to use the with notation."""

        self.stop_viewing()
        return exc_type is None
