import os
import signal
import logging
import datetime
import time
from logging.handlers import RotatingFileHandler

logger = logging.getLogger("wssample")

# Get hold of the configuration file (package_config.ini)
moduledir = os.path.abspath(os.path.dirname(__file__))
BASEDIR = os.getenv("CAF_APP_PATH", moduledir)

# If we are not running with CAF, use the BASEDIR to get cfg file
tcfg = os.path.join(BASEDIR, "package_config.ini")
CONFIG_FILE = os.getenv("CAF_APP_CONFIG_FILE", tcfg)


def setup_logging(cfg):
    """
    Setup logging for the current module and dependent libraries based on
    values available in config.
    """
    # set a format which is simpler for console use
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')

    # Set log level based on what is defined in package_config.ini file
    loglevel = cfg.getint("logging", "log_level")
    logger.setLevel(loglevel)

    # Create a console handler only if console logging is enabled
    ce = cfg.getboolean("logging", "console")
    if ce:
        console = logging.StreamHandler()
        console.setLevel(loglevel)
        console.setFormatter(formatter)
        # add the handler to the root logger
        logger.addHandler(console)

    # The default is to use a Rotating File Handler
    log_file_dir = os.getenv("CAF_APP_LOG_DIR", "/tmp")
    log_file_path = os.path.join(log_file_dir, "thingtalk.log")

    # Lets cap the file at 1MB and keep 3 backups
    rfh = RotatingFileHandler(log_file_path, maxBytes=1024*1024, backupCount=3)
    rfh.setLevel(loglevel)
    rfh.setFormatter(formatter)
    logger.addHandler(rfh)


# Gracefully handle SIGTERM and SIGINT
def handle_signal(signum, stack):
    logger.info('Received Signal: %s', signum)
    # Raise a KeyboardInterrupt so that the main loop catches this and shuts down
    raise KeyboardInterrupt

signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)


if __name__ == '__main__':
    from ConfigParser import SafeConfigParser
    from websocket import create_connection

    cfg = SafeConfigParser()
    cfg.read(CONFIG_FILE)
    setup_logging(cfg)
    wsserver = cfg.get("ws","server", None)
    ws = create_connection(wsserver)

    def terminate_self():
        logger.info("Stopping the application")
        try:
            ws.close()
        except Exception as ex:
            logger.exception("Error stopping the app gracefully.")
        logger.info("Killing self..")
        os.kill(os.getpid(), 9)

    while True:
        try:
            msg = "Current date and time is : %s" % str(datetime.datetime.now())
            print "Sending Message: %s" % msg
            ws.send(msg)
            print "\t > Sent"
            print "\t < Receiving..."
            result =  ws.recv()
            print "Received '%s'" % result    
            print "Sleeping for 5 seconds.."
            time.sleep(5)    
        except KeyboardInterrupt:
            terminate_self()
        except Exception as ex:
            logger.exception("Caught exception! Terminating..")
            terminate_self()
