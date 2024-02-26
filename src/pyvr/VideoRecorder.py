"""
... RAW:: html

    <h3 class="cls_header">VideoRecorder</h3>
    <div class="highlight cls_author">
        <pre>
        Author: Jeffery Alkire
        Date:   October 2023</pre>
    </div>
"""
import cv2
import logging as log
import time
import threading

from .VideoCard import VideoCard
from .VideoHandler import VideoHandler


class VideoRecorder(VideoHandler):
    """
    A VideoRecorder object will start a thread that will monitor and record
    video frames supplied by
    :py:class:`VideoCard<pyvr.VideoCard.VideoCard>`

    ... SEEALSO:: Code snippet from :py:func:`record(...)<pyvr.record>`
    """
    def __init__(self, filename: str, card: VideoCard) -> None:
        """
        :about: VideoRecorder constructor
        :param filename: filename (currently must end with .mp4) to record video to.
        :param card:  object used to retrieve the video frames from the hardware.
        """
        VideoHandler.__init__(self, card)

        assert filename.endswith(".mp4")

        log.info("Setup video recorder.")

        # MEMBERS RELATED TO INTER-THREAD COMMUNICATION
        self.recording = False
        self.record_thread = None
        self.filename = filename

        self.writer = cv2.VideoWriter(self.filename,
                                      self.codec,
                                      self.card.fps,
                                      (self.card.width, self.card.height)
                                      )

    def before_processing(self):
        log.info("video-write-thread started.")

    def after_processing(self, monotonic_start_time):
        tm = time.monotonic() - monotonic_start_time
        calc_fps = round(self.frame_count / tm, 3)

        log.info(f"Recorded {self.frame_count} frames in {round(tm, 1)} seconds. ({calc_fps} frames/second)")
        self.writer.release()

    def process_single_frame(self):
        if self.new_frame_avail:
            self.writer.write(self.frame)
            self.new_frame_avail = False
        else:
            exc = IOError(f"Unable to record at {self.card.fps} frames/second.")
            log.exception(exc)
            raise exc
