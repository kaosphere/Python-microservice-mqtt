#!/usr/bin/env python

from time import time
from logging import handlers, addLevelName, Formatter, getLoggerClass, setLoggerClass, NOTSET, DEBUG
from config import FILE_LOG

"""
    Logging module, which provides logging interface. This way
    it is easier to modify logging if we want to.
"""

# logging supports these logging levels
#
# LOG_ERROR, LOG_WARNING, LOG_INFO, LOG_DEBUG, LOG_VERBOSE.

# Logging levels in our system: higher the value, the more (crap) you get

LEVEL_VERBOSE = 4
LEVEL_DEBUG = 3
LEVEL_INFO = 2
LEVEL_WARNING = 1
LEVEL_ERROR = 0


class Logging(getLoggerClass()):
    VERBOSE = 4

    def __init__(self, name, level=NOTSET):
        super().__init__(name, level)
        addLevelName(Logging.VERBOSE, "VERBOSE")

    def verbose(self, msg, *args, **kwargs):
        if self.isEnabledFor(Logging.VERBOSE):
            self._log(Logging.VERBOSE, msg, args, **kwargs)


setLoggerClass(Logging)

logger = Logging("Microservices", Logging.VERBOSE)

# FILE HANDLER
formatter = Formatter("%(asctime)s : %(name)s-%(serviceName)s: %(level)s : %(message)s")
file_handler = handlers.RotatingFileHandler(FILE_LOG, "a", maxBytes=10 * 1024 * 1024, backupCount=10)
file_handler.setLevel(Logging.VERBOSE)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

SELECTIVE_LOGGING = False
LOGGING_MODULES = []
CURRENT_LEVEL = LEVEL_VERBOSE


class Bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    NORMAL = '\033[39m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


log_messages = []


def add_log_message(level, tag, msg):
    global log_messages
    log_messages.append(LogMessage(level, tag, msg))


class LogMessage(object):

    def __init__(self, level, tag, msg, timestamp=None):
        self.level = level
        self.tag = tag
        self.msg = msg
        if not timestamp:
            timestamp = time()
        self.timestamp = timestamp

    def is_error(self):
        return self.level == LEVEL_ERROR

    def is_warning(self):
        return self.level == LEVEL_WARNING


class Logger(object):
    def __init__(self, service):

        self.log_to_console = True
        self.log = logger

        if type(service) == str:
            self.ident = service
        else:
            self.ident = service.__class__.__name__

        self.config = {"serviceName": self.ident, "level": ""}

    def print_to_console(self, msg, level):
        """
            Prints message to console using nice formatting.
        """
        # If we are in selective logging, we don't want to print any output
        # related to modules not in the LOGGING_MODULES list
        if SELECTIVE_LOGGING:
            if self.ident not in LOGGING_MODULES:
                return

        header = Bcolors.NORMAL
        failcolor = Bcolors.NORMAL
        if level == "INFO":
            header = Bcolors.OKGREEN
        elif level == "WARNING":
            header = Bcolors.WARNING
            failcolor = Bcolors.WARNING
        elif level == "ERROR":
            header = Bcolors.FAIL
            failcolor = Bcolors.FAIL

        print ((Bcolors.HEADER + "%s " + Bcolors.ENDC +
                ":" + header +" %s " + Bcolors.ENDC +
                failcolor + "- %s" + Bcolors.ENDC) % (self.ident.ljust(20), level.ljust(8), msg) )

    def v(self, msg):
        """
            Logs debug message.
        """
        if CURRENT_LEVEL < LEVEL_VERBOSE:
            return

        msg = str(msg)
        if self.log_to_console:
            self.print_to_console(msg.encode("utf8"), "VERBOSE")
        if CURRENT_LEVEL > 0:
            self.config["level"] = "VERBOSE"
            self.log.verbose(msg, extra=self.config)

    def d(self, msg):
        """
            Logs debug message.
        """

        if CURRENT_LEVEL < LEVEL_DEBUG:
            return

        msg = str(msg)
        if self.log_to_console:
            self.print_to_console(msg.encode("utf8"), "DEBUG")
        if CURRENT_LEVEL > 0:
            self.config["level"] = "DEBUG"
            self.log.debug(msg, extra=self.config)

    def i(self, msg):
        """
            Logs debug message.
        """
        if CURRENT_LEVEL < LEVEL_INFO:
            return

        msg = str(msg)
        if self.log_to_console:
            self.print_to_console(msg.encode("utf8"), "INFO")
        if CURRENT_LEVEL > 0:
            self.config["level"] = "INFO"
            self.log.info(msg, extra=self.config)

    def w(self, msg):
        """
            Logs warning message.
        """
        add_log_message(LEVEL_WARNING, self.ident, msg)
        if CURRENT_LEVEL < LEVEL_WARNING:
            return

        msg = str(msg)
        if self.log_to_console:
            self.print_to_console(msg.encode("utf8"), "WARNING")
        if CURRENT_LEVEL > 0:
            self.config["level"] = "WARNING"
            self.log.warning(msg, extra=self.config)

    def e(self, msg):
        """
            Logs error message.
        """
        add_log_message(LEVEL_ERROR, self.ident, msg)
        if CURRENT_LEVEL < LEVEL_ERROR:
            return

        msg = str(msg)
        if self.log_to_console:
            self.print_to_console(msg.encode("utf8"), "ERROR")
        if CURRENT_LEVEL > 0:
            self.config["level"] = "ERROR"
            self.log.error(msg, extra=self.config)


def write(data):
    """
        STDERR strings are written here. We print it to console, but we also
        save the error for later viewing from web interface. Makes debugging
        a much easier.
    """
    print(data)
    add_log_message(LEVEL_ERROR, "TRACEBACK", str(data))

__all__ = ["Logger", "LEVEL_DEBUG", "LEVEL_ERROR", "LEVEL_VERBOSE", "LEVEL_INFO", "LEVEL_WARNING",
           "CURRENT_LEVEL", "SELECTIVE_LOGGING"]
