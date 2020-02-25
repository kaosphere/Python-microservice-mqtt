import os
import signal

#####################################
# --------- GLOBAL CONFIG --------- #
#####################################
from os.path import dirname

WORKING_DIR = os.path.dirname(os.path.abspath(dirname(__file__)))
LOGFILE = "lastrun.log"
SERVICE_NAME = "system"

#####################################
# ---------- MQTT CONFIG ---------- #
#####################################
MQTT_HOST = os.getenv('MQTT_HOST', "127.0.0.1")
MQTT_PORT = int(os.getenv('MQTT_PORT', "1883"))
FILE_LOG = os.getenv("FILE_LOG", LOGFILE)


class SignalShutDown(Exception):
    pass


def handler_stop_signals(signum, frame):
    raise SignalShutDown("received shutdown signal")


signal.signal(signal.SIGINT, handler_stop_signals)
signal.signal(signal.SIGTERM, handler_stop_signals)
