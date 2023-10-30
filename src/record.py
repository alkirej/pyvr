import logging as log
# SETUP LOGGER BEFORE IMPORTS SO THEY CAN USE THESE SETTINGS
log.basicConfig(filename="pyvr.log",
                filemode="w",
                format="%(asctime)s %(filename)15.15s %(funcName)15.15s %(levelname)5.5s %(lineno)4.4s %(message)s",
                datefmt="%Y%m%d %H%M%S"
                )
log.getLogger().setLevel(log.DEBUG)

import pyvr

def main() -> None:
    pyvr.record("recording")

if "__main__" == __name__:
    main()
