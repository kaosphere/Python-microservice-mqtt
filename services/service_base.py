from abc import abstractmethod
from log import Logger

class ServiceBase(object):
    """
        Plugin modules have some common attributes and operations.
        This is base class to collect these common stuff.

        A mandatory service is required for the system to work properly
        If a mandatory service cannot run, it will stop the system
        If a non-mandatory service cannot run properly, it will create
        a fault in the system, but the system will still run in a degraded state.
    """

    def __init__(self, mandatory):
        # Every module has own logger object.
        # This was needed to get correct ident for each module in syslog
        self.logger = Logger(self)
        self.isMandatory = mandatory
        self.logger.i("__init__")

    def is_mandatory(self):
        return self.is_mandatory()

    @abstractmethod
    def run(self):
        pass

