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
                                      self.fps,
                                      (self.width, self.height)
                                      )

    def start_recording(self) -> None:
        """
        :about: Start a new thread and use it to record (write to disk) the video
                frames retrieved from the VideoCard
        """
        log.info("Starting video recording.")
        if not self.recording:
            self.recording = True
            self.record_thread = threading.Thread(name="video-write-thread", target=self.record)
            self.record_thread.start()

    def stop_recording(self) -> None:
        """
        :about: Complete recording and stop the thread doing it.
        """
        log.info("Stopping video recording.")
        if self.recording:
            self.recording = False
            self.record_thread.join()

    def before_processing(self):
        log.info("video-write-thread is starting.")
        time.sleep(self.pre_start_delay)
        log.info("video-write-thread finished started.")

    def after_processing(self, monotonic_start_time):
        tm = time.monotonic() - monotonic_start_time
        calc_fps = round(self.frame_count / tm, 3)

        log.info(f"Recorded {self.frame_count} frames in {round(tm, 1)} seconds. ({calc_fps} frames/second)")
        self.writer.release()

    def process_single_frame(self):
        if self.new_frame_avail:
            self.writer.write(self.frame)
            self.new_frame_avail = False
            self.frame_count += 1
        else:
            exc = IOError(f"Unable to record at {self.fps} frames/second.")
            log.exception(exc)
            raise exc

    def record(self) -> None:
        """
        :about: Routine run from the VideoRecorder's thread. This thread monitors
                the passage of time recording the proper number of frames each
                second.
        :note:  A log entry is written at the conclusion of recording indicating
                the speed of the recording.
        """
        log.info("video-write-thread is starting.")
        time.sleep(self.pre_start_delay)
        log.info("video-write-thread finished started.")
        start_time = time.monotonic()
        while self.recording:
            record_at = self.next_frame_at(start_time)
            while record_at > time.monotonic():
                time.sleep(self.time_to_sleep)

            self.next_frame(self.card.most_recent_frame())

            if self.new_frame_avail:
                self.writer.write(self.frame)
                self.new_frame_avail = False
                self.frame_count += 1
            else:
                exc = IOError(f"Unable to record at {self.fps} frames/second.")
                log.exception(exc)
                raise exc

        tm = time.monotonic() - start_time
        calc_fps = round(self.frame_count / tm, 3)

        log.info(f"Recorded {self.frame_count} frames in {round(tm, 1)} seconds. ({calc_fps} frames/second)")
        self.writer.release()

    """
    def __enter__(self):
        " "" __enter__ and __exit__ allow objects of this class to use the with notation."" "
        self.start_recording()
        return self

    def __exit__(self, exc_type, exc_val, exc_traceback):
        " "" __enter__ and __exit__ allow objects of this class to use the with notation."" "
        self.stop_recording()
        return exc_type is None
    """
