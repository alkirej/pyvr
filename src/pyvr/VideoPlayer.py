"""
... RAW:: html

    <h3 class="cls_header">VideoRecorder</h3>
    <div class="highlight cls_author">
        <pre>
        Author: Jeffery Alkire
        Date:   February 2024</pre>
    </div>
"""
import cv2
import logging as log
import math
import time
import threading

from .configuration import load_config, AudioCfg, PreviewCfg
from .VideoCard import VideoCard
from .VideoHandler import VideoHandler


class VideoPlayer(VideoHandler):
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
        VideoHandler.__init__(self, card)

        # MEMBERS RELATED TO INTER-THREAD COMMUNICATION
        self.playing: bool = False
        self.play_thread = None

        # DELAY VIDEO TO SYNC WITH AUDIO
        audio_config, _, preview_config = load_config()
        self.video_buffer: [bytes] = []
        if bool(audio_config[AudioCfg.SYNC_PLAYER]):
            frame_count: int = math.ceil(audio_config[AudioCfg.SECS_OF_BUFFER]) * int(self.card.fps)
            self.buffer_frame_count = math.ceil(frame_count - int(1.6*self.card.fps))
        else:
            self.buffer_frame_count = 1

        self.height = int(preview_config[PreviewCfg.HEIGHT])
        self.width = int(preview_config[PreviewCfg.WIDTH])

    def start_playing(self) -> None:
        """
        :about: Start a new thread and use it to record (write to disk) the video
                frames retrieved from the VideoCard
        """
        log.info("Starting video.")
        if not self.playing:
            self.playing = True
            self.play_thread = threading.Thread(name="video-write-thread", target=self.play)
            self.play_thread.start()

    def stop_playing(self) -> None:
        """
        :about: Complete recording and stop the thread doing it.
        """
        log.info("Stopping video.")
        if self.playing:
            self.playing = False
            self.play_thread.join()

    def before_processing(self):
        log.info("video-thread is starting.")

        # fill buffer
        start_time = time.monotonic()
        while len(self.video_buffer) < self.buffer_frame_count:
            process_at = self.next_frame_at(start_time)
            while process_at > time.monotonic():
                time.sleep(self.time_to_sleep)

            self.next_frame(self.card.most_recent_frame())
            self.video_buffer.append(self.frame)

    def after_processing(self, monotonic_start_time):
        tm = time.monotonic() - monotonic_start_time
        calc_fps = round(self.frame_count / tm, 3)

        log.info(f"Displayed {self.frame_count} frames in {round(tm, 1)} seconds. ({calc_fps} frames/second)")
        cv2.destroyWindow("Display from Video Card")

    def process_single_frame(self):
        self.next_frame(self.card.most_recent_frame())
        self.video_buffer.append(self.frame)

        if len(self.video_buffer) > 0:
            frame = self.video_buffer.pop(0)
            resized = cv2.resize(frame, (self.width, self.height))
            cv2.imshow("Display from Video Card", resized)

            self.new_frame_avail = False
        else:
            exc = IOError(f"Unable to display at {self.fps} frames/second.")
            log.exception(exc)
            raise exc

        keypress = cv2.waitKey(1)
        if keypress & 0xFF == 27:
            self.processing = False

    def play(self) -> None:
        """
        :about: Routine run from the VideoRecorder's thread. This thread monitors
                the passage of time recording the proper number of frames each
                second.
        :note:  A log entry is written at the conclusion of recording indicating
                the speed of the recording.
        """
        log.info("video-thread is starting.")
        start_time = time.monotonic()
        # fill buffer
        while self.playing and len(self.video_buffer) < self.buffer_frame_count:
            if self.new_frame_avail:
                self.video_buffer.append(self.frame)

        while self.playing:
            play_at = self.next_frame_at(start_time)
            while play_at > time.monotonic():
                time.sleep(self.time_to_sleep)

            self.next_frame(self.card.most_recent_frame())

            if self.new_frame_avail:
                resized = cv2.resize(self.frame, (self.card.width, self.card.height))
                cv2.imshow("Display from Video Card", resized)

                self.new_frame_avail = False
                self.frame_count += 1
            else:
                exc = IOError(f"Unable to display at {self.fps} frames/second.")
                log.exception(exc)
                raise exc

            keypress = cv2.waitKey(1)
            if keypress & 0xFF == 27:
                self.playing = False

        tm = time.monotonic() - start_time
        calc_fps = round(self.frame_count / tm, 3)

        log.info(f"Displayed {self.frame_count} frames in {round(tm, 1)} seconds. ({calc_fps} frames/second)")
        cv2.destroyWindow("Display from Video Card")

    """
    def __enter__(self):
        " "" __enter__ and __exit__ allow objects of this class to use the with notation."" "
        self.start_playing()
        return self

    def __exit__(self, exc_type, exc_val, exc_traceback):
        " "" __enter__ and __exit__ allow objects of this class to use the with notation."" "
        self.stop_playing()
        return exc_type is None
    """