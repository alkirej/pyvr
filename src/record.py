import time
import cv2

from video_utils.VideoCard import VideoCard
from video_utils.VideoRecorder import VideoRecorder
from audio_utils.AudioInput import AudioInput

with AudioInput() as ai:
    with VideoCard() as vc:
        with VideoRecorder("testing-output.mp4", vc) as vr:
            while True:
                f = vc.most_recent_frame()
                resized = cv2.resize(f, (300,200))
                cv2.imshow("Preview", resized)

                vr.next_frame(f)
                keypress = cv2.waitKey(1)
                if keypress & 0xFF == ord('q'):
                    break

                time.sleep(1)

cv2.destroyWindow("Preview")