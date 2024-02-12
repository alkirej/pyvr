"""
.. RAW:: html

    <h3 class="cls_header">VideoRecorder</h3>
    <div class="highlight cls_author">
        <pre>
        Author: Jeffery Alkire
        Date:   February 2024</pre>
    </div>
"""
import cv2
import time
import threading

from .configuration import load_config, VideoCfg
from .VideoCard import VideoCard


class VideoPlayer:
    """
    A VideoRecorder object will start a thread that will monitor and record
    video frames supplied by
    :py:class:`VideoCard<pyvr.VideoCard.VideoCard>`

    .. SEEALSO:: Code snippet from :py:func:`record(...)<pyvr.record>`
    """
    def __init__(self, card: VideoCard) -> None:
        """
        :about: VideoRecorder constructor
        :param filename: filename (currently must end with .mp4) to record video to.
        :param card:  object used to retrieve the video frames from the hardware.
        """

        # MEMBERS RELATED TO INTER-THREAD COMMUNICATION
        self.play_video_thread = None
        self.new_frame_avail = False
        self.frame = None
        self.card = card

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
        self.writer = cv2.VideoWriter(self.filename,
                                      self.codec,
                                      self.fps,
                                      (self.width, self.height)
                                      )

        # MEMBERS TO ENSURE VIDEO IS RECORDED AT THE PROPER PACE
        self.start = time.time
        self.frame_count = 0
        self.time_per_frame = 1 / self.fps
        self.time_to_sleep = self.time_per_frame / 2

    def start_recording(self) -> None:
        """
        :about: Start a new thread and use it to record (write to disk) the video
                frames retreived from the VideoCard
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

    def ready_for_new_frame(self) -> bool:
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
        if self.ready_for_new_frame():
            self.frame = frame
            self.new_frame_avail = True
            return True

        return False

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
            record_at = self.record_next_frame_at(start_time)
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

    def record_next_frame_at(self, start: float) -> float:
        """
        :about: Determine the time the next frame should be recorded.
        :param start: the time the video recording began (in seconds)
        :returns: the results of a simple calculation of the time the
                  next frame should be saved. (in seconds)
        """
        return start + self.frame_count / self.fps

    def __enter__(self):
        """ __enter__ and __exit__ allow objects of this class to use the with notation."""
        self.start_recording()
        return self

    def __exit__(self, exc_type, exc_val, exc_traceback):
        """ __enter__ and __exit__ allow objects of this class to use the with notation."""
        self.stop_recording()
        return exc_type is None
