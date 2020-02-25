import sys
import time
import argparse
import log

from config import *
import services.core.core as core

#####################################
# ---------- MAIN ---------- #
#####################################


def main():
    parser = argparse.ArgumentParser(description='Micro Services')
    parser.add_argument("-l", "--log_level", help="logging level: higher the value, the more logs you get",
                        required=False, default=log.LEVEL_DEBUG, type=int)
    parser.add_argument("-S", "--selective_logging", help="Selective logging, service names in parameters",
                        action='store', nargs='+', required=False, metavar="services")
    parser.add_argument("-r", "--max_restart", help="Maximum number of restart tries when a service doesn't run.",
                        default=3, type=int)
    parser.add_argument("-d", "--daemon", help="Enable daemon mode ", required=False, action="store_true")

    args = parser.parse_args()

    # If selective logging is used
    if args.selective_logging:
        # Get selective modules
        log.SELECTIVE_LOGGING = True
        log.LOGGING_MODULES = args.selective_logging

    if args.log_level:
        log.CURRENT_LEVEL = args.log_level

    if args.max_restart:
        core.MAX_RESTART_RETRY = args.max_restart

    core_service = core.Core(args.daemon)

    try:
        core_service.run()
    except SignalShutDown:
        pass
    except KeyboardInterrupt:
        pass
    finally:
        pass
        core_service.logger.i("Ending microservices...")
        core_service.kill_all_services()
        import os
        import signal
        os.kill(os.getpid(), signal.SIGKILL)


if __name__ == "__main__":  # pragma: no cover
    main()
