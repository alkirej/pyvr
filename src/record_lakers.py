from record import *


def main() -> None:
    file_name = prompt_for_filename()
    duration = prompt_for_duration()

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
