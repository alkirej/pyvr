import cv2
import logging as log
import time
import os

from audio_utils.AudioRecorder import AudioInput, AudioRecorder
from video_utils.VideoRecorder import VideoCard, VideoRecorder

import video_utils as vu


log.basicConfig(filename="pvr.log",
                filemode="w",
                format="%(asctime)s %(filename)15.15s %(funcName)15.15s %(levelname)5.5s %(lineno)4.4s %(message)s",
                datefmt="%Y%m%d %H%M%S"
                )
log.getLogger().setLevel(log.DEBUG)

log.debug("*** *** *** Begin record program *** *** ***")
with VideoCard() as vc:
    with VideoRecorder("testing-output.mp4", vc) as vr:
        with AudioInput(input_name="Pyle") as ai:
            with AudioRecorder(ai, filename="testing-output.wav") as ar:
                while True:
                    f = vc.most_recent_frame()
                    resized = cv2.resize(f, (300, 200))
                    cv2.imshow("Preview", resized)

                    vr.next_frame(f)
                    keypress = cv2.waitKey(1)
                    if keypress & 0xFF == ord('q'):
                        break

                    time.sleep(1)

fn = "testing-output.mkv"
if(os.path.isfile(fn)):
    os.remove(fn)

cv2.destroyWindow("Preview")
log.info("Combine and compress recording information.")
vu.combine_video_and_audio("testing-output.mp4", "testing-output.wav", "testing-output.mkv")
log.info(f"Process complete. Results stored in {'testing-output.mkv'}")
