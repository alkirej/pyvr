import calendar as cal
import cv2
import datetime as dt
import enum
import logging as log
import optparse as cl  # cl = command line.
import os
import sys
import time
import typing as typ

import pyvr

# SETUP LOGGER BEFORE IMPORTS SO THEY CAN USE THESE SETTINGS
log.basicConfig(filename="pyvr.log",
                filemode="w",
                format="%(asctime)s %(filename)15.15s %(funcName)15.15s %(levelname)5.5s %(lineno)4.4s %(message)s",
                datefmt="%Y%m%d %H%M%S"
                )
log.getLogger().setLevel(log.DEBUG)


class CommandLineOpts(str, enum.Enum):
    """
    Enumeration of the command line parameters that can be sent to the application.
    """
    DELETE = "delete"
    FILE_NAME = "filename"
    RECORD_LENGTH = "record_length"
    PROMPT = "prompt"
    START_TIME = "start_time"
    STOP_TIME = "stop_time"


def is_valid_duration(duration: str) -> bool:
    try:
        dur_parts = duration.split(":")
        part_count = len(dur_parts)

        # VALIDATE THE NUMBER OF PARTS. 1 (ss), 2 (mm:ss) and 3 (hh:mm:ss) ARE VALID.
        if part_count < 1 or part_count > 3:
            return False

        # ENSURE THE LENGTHS OF EACH PART ARE VALID
        for idx, part in enumerate(dur_parts):
            if 0 == idx:
                # The first section may have 1 or 2 numerals 0 to 59.
                if len(part) < 1 or len(part) > 2:
                    return False
            else:
                # Sections after the first must contain 2 numerals 00 to 59
                if len(part) != 2:
                    return False

        # VALIDATE EACH SECTION AS NUMERIC AND IN THE CORRECT RANGE.
        for idx, part in enumerate(dur_parts):
            value = int(part)
            if idx == 0:
                if value < 0 or value > 99:
                    return False
                else:
                    return True
            elif value < 0 or value > 59:
                return False
            else:
                return True

    except ValueError:
        return False


def is_valid_time(time_str: str) -> bool:
    try:
        dur_parts = time_str.split(":")
        part_count = len(dur_parts)

        # VALIDATE THE NUMBER OF PARTS. THERE MUST BE 2 hh:mm
        if part_count != 2:
            return False

        hour = int(dur_parts[0])
        if hour < 0 or hour > 23:
            return False

        minutes = int(dur_parts[1])
        if minutes < 0 or minutes > 59:
            return False

        return True

    except ValueError:
        return False


def parse_command_line() -> dict:
    parser = cl.OptionParser()
    parser.set_defaults(filename="recording")
    parser.add_option("--prompt",
                      dest=CommandLineOpts.PROMPT,
                      default=False,
                      action="store_true",
                      help="Prompt for options via command line."
                      )
    parser.add_option("--file",
                      dest=CommandLineOpts.FILE_NAME,
                      help="Name of file to store results in (do NOT include an extension)"
                      )
    parser.add_option("--start",
                      dest=CommandLineOpts.START_TIME,
                      help="The time at which the recording should start (hh:mm). Note: 24 hour clock."
                      )
    parser.add_option("--dur",
                      dest=CommandLineOpts.RECORD_LENGTH,
                      help="How long to record (hh:mm:ss)."
                      )
    parser.add_option("--stop",
                      dest=CommandLineOpts.STOP_TIME,
                      help="The time to stop recording (hh:mm). Note: 24 hour clock."
                      )
    parser.add_option("--del", "--delete",
                      dest=CommandLineOpts.DELETE,
                      default=False,
                      action="store_true",
                      help="Delete to original video and audio files."
                      )
    options, _ = parser.parse_args()

    # VALIDATE OPTION VALUES WHERE APPROPRIATE
    if options.start_time and not is_valid_time(options.start_time):
        parser.error("invalid start time.")

    if options.record_length and not is_valid_duration(options.record_length):
        parser.error("invalid value supplied with --dur.")

    if options.stop_time and not is_valid_time(options.stop_time):
        parser.error("invalid stop time.")

    if options.record_length and options.stop_time:
        parser.error("--dur and --stop are mutually exclusive.")

    return vars(options)


def compute_start_time(start_time: str) -> dt.datetime:
    if start_time is None:
        # BY DEFAULT START RIGHT NOW
        start_at: dt.datetime = dt.datetime.now()
    else:
        splits = [int(x) for x in start_time.split(":")]
        start_at = dt.datetime.now().replace(hour=splits[0], minute=splits[1])

    return start_at


