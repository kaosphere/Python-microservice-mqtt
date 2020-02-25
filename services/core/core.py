import log
import sys
import time
import threading
import traceback
import os
import sdnotify

SRC_ROOT_DIR = "../../"
sys.path.append(SRC_ROOT_DIR)

from config import *
from services.service_base import ServiceBase
from broker.mqtt import MqttClient

SERVICE_CONF_FILE = "services.conf"
VERSION_FILE = "VERSION"

MAX_RESTART_RETRY = 3

class Core(MqttClient, ServiceBase):

    def __init__(self, daemon):

        ServiceBase.__init__(self, True)
        MqttClient.__init__(
            self,
            self.logger,
            MQTT_HOST,
            MQTT_PORT,
            [],
            loop_start=True,
        )
        self.logger.d("__init__")
        self.isDaemon = False
        if daemon:
            self.isDaemon = True
            self.daemon = sdnotify.SystemdNotifier()

        self.logger.i("Log level is " + str(log.CURRENT_LEVEL))
        self.logger.i("Maximum restart retry number is " + str(MAX_RESTART_RETRY))

        self.relaunchCnt = {}

        try:
            self.version = self.get_version()

            self.logger.i("Lauch Microservice %s" % self.version)

            self.services = self.get_service_list()

            if len(self.services) == 0:
                self.logger.i("No service is specified in services.conf. Exiting.")
                sys.exit(1)

            # Import and init plugin_modules
            for service in self.services:
                self.relaunchCnt[service["name"]] = 0
                self.init_service(service["name"], service["mandatory"])

        except Exception as e:
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
            raise(e)

    def get_service_list(self):
        """
            Returns the services to be launched that are specified inside services.conf file
        """
        services = []

        with open(SERVICE_CONF_FILE, mode='r', encoding='utf-8') as services_file:
            for service_line in services_file:
                service_line = service_line.rstrip('\n')

                # Don't include commented lines and empty lines
                if len(service_line) > 0:
                    if service_line[0] != '#' :

                        # A service is made of its name and its "mandatory" attribute which is "true" or "false"
                        # Verify that it's formatted well
                        if len(service_line.split(",")) != 2:
                            raise Exception("Service's format is wrong in services.conf : " + service_line)
                        elif service_line.split(",")[1] != "True" and service_line.split(",")[1] != "False":
                            raise Exception("Service's format is wrong in services.conf : " + service_line)
                        else :
                            services.append({"name":service_line.split(",")[0], "mandatory":service_line.split(",")[1]})

        return services

    def get_version(self):
        """
            Returns Current version of Alarm System
        """
        with open(VERSION_FILE, mode='r', encoding='utf-8') as version_file:
            return version_file.read().rstrip('\n')



    def init_service(self, service, mandatory):
        # Import service package
        self.logger.i("Importing " + service)

        service_name = service

        # If service is a path (ex : net/abstraction) we transform it to "net.abstraction" to import it
        # We also use only the final package part to name it => "abstraction"
        if len(service.split('/')) > 1 :
            service_name = service.split('/')[-1]
            exec("import services."  +
                 service.replace("/",".") + "." +
                 service_name + " as " +  service_name)
        else:
            exec("import services." + service + "." + service + " as " + service)

        # Init service
        capitalizedService = service_name[0].capitalize() + service_name[1:]
        exec("self." + service_name + "=" + service_name + "." + capitalizedService + "(" + mandatory +")")

    def launch_service(self, service):
        self.logger.i("Launching " + service)

        try:
            # If service string is a path, just use the package name
            if len(service.split('/')) > 1 :
                service = service.split('/')[-1]

            exec("self." + service + "_thread = threading.Thread(target=self." + service + ".run)")
            exec("self." + service + "_thread.start()")

        except Exception as e:
            print(e)

    def kill_all_services(self):
        pass


    def notify(self, notif):
        self.daemon.notify(notif)

    def run(self):
        global MAX_RESTART_RETRY

        try:
            for service in self.services:
                self.launch_service(service["name"])
                time.sleep(0.1)

            if self.isDaemon:
                self.daemon.notify("READY=1")


            while(1):
                self.logger.v("Checking threads...")

                # iterate over all thread objects to find the one missing
                for service in self.services:
                    self.isAlive = False

                    # If service string is a path, just use the package name
                    if len(service["name"].split('/')) > 1:
                        service_name = service["name"].split('/')[-1]
                    else :
                        service_name = service["name"]

                    exec("self.isAlive = self." + service_name + "_thread.isAlive()")

                    if self.isAlive:
                        self.logger.v(service_name + " is alive")
                        self.relaunchCnt[service_name] = 0

                    # Try to relaunch a crashed service if relaunching hasn't failed already
                    if not self.isAlive and self.relaunchCnt[service_name] < MAX_RESTART_RETRY:
                        self.logger.e(service_name + "_thread is inactive")
                        # Re-Init and Relaunch inactive thread if we have tried less than MAX_RESTART_RETRY times
                        self.logger.e("Restarting " + service_name + "_thread")
                        self.init_service(service["name"],service["mandatory"])
                        self.launch_service(service["name"])
                        self.relaunchCnt[service_name] += 1

                        if self.relaunchCnt[service_name] >= MAX_RESTART_RETRY:
                            # If service isn't mandatory, create fault on the gateway
                            if service["mandatory"] == "False":
                                pass
                                # self.send_service_fault_mqtt(CMD_ID_SERVICE_FAULT, service_name)
                            else:
                                self.logger.e("Max retry number was reached on a mandatory service. Send KO system message")
                                sys.exit(2)

                if self.isDaemon:
                    self.daemon.notify("WATCHDOG=1")
                time.sleep(25)

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            exceptionStr = (
                    os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    + ", line "
                    + str(exc_tb.tb_lineno)
                    + " : "
                    + str(e)
                    + "".join(traceback.format_tb(e.__traceback__))
            )
            exc_type, exc_obj, exc_tb = sys.exc_info()
            self.logger.e(exceptionStr)
