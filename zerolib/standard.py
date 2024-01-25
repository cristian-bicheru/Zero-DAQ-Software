"""
This file contains code which appears across the Monitor/Controller codebases
for the purpose of standardization.
"""
import os
import logging

logging_config = {
    "format" : "%(asctime)s | %(levelname)s: %(message)s [%(name)s line %(lineno)d in %(threadName)s]",
    "level" : logging.INFO,
    "datefmt" : "%m/%d/%Y %I:%M:%S %p"
}

formatter_config = {
    "fmt" : logging_config["format"],
    "datefmt" : logging_config["datefmt"]
}

def get_sensor_cfg_location():
    """
    The sensors.cfg file is intended to be in the root directory, so just
    recurse backwards until it exists.
    """
    path = "."

    while "sensors.cfg" not in os.listdir(path):
        path = f"../{path}"

    return path[:-1] + "sensors.cfg"

sensor_cfg_location = get_sensor_cfg_location()
