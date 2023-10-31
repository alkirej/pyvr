# Python Video Recorder (pyvr)

## Installation:
1. Download/Clone the repository
2. Install the required libraries:
    * pip install -r requirements.txt
3. Execute the application:
    <pre>
    USAGE: python record.py [options]
       Options:
          -h, --help           show this help message and exit
          --file=FILENAME      Name of file to store results in (do NOT include an
                                   extension)
          --start=START_TIME   The time at which the recording should start (hh:mm)
                                   Note: Uses a 24-hour clock.
          --dur=RECORD_LENGTH  How long to record (hh:mm:ss).
          --stop=STOP_TIME     The time to stop recording (hh:mm). 
                                   Note: Uses a 24-hour clock.
    </pre>
4. Documentation for the library created for and used by this application, open up *src/doc/_build/html/index.html* in 
       a web browser
