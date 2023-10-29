"""
Routines that can be used to simplify or remove the interaction with the classes
"""
import cv2
import logging as log
import os
import time

from ffmpeg import FFmpeg

from .AudioRecorder import AudioInput, AudioRecorder
from .VideoRecorder import VideoCard, VideoRecorder

# GLOBAL VARIABLES FOR FILE EXTENSION TYPES
VIDEO_EXT = "mp4"
AUDIO_EXT = "wav"
RESULT_EXT = "mkv"

# SETUP LOGGER
log.basicConfig(filename="pvr.log",
                filemode="w",
                format="%(asctime)s %(filename)15.15s %(funcName)15.15s %(levelname)5.5s %(lineno)4.4s %(message)s",
                datefmt="%Y%m%d %H%M%S"
                )
log.getLogger().setLevel(log.DEBUG)


def record(filename_no_ext: str) -> None:
    """
    :about: This is the main entrypoint to the pyvr package.  It is likely the only function
            you will use. **Call it to record video and audio from you system.**
    :param filename_no_ext: The name of the resulting file (without the .mkv extension).  This
                            filename will be used to create 2 intermediate files (one .wav and
                            one .mp4) that are combined after the recording is complete into
                            the .mkv file.
    :Side Effect: Creation of a .mkv file recording the requested audio and video.

    .. note::
        This routine makes a great example of how to interact with the classes in this package.

            .. code-block:: python
                :caption: Sample Code using the AudioRecorder and VideoRecorder classes.

                    with VideoCard() as vc:
                        with VideoRecorder("video.mp4", vc):
                            with AudioInput(input_name="Pyle") as ai:
                                with AudioRecorder(ai, filename="audio.wav"):
                                    while True:
                                        f = vc.most_recent_frame()
                                        cv2.imshow("Preview", f)

                                        keypress = cv2.waitKey(1)
                                        if keypress & 0xFF == ord('q'):
                                            break
    """
    log.debug("*** *** *** Begin recording *** *** ***")

    # Each with line creates its own thread.
    with VideoCard() as vc:
        with VideoRecorder(f"{filename_no_ext}.{VIDEO_EXT}", vc):
            with AudioInput(input_name="Pyle") as ai:
                with AudioRecorder(ai, filename=f"{filename_no_ext}.{AUDIO_EXT}"):
                    while True:
                        # Preview the video being recorded.
                        f = vc.most_recent_frame()
                        resized = cv2.resize(f, (300, 200))
                        cv2.imshow("Preview", resized)

                        # Stop/end recording when escape key is pressed.
                        keypress = cv2.waitKey(1)
                        if keypress & 0xFF == 27: # ord('q'):
                            break

                        # Save some cpu for other people. Sleep and only show an occasional update.
                        time.sleep(1)

    cv2.destroyWindow("Preview")
    log.info("Combine and compress recording information.")
    combine_video_and_audio(f"{filename_no_ext}.{VIDEO_EXT}",
                            f"{filename_no_ext}.{AUDIO_EXT}",
                            f"{filename_no_ext}.{RESULT_EXT}"
                            )
    # delete video and audio files.
    os.remove(f"{filename_no_ext}.{VIDEO_EXT}")
    os.remove(f"{filename_no_ext}.{AUDIO_EXT}")

    log.info(f"Process complete. Results stored in {filename_no_ext}.{RESULT_EXT}")


def combine_video_and_audio(video_file: str, audio_file: str, resulting_file: str) -> None:
    """
    :about: Routine to combine a video file (with no audio) and an audio file into a single
            file using the H.265 codec creating a that is as small as possible without losing
            its quality.

    :param video_file: filename of the video file as a string (must end in .mp4)
    :param audio_file: filename of the audio file as a string (must end in .wav)
    :param resulting_file: store the resulting combined file in this filename (must end in .mkv)
    :Side Effect: Creation of a .mkv file recording the requested audio and video.
    """
    assert video_file.endswith(".mp4")
    assert audio_file.endswith(".wav")
    assert resulting_file.endswith(".mkv")
    assert os.path.isfile(video_file)
    assert os.path.isfile(audio_file)

    if os.path.isfile(resulting_file):
        os.remove(resulting_file)

    combine_and_compress = (FFmpeg()
                            .input(video_file)
                            .input(audio_file)
                            .output(resulting_file, {"codec:v": "libx265"})
                            )

    combine_and_compress.execute()
