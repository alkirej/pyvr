"""
.. py:module:: VideoCard

A VideoCard object will start a thread that will monitor the video stream
of a linux video device. It is designed to work with a with clause as shown
below.

Example Code:
=============

.. code-block:: python

    import cv2
    from video_utils.VideoCard import VideoCard

    with VideoCard() as vc:
        while True:
            f = vc.most_recent_frame()
            cv2.imshow("Preview", f)

            keypress = cv2.waitKey(1)
            if keypress & 0xFF == ord('q'):
                break
            time.sleep(1)
"""
from collections import namedtuple
from typing import Self

import cv2
import logging as log
import threading as thr
import time

VideoReadSpecs = namedtuple("VideoReadSpecs", "device height width")
def_read_specs = VideoReadSpecs("/dev/video0", 720, 1280)


class VideoCard:
    """Class to interact with a web-camera or other recording device."""

    def __init__(self, specs: VideoReadSpecs = def_read_specs) -> None:
        """VideoCard object constructor.

        Params:
            specs (VideoReadSpecs): device and screen size of the video capture device.

        Returns:
            None
        """

        log.info("Setting up Video Card object")
        self.specs: VideoReadSpecs = specs
        self.vid_source: cv2.VideoCapture = cv2.VideoCapture(specs.device)
        self.viewing: bool = False
        self.grab_vid_thread = None
        self.latest_frame = None
        log.debug(f"    - device = {self.specs.device}")
        log.debug(f"    - size   = {self.specs.width} x {self.specs.height}")

    def start_viewing(self) -> None:
        """Start monitoring this device and storing the video images locally.  This will
        start a thread devoted to the process and then return.

        Returns:
            None
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
        """Code executed by the video-capture-thread. Constantly examine the video from the
        card and store it locally.

        Returns:
            None
        """

        log.info("video-capture-thread has started.")
        while self.viewing:
            valid, frame = self.vid_source.read()
            if valid:
                self.latest_frame = frame

    def most_recent_frame(self) -> bytes:
        """Get the most recently captured frame from the video capture device.  Used to
        view or record the contents of the video stream.

        Returns:
            bytes: binary image as captured by the video capture device.
        """

        return self.latest_frame

    def stop_viewing(self) -> None:
        """Complete the monitoring of video capture device.

        Returns:
            None
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
