"""
Routines that can be used to simplify or remove the interaction with the classes
"""
from ffmpeg import FFmpeg
import os


def combine_video_and_audio(video_file: str, audio_file: str, resulting_file: str) -> None:
    """
    :about: Routine to combine a video file (with no audio) and an audio file into a single
            file using the H.265 codec creating a that is as small as possible without losing
            its quality.

    :param video_file: filename of the video file as a string (must end in .mp4)
    :param audio_file: filename of the audio file as a string (must end in .wav)
    :param resulting_file: store the resulting combined file in this filename (must end in .mkv)
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
