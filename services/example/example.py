import log
import sys
import traceback
import time

SRC_ROOT_DIR = "../../"
sys.path.append(SRC_ROOT_DIR)

from config import *
from services.service_base import ServiceBase
from broker.mqtt import MqttClient

MAX_RESTART_RETRY = 3

class Example(MqttClient, ServiceBase):

    def __init__(self, mandatory):

        ServiceBase.__init__(self, mandatory)
        MqttClient.__init__(
            self,
            self.logger,
            MQTT_HOST,
            MQTT_PORT,
            ["test/test_topic"],
            loop_start=True,
        )
        self.logger.d("__init__")

    def parse_mqtt(self, parsed_json, topic):
        # Call base class parser
        MqttClient.parse_mqtt(self,parsed_json, topic)
        self.logger.d("Received command : " + self.command)
        self.logger.d("Received data : " + self.data)

    def run(self):
        # Do stuff
        while(1):
            self.logger.d("Example service running...")
            time.sleep(5)
