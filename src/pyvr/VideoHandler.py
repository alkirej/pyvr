"""
... RAW:: html

    <h3 class="cls_header">VideoRecorder</h3>
    <div class="highlight cls_author">
        <pre>
        Author: Jeffery Alkire
        Date:   October 2023</pre>
    </div>
"""
from abc import abstractmethod

import cv2
import logging as log
import threading as thr
import time

from .configuration import load_config, VideoCfg
from .VideoCard import VideoCard


class VideoHandler:
    """
    A VideoRecorder object will start a thread that will monitor and record
    video frames supplied by
    :py:class:`VideoCard<pyvr.VideoCard.VideoCard>`

    ... SEEALSO:: Code snippet from :py:func:`record(...)<pyvr.record>`
    """
    def __init__(self, card: VideoCard) -> None:
        """
        :about: VideoRecorder constructor
        :param card:  object used to retrieve the video frames from the hardware.
        """
        log.info("Setup video player.")

        # MEMBERS RELATED TO INTER-THREAD COMMUNICATION
        self.new_frame_avail: bool = False
        self.frame: bytes | None = None
        self.card: VideoCard = card

        self.processing: bool = False
        self.process_thread: thr.Thread | None = None

        # LOAD CONFIG RELATED TO VIDEO OUTPUT FILE
        _, video_config, _ = load_config()
        self.fps = int(video_config[VideoCfg.FPS])
        self.codec = cv2.VideoWriter.fourcc(*video_config[VideoCfg.CODEC])
        self.width = int(video_config[VideoCfg.WIDTH])
        self.height = int(video_config[VideoCfg.HEIGHT])
        self.pre_start_delay = float(video_config[VideoCfg.PRE_START_DELAY])

        log.debug(f"Video startup delay: {self.pre_start_delay} seconds.")

        log.debug(f"    - codec = {self.codec}")
        log.debug(f"    - fps   = {self.fps}")
        log.debug(f"    - size  = {self.width} x {self.height}")

        # MEMBERS TO ENSURE VIDEO IS RECORDED AT THE PROPER PACE
        self.frame_count = 0
        self.time_per_frame = 1 / self.fps
        self.time_to_sleep = self.time_per_frame / 2

    def ready_for_next_frame(self) -> bool:
        """
        :about: determine if the recorder is able to store the next video frame.
        """
        return not self.new_frame_avail

    def next_frame(self, frame: bytes) -> bool:
        """
        :about: get a copy of the next frame to be saved to disk.
        :note:  The frame is only cached at this point.  It will be saved to disk only
                when it is time (based on the fps).  This insures the recording is taken
                at the correct speed.
        :returns: Return TRUE if the next frame was accepted and FALSE if it is too
                  soon.
        """
        if self.ready_for_next_frame():
            self.frame = frame
            self.new_frame_avail = True
            return True

        return False

    def next_frame_at(self, start: float) -> float:
        """
        :about: Determine the time the next frame should be recorded.
        :param start: the time the video recording began (in seconds)
        :returns: the results of a simple calculation of the time the
                  next frame should be saved. (in seconds)
        """
        return start + self.frame_count / self.fps

    def start_processing(self) -> None:
        """
        :about: Start a new thread and use it to record (write to disk) the video
                frames retrieved from the VideoCard
        """
        log.info("Start processing video.")
        if not self.processing:
            self.processing = True
            self.process_thread = thr.Thread(name="video-processing-thread", target=self.process)
            self.process_thread.start()

    def stop_processing(self) -> None:
        """
        :about: Complete recording and stop the thread doing it.
        """
        log.info("Stop processing video.")
        if self.processing:
            self.processing = False
            self.process_thread.join()

    def __enter__(self):
        """ __enter__ and __exit__ allow objects of this class to use the with notation."""
        self.start_processing()
        return self

    def __exit__(self, exc_type, exc_val, exc_traceback):
        """ __enter__ and __exit__ allow objects of this class to use the with notation."""
        self.stop_processing()
        return exc_type is None

    @abstractmethod
    def before_processing(self):
        pass

    @abstractmethod
    def after_processing(self, monotonic_start_time):
        pass

    @abstractmethod
    def process_single_frame(self):
        pass

    def process(self):
        self.before_processing()

        start_time = time.monotonic()
        while self.processing:
            process_at = self.next_frame_at(start_time)
            while process_at > time.monotonic():
                time.sleep(self.time_to_sleep)

            self.next_frame(self.card.most_recent_frame())

            self.frame_count += 1
            self.process_single_frame()

        self.after_processing(start_time)
