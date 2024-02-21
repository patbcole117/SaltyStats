import configparser
import logging
import logging.config
import time

CONFIGURATION_FILENAME = "saltystat.conf"

class Config:
    def __init__(self):
        self.conf = configparser.ConfigParser()
        self.conf.read(CONFIGURATION_FILENAME)
        self.banner         = self.conf["DEFAULT"]["BANNER"]
        self.saltyurl       = self.conf["DEFAULT"]["SALTYBET_URL"]
        self.sleep          = int(self.conf["DEFAULT"]["SLEEP"])
        self.db_url         = self.conf["DATABASE"]["MONGO_URL"]
        self.db_locale      = self.conf["DATABASE"]["LOCALE"]
        self.db_user        = self.conf["DATABASE"]["MONGO_USER"]
        self.db_pw          = self.conf["DATABASE"]["MONGO_PASSWORD"]
        self.db_type        = self.conf["DATABASE"]["DB_TYPE"]
        self.ffmpeg_path    = self.conf["REC"]["FFMPEG_PATH"]
        self.root_path      = self.conf["REC"]["ROOT_PATH"]
        self.quality        = self.conf["REC"]["QUALITY"]
        self.streamname     = self.conf["REC"]["STREAM"]
        self.log_level      = self.conf["handler_console"]["level"]
        

        logging.config.fileConfig(CONFIGURATION_FILENAME)
        logging.Formatter.converter = time.gmtime
        self.log = logging.getLogger("saltylogger")
