from record import *

import string
import subprocess as proc
import sys

LAST_SERIES_NAME_FILE: str = ".last_series_name"


def save_previous_series(series_name: str) -> None:
    with open(LAST_SERIES_NAME_FILE, "w") as f:
        f.write(series_name)


def get_previous_series() -> str:
    try:
        with open(LAST_SERIES_NAME_FILE, "r") as f:
            text: str = f.read()
            if "\n" in text:
                return ""

        return text
    except FileNotFoundError:
        return ""


def contains_pun(text: str) -> bool:
    return any(ch in string.punctuation for ch in text)


def accept_int(prompt: str) -> int:
    str_val: str = input(f"    {prompt}: ")
    int_val: int = int(str_val)

    if int_val < 0 or int_val > 99:
        print("VALUE OUT OF RANGE!")
        sys.exit(1)

    return int_val


def prompt_for_movie_info() -> (str, str):
    # returns 2 paths.  The directory to store file in as well as the file name (sans extension)
    mov_type: str = input("(M)ovie or TV (E)pisode? ").lower()

    if mov_type not in ("m", "e"):
        print("INVALID MOVIE TYPE.")
        sys.exit(1)

    if mov_type == "m":
        year: str = input("    Movie year (4 digits): ")
        int_year: int = int(year)

        if int_year < 1850 or int_year > 2100:
            print("INVALID YEAR.")
            sys.exit(1)

        name: str = input("    Movie name: ")

        if contains_pun(name):
            print("NO PUNCTUATION ALLOWED IN MOVIE NAMES.  PLEASE TRY AGAIN WITHOUT PUNCTUATION.")
            sys.exit(1)

        file_name = f"{name} ({year})"
        return file_name, file_name

    else:
        prev_series: str = get_previous_series()
        series: str = input(f"    Series name [{prev_series}]: ")

        if contains_pun(series):
            print("NO PUNCTUATION ALLOWED IN NAMES.  PLEASE TRY AGAIN WITHOUT PUNCTUATION.")
            sys.exit(1)
        if series == "":
            series = prev_series

        save_previous_series(series)

        season: int = accept_int("Season #")
        episode: int = accept_int("Episode #")

        zero_maybe: str = ""
        if episode < 10:
            zero_maybe = "0"

        return f"{series}/Season {season}", f"{series}-s{season}e{zero_maybe}{episode}"


def prompt_to_start() -> None:
    print()
    input("START video AND press ENTER simultaneously now: ")
    print()


def main() -> None:
    play_video_args: [str] = \
        ["python", "/home/jeff/git/pyvr/src/play_video.py"]

    with proc.Popen(play_video_args, text=True, stderr=proc.PIPE) as process:
        print()
        print()

        dir_name, file_name = prompt_for_movie_info()
        duration = prompt_for_duration()
        prompt_to_start()
        process.terminate()

    full_path = os.path.join(dir_name, file_name)

    print(f"Record to:  {full_path}.mkv")
    print(f"Record for: {duration}")

    os.makedirs(dir_name, exist_ok=True)

    start_time: dt.datetime = dt.datetime.now()
    record(full_path,
           start_time,
           compute_end_time(None, duration, None),
           False
           )


if "__main__" == __name__:
    main()