def compute_end_time(start_time: typ.Optional[str], duration: str, stop_time: typ.Optional[str]) -> None | dt.datetime:
    if duration is None and stop_time is None:
        return None

    if stop_time is not None:
        splits = [int(x) for x in stop_time.split(":")]
        return dt.datetime.now().replace(hour=splits[0], minute=splits[1])
    start_at = compute_start_time(start_time)

    # DURATION MUST BE DEFINED, OR WE WOULDN'T BE HERE.
    hrs = mins = secs = 0
    splits = [int(x) for x in duration.split(":")]
    for idx, split in enumerate(reversed(splits)):
        match idx:
            case 0: secs = split
            case 1: mins = split
            case 2: hrs = split

    return start_at + dt.timedelta(hours=hrs, minutes=mins, seconds=secs)


def display_time_remaining(seconds_left: int) -> None:
    hours: int = seconds_left // (60*60)
    mins: int = (seconds_left - hours * (60*60)) // 60
    secs: int = seconds_left % 60

    print(f"Time remaining: \033[92m\033[1m{hours}:{mins:02}:{secs:02}\033[0m\r", end="")


def record(filename_no_ext: str,
           start_recording_at: dt.datetime,
           stop_recording_at: dt.datetime,
           delete_files: bool
           ) -> None:
    """
    :about: This is the main entrypoint to the pyvr package.  It is likely the only function
            you will use. **Call it to record video and audio from you system.**
    :param filename_no_ext: The name of the resulting file (without the .mkv extension).  This
                            filename will be used to create 2 intermediate files (one .wav and
                            one .mp4) that are combined after the recording is complete into
                            the .mkv file.
    :param start_recording_at: date/time the recording should start
    :param stop_recording_at: date/time the recording should complete
    :param delete_files:
    :Side Effect: Creation of a .mkv file recording the requested audio and video.

    ... note::
        This routine makes a great example of how to interact with the classes in this package.

            ... code-block:: python
                :caption: Sample Code using the AudioRecorder and VideoRecorder classes.

                    with VideoCard() as vc:
                        with VideoRecorder("video.mp4", vc):
                            with AudioInput(input_name="Pyle") as ai:
                                with AudioRecorder(ai, filename="audio.wav"):
                                    while True:
                                        f = vc.most_recent_frame()
                                        cv2.imshow("Preview", f)

                                        keypress = cv2.waitKey(1)
                                        if keypress & 0xFF == ord('q'):
                                            break
    """
    log.debug("*** *** *** Begin recording *** *** ***")

    # LOAD PREVIEW CONFIG ATTRIBUTES FROM pyvr.ini
    _, _, preview_config = pyvr.load_config()
    width: int = int(preview_config[pyvr.PreviewCfg.WIDTH])
    height: int = int(preview_config[pyvr.PreviewCfg.HEIGHT])
    interval: float = float(preview_config[pyvr.PreviewCfg.INTERVAL])

    # WAIT UNTIL WE SHOULD START RECORDING
    if start_recording_at is not None:
        begin: bool = False
        while not begin:
            current_time = dt.datetime.now()
            if current_time > start_recording_at:
                begin = True
            else:
                # SLEEP (ALMOST) ONE MINUTE AND CHECK AGAIN.
                time.sleep(59)

    # Each with line creates its own thread.
    with pyvr.VideoCard() as vc:
        with pyvr.VideoRecorder(f"{filename_no_ext}.{pyvr.VIDEO_EXT}", vc) as vr:
            print(f"Record resolution: ({vc.width}, {vc.height})")
            log.debug(f"Record resolution: ({vc.width}, {vc.height})")
            with pyvr.AudioInput() as ai:
                with pyvr.AudioRecorder(ai, filename=f"{filename_no_ext}.{pyvr.AUDIO_EXT}") as ar:
                    while True:
                        # Preview the video being recorded.
                        f = vc.most_recent_frame()
                        resized = cv2.resize(f, (width, height))
                        cv2.imshow("Preview", resized)

                        # Stop/end recording when escape key is pressed.
                        keypress = cv2.waitKey(1)
                        if keypress & 0xFF == 27:
                            break

                        # Stop recording if the end recording time is reached.
                        if stop_recording_at is not None:
                            current_time = dt.datetime.now()
                            if current_time > stop_recording_at:
                                break
                            else:
                                seconds_left: int = (stop_recording_at - current_time).seconds
                                display_time_remaining(seconds_left)

                        # Save some cpu for other people. Sleep and only show an occasional update.
                        time.sleep(interval)

                    ar.processing = False
                    ai.new_audio_sample = False

    print()
    cv2.destroyWindow("Preview")
    log.info("Combine and compress recording information.")
    print("Processing final results.  Please be patient ...")
    pyvr.combine_video_and_audio(f"{filename_no_ext}.{pyvr.VIDEO_EXT}",
                                 f"{filename_no_ext}.{pyvr.AUDIO_EXT}",
                                 f"{filename_no_ext}.{pyvr.RESULT_EXT}"
                                 )

    # delete video and audio files.
    if delete_files:
        os.remove(f"{filename_no_ext}.{pyvr.VIDEO_EXT}")
        os.remove(f"{filename_no_ext}.{pyvr.AUDIO_EXT}")

    log.info(f"Process complete. Results stored in {filename_no_ext}.{pyvr.RESULT_EXT}")


