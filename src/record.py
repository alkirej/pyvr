import cv2
import logging as log
import time
import os

from pyvr.AudioRecorder import AudioInput, AudioRecorder
from pyvr.VideoRecorder import VideoCard, VideoRecorder

import pyvr

FILE_NAME = "recording"
VIDEO_EXT = "mp4"
AUDIO_EXT = "wav"
RESULT_EXT = "mkv"


def main() -> None:
    log.basicConfig(filename="pvr.log",
                    filemode="w",
                    format="%(asctime)s %(filename)15.15s %(funcName)15.15s %(levelname)5.5s %(lineno)4.4s %(message)s",
                    datefmt="%Y%m%d %H%M%S"
                    )
    log.getLogger().setLevel(log.DEBUG)

    log.debug("*** *** *** Begin record program *** *** ***")
    with VideoCard() as vc:
        with VideoRecorder(f"{FILE_NAME}.{VIDEO_EXT}", vc):
            with AudioInput(input_name="Pyle") as ai:
                with AudioRecorder(ai, filename=f"{FILE_NAME}.{AUDIO_EXT}"):
                    while True:
                        f = vc.most_recent_frame()
                        resized = cv2.resize(f, (300, 200))
                        cv2.imshow("Preview", resized)

                        keypress = cv2.waitKey(1)
                        if keypress & 0xFF == ord('q'):
                            break

                        time.sleep(1)

    cv2.destroyWindow("Preview")
    log.info("Combine and compress recording information.")
    pyvr.combine_video_and_audio(f"{FILE_NAME}.{VIDEO_EXT}",
                                 f"{FILE_NAME}.{AUDIO_EXT}",
                                 f"{FILE_NAME}.{RESULT_EXT}"
                                 )
    # delete video and audio files.
    os.remove(f"{FILE_NAME}.{VIDEO_EXT}")
    os.remove(f"{FILE_NAME}.{AUDIO_EXT}")

    log.info(f"Process complete. Results stored in {FILE_NAME}.{RESULT_EXT}")


if "__main__" == __name__:
    main()
