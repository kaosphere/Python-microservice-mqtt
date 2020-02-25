import paho.mqtt.client as mqtt
from config import *
import json
import threading
import sys


class MqttClient:
    """
    Mqtt client with specific parser
    """

    def __init__(
        self,
        logger,
        mqtt_host,
        mqtt_port,
        topic_list,
        loop_start=False,
        topic_list_unsubscribe=[],
    ):
        """
        Create an Mqtt client
        :param mqtt_host: Address of mqtt server
        :param mqtt_port: Port to connect to server
        :param topic_list: List of topics to subscribe to
        :param loop_start: If true, loop_start will be called on mqtt client. This will
                           launch a thread waiting for mqtt messages on subscribed topics.
        """
        self.logger = logger
        self.command = None
        self.data = None
        self.topic_list = topic_list
        self.topic_list_unsubscribe = topic_list_unsubscribe
        self.loop_start = loop_start

        self.clientMqtt = mqtt.Client()
        self.clientMqtt.on_message = self.on_message
        self.clientMqtt.on_connect = self.on_connect
        self.clientMqtt.connect(mqtt_host, mqtt_port)
        self.mqtt_connect_event = threading.Event()

        self.logger.v("MQTT client init")

        if self.loop_start:
            self.clientMqtt.loop_start()
            self.mqtt_connect_event.wait()

    def on_connect(self, client, userdata, flags, rc):
        """
        Called by paho mqtt client librairie when client is connected to mosquitto
        Subscribe to topic_list after connection (subscribe should be done after connection)
        :param client:
        :param userdata:
        :param flags:
        :param rc:
        :return:
        """
        try:
            for topic in self.topic_list:
                self.clientMqtt.subscribe(topic)
                self.logger.d("subscribe on " + topic)
            for topic in self.topic_list_unsubscribe:
                self.clientMqtt.unsubscribe(topic)
                self.logger.d("unsubscribe on " + topic)
            self.mqtt_connect_event.set()
        except Exception as e:
            import traceback
            exc_type, exc_obj, exc_tb = sys.exc_info()
            exceptionStr = (
                    os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    + ", line "
                    + str(exc_tb.tb_lineno)
                    + " : "
                    + str(e) +
                    "".join(traceback.format_tb(e.__traceback__))
            )
            self.logger.e(exceptionStr)

    # The callback for when a PUBLISH message is received from the server.
    def on_message(self, client, user_data, msg):
        """
        Called when an MQTT message is received
        :param client:
        :param user_data:
        :param msg:
        :return:
        """
        self.logger.d("mqtt message received")
        self.logger.d(msg.topic + " " + str(msg.payload))

        parsed_json = json.loads(msg.payload.decode("utf-8"))
        self.parse_mqtt(parsed_json, msg.topic)

    # overrided by children
    def parse_mqtt(self, parsed_json, topic):
        """
        Parse MQTT message received in on_message and save data in  attribute
        :param parsed_json:
        :param topic:
        :return:
        """
        try:
            try:
                self.command = parsed_json["command"]
            except:
                self.logger.i("Operation must be specified")
            try:
                self.data = parsed_json["data"]
            except:
                self.data = None
            self.topic = topic

        except Exception as e:
            self.logger.e("MQTT parser error")
            import traceback
            exc_type, exc_obj, exc_tb = sys.exc_info()
            exceptionStr = (
                    os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    + ", line "
                    + str(exc_tb.tb_lineno)
                    + " : "
                    + str(e) +
                    "".join(traceback.format_tb(e.__traceback__))
            )
            self.logger.e(exceptionStr)

    def publish_mqtt(self, id, payload, topic):
        """
        Publish MQTT message
        :param id:
        :param payload:
        :param topic:
        :return:
        """
        try:
            self.logger.d("mqtt message sent")
            if id == "":
                id = None
            dict_to_send = {"id": id, "payload": payload}
            self.logger.d(topic + " " + str(dict_to_send))
            self.clientMqtt.publish(
                topic, (json.dumps(dict_to_send)).encode("utf-8")
            )  # publish
        except Exception as e:
            import traceback
            exc_type, exc_obj, exc_tb = sys.exc_info()
            exceptionStr = (
                    os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    + ", line "
                    + str(exc_tb.tb_lineno)
                    + " : "
                    + str(e) +
                    "".join(traceback.format_tb(e.__traceback__))
            )
            self.logger.e(exceptionStr)

    def publish_json_mqtt(self, parsed_json, topic):
        """
        Publish parsed_json without interpretation
        :param parsed_json:
        :param topic:
        :return:
        """
        self.logger.d("mqtt message sent")
        self.logger.d(topic + " " + str(parsed_json))
        self.clientMqtt.publish(
            topic, (json.dumps(parsed_json)).encode("utf-8")
        )  # publish

    def run(self):
        pass