def prompt_for_duration() -> str:
    print()
    print("RECORD DURATION")
    int_hr = int(input("    Hours: "))
    if int_hr < 0 or int_hr > 4:
        print("INVALID RECORD DURATION (HOURS)")
        sys.exit(1)
    hrs = str(int_hr)

    int_min = int(input("    Minutes (0-59): "))
    if int_min < 0 or int_min > 59:
        print("INVALID RECORD DURATION (MINUTES)")
        sys.exit(1)
    mins = str(int_min)
    if len(mins) == 1:
        mins = f"0{int_min}"

    int_secs = int(input("    Seconds (0-59): "))
    if int_secs < 0 or int_secs > 59:
        print("INVALID RECORD DURATION (SECONDS)")
        sys.exit(1)
    secs = str(int_secs)
    if len(secs) == 1:
        secs = f"0{int_secs}"

    return f"{hrs}:{mins}:{secs}"


def prompt_for_filename() -> str:
    print("Game Date:")

    year = input("   Year: ")
    int_year = int(year)
    if int_year < 1950 or int_year > 2100:
        print("INVALID YEAR.")
        sys.exit(1)

    int_month = int(input("   Month (1-12): "))
    month = str(int_month)
    if int_month < 1 or int_month > 12:
        print("INVALID MONTH.")
        sys.exit(1)
    if len(month) < 2:
        month = "0" + month
    _, max_day = cal.monthrange(int_year, int_month)
    int_day = int(input(f"   Day of the Month (1-{max_day}): "))
    day = str(int_day)
    if int_day < 1 or int_day > max_day:
        print("INVALID DAY OF THE MONTH.")
        sys.exit(1)
    if len(day) < 2:
        day = "0" + day

    print()
    home = input("   (H)ome or (A)way? ")
    if home.lower() == "h":
        vs_str = "vs"
    elif home.lower() == "a":
        vs_str = "at"
    else:
        print("INVALID RESPONSE. PLEASE SELECT H OR A.")
        sys.exit(1)

    print()
    city = input("   Opponent: ")
    city = city.strip()
    city = city.replace(" ", "")

    if int_month <= 7:
        prefix = "1"
        season = str(int_year)
    else:
        prefix = ""
        season = str(int_year+1)

    print()
    notes = input("   Note: ")
    notes = notes.strip()
    notes = notes.replace(" ", "")
    if len(notes) > 0:
        notes = f"-{notes}"

    return f"{year}{month}{day}{vs_str}{city}-s{season}e{prefix}{month}{day}{notes}"


def main() -> None:
    cl_opts = parse_command_line()

    if cl_opts[CommandLineOpts.PROMPT]:
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
        # DELETE EXTRA FILES NOW?

    else:
        record_at: dt.datetime = compute_start_time(cl_opts[CommandLineOpts.START_TIME])
        record_until: dt.datetime = compute_end_time(cl_opts[CommandLineOpts.START_TIME],
                                                     cl_opts[CommandLineOpts.RECORD_LENGTH],
                                                     cl_opts[CommandLineOpts. STOP_TIME]
                                                     )
        record(cl_opts[CommandLineOpts.FILE_NAME],
               record_at,
               record_until,
               cl_opts[CommandLineOpts.DELETE]
               )


if "__main__" == __name__:
    main()
