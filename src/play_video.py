import cv2
import time

import pyvr


def main() -> None:
    _, _, preview_config = pyvr.load_config()

    scale: float = int(preview_config[pyvr.PreviewCfg.PLAYER_SCALE]) / 100.0
    width: int = int(preview_config[pyvr.PreviewCfg.WIDTH] * scale)
    height: int = int(preview_config[pyvr.PreviewCfg.HEIGHT] * scale)

    with pyvr.VideoCard() as vc:
        while True:
            # Preview the video being recorded.
            f = vc.most_recent_frame()
            resized = cv2.resize(f, (width, height))
            cv2.imshow("Currently Playing", resized)

            # Stop/end recording when escape key is pressed.
            keypress = cv2.waitKey(1)
            if keypress & 0xFF == 27:
                break

            # Save some cpu for other people. Sleep and only show an occasional update.
            time.sleep(1.0/60)

    cv2.destroyWindow("Currently Playing")


if "__main__" == __name__:
    main()

