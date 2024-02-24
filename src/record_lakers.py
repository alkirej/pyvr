from record import *

import subprocess as proc

def prompt_to_start() -> None:
    print()
    input("START video AND press ENTER simultaneously now: ")
    print()


def main() -> None:
    play_video_args: [str] = \
        ["python", "/home/jeff/git/pyvr/src/play_video.py", "2>/dev/null"]

    with proc.Popen(play_video_args, text=True, stderr=proc.PIPE) as process:
        print()
        print()
        file_name = prompt_for_filename()
        duration = prompt_for_duration()
        prompt_to_start()
        process.terminate()

    print(f"Record to:  {file_name}.mkv")
    print(f"Record for: {duration}")

    start_time: dt.datetime = dt.datetime.now()
    record(file_name,
           start_time,
           compute_end_time(None, duration, None),
           False
           )


if "__main__" == __name__:
    main()
