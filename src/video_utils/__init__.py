import ffmpeg
from ffmpeg import FFmpeg, Progress


def combine_video_and_audio(video_file: str, audio_file: str, resulting_file: str) -> None:
    assert video_file.endswith(".mp4")
    assert audio_file.endswith(".wav")
    assert resulting_file.endswith(".mkv")

    combine_and_compress = (FFmpeg()
                            .input(video_file)
                            .input(audio_file)
                            .output(resulting_file, {"codec:v": "libx265"})
                            )

    """
    @ffmpeg.on("progress")
    def show_progress(progress: Progress):
        print(f"frame={progress.frame}")
    """

    combine_and_compress.execute()
