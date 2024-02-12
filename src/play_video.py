import cv2
import time

import pyvr


def main() -> None:
    with pyvr.VideoCard() as vc:
        while True:
            # Preview the video being recorded.
            f = vc.most_recent_frame()
            cv2.imshow("Currently Playing", f)

            # Stop/end recording when escape key is pressed.
            keypress = cv2.waitKey(1)
            if keypress & 0xFF == 27:
                break

            # Save some cpu for other people. Sleep and only show an occasional update.
            time.sleep(1.0/60)

    cv2.destroyWindow("Currently Playing")


if "__main__" == __name__:
    main()

