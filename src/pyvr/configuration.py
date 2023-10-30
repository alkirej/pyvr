"""
Read pyvr.ini and set up the configuration for the pyvr package.
"""
import configparser as cp
import enum
import logging as log
import sys

_AUDIO_CFG = _VIDEO_CFG = _PREVIEW_CFG = None


def ensure_exists(_: str) -> None:
    """
    Dummy function that is called to make sure the passed item
    can be found (usually in a dictionary).
    """
    pass


class AudioCfg(str, enum.Enum):
    """
    Enumeration of the audio parameters that can be set via the .ini file
    and their corresponding name in the ini file.
    """
    DEVICE_NAME = "devicename"


class VideoCfg(str, enum.Enum):
    """
    Enumeration of the video parameters that can be set via the .ini file
    and their corresponding name in the ini file.
    """
    CODEC = "codec"
    DEVICE = "device"
    FPS = "fps"
    HEIGHT = "height"
    WIDTH = "width"


class PreviewCfg(str, enum.Enum):
    """
    Enumeration of the video preview parameters that can be set via the .ini file
    and their corresponding name in the ini file.
    """
    INTERVAL = "intervalinsecs"
    HEIGHT = "height"
    WIDTH = "width"


# LOAD CONFIGURATION
def load_config() -> (dict, dict):
    """
    Load pyvr.ini from the local directory and massage data to be used by the recorder.
    :returns: 2 dictionaries of configuration data.  The first is for the audio
                configurations and the second is for the video config.
    """
    global _AUDIO_CFG, _VIDEO_CFG, _PREVIEW_CFG
    if _AUDIO_CFG is not None or _VIDEO_CFG is not None:
        return _AUDIO_CFG, _VIDEO_CFG, _PREVIEW_CFG

    log.debug("Loading config (pyvr.ini) file.")
    config = cp.ConfigParser()
    config.read("pyvr.ini")

    try:
        log.debug("Load [AUDIO] section from pyvr.ini")
        # LOAD EACH SECTION AND ENSURE REQUIRED VALUES WERE PROVIDED
        audio_config = config["AUDIO"]
        ensure_exists(audio_config[AudioCfg.DEVICE_NAME])

        log.debug("Load [VIDEO] section from pyvr.ini")
        video_config = config["VIDEO"]
        ensure_exists(video_config[VideoCfg.DEVICE])
        ensure_exists(video_config[VideoCfg.WIDTH])
        ensure_exists(video_config[VideoCfg.HEIGHT])
        ensure_exists(video_config[VideoCfg.FPS])
        ensure_exists(video_config[VideoCfg.CODEC])

        log.debug("Load [PREVIEW] section from pyvr.ini")
        preview_config = config["PREVIEW"]
        ensure_exists(preview_config[PreviewCfg.INTERVAL])
        ensure_exists(preview_config[PreviewCfg.WIDTH])
        ensure_exists(preview_config[PreviewCfg.HEIGHT])

    except KeyError as ke:
        print()
        print("*** pyvr.ini is missing or formatted incorrectly.  Unable to continue. ***")
        print(f"    {str(ke)} is required!")
        print()
        log.critical("pyvr.ini is missing or formatted incorrectly.  Unable to continue.")
        log.exception(ke)
        log.debug(f"Section or key {str(ke)} is required.")
        sys.exit(1)

    # return data from newly read pyvr.ini.
    _AUDIO_CFG = audio_config
    _VIDEO_CFG = video_config
    _PREVIEW_CFG = preview_config
    return _AUDIO_CFG, _VIDEO_CFG, _PREVIEW_CFG
