import gzip
import shutil
import os
import logging
from logging import handlers
from logging import config


def init(file_path: str):
    if not ("logs" in os.listdir()):
        os.mkdir("logs")

    fmt = "%(levelname)s\t%(asctime)s\t%(pathname)s\t[%(filename)s:%(funcName)s:%(lineno)d]: %(message)s"
    formatter = logging.Formatter(fmt=fmt)

    logger = logging.getLogger()
    logger.setLevel(logging.NOTSET)

    def namer(name):
        return name + ".gz"

    def rotator(source, dest):
        with open(source, 'rb') as f_in:
            with gzip.open(dest, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        os.remove(source)

    # file_handler = logging.FileHandler("logs/tg_bot.log")
    # file_handler = handlers.RotatingFileHandler("logs/tg_bot.log", backupCount=16, maxBytes=1024 * 1024 * 128)
    file_handler = handlers.TimedRotatingFileHandler(file_path, backupCount=32, when="midnight")
    file_handler.rotator = rotator
    file_handler.namer = namer

    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.WARNING)
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)