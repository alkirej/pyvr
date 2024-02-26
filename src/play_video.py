import logging as log
import time

import pyvr

log.basicConfig(filename="play_video.log",
                filemode="w",
                format="%(asctime)s %(filename)15.15s %(funcName)15.15s %(levelname)5.5s %(lineno)4.4s %(message)s",
                datefmt="%Y%m%d %H%M%S"
                )
log.getLogger().setLevel(log.DEBUG)


def main() -> None:
    with pyvr.VideoCard() as vc:
        with pyvr.VideoPlayer(vc) as vp:
            with pyvr.AudioInput() as ai:
                with pyvr.AudioPlayer(ai) as ap:
                    while vp.processing:
                        # Save some cpu for other people. Sleep and only show an occasional update.
                        time.sleep(0.25)
                    ap.processing = False
                    ai.new_audio_sample = False


if "__main__" == __name__:
    main()
