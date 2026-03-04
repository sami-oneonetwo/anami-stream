#!/usr/bin/env python3
"""
Logger

Centralized logging for anami-stream.
Mirrors anami-controller/utils/logger.py.
"""

import os
import sys
import logging
import threading
from logging.handlers import RotatingFileHandler

original_factory = logging.getLogRecordFactory()


def record_factory(*args, **kwargs):
    record = original_factory(*args, **kwargs)
    record.threadname = threading.current_thread().name
    return record


logging.setLogRecordFactory(record_factory)

os.makedirs('logs', exist_ok=True)

_loggers = {}


class Logger:
    DEFAULT_LOG_LEVEL = logging.INFO
    DEFAULT_FORMAT = '[%(asctime)s] [%(levelname)s] [%(threadname)s] [%(name)s] %(message)s'
    DEFAULT_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    DEFAULT_LOG_DIR = 'logs'
    DEFAULT_LOG_FILE = 'anami_stream.log'
    MAX_LOG_SIZE = 10 * 1024 * 1024  # 10 MB
    BACKUP_COUNT = 5

    @classmethod
    def setup(cls, log_level=None, log_file=None, console=True, file=True,
              format_str=None, date_format=None, log_directory=None):
        if isinstance(log_level, str):
            log_level = getattr(logging, log_level.upper(), cls.DEFAULT_LOG_LEVEL)
        else:
            log_level = log_level or cls.DEFAULT_LOG_LEVEL

        log_file = log_file or cls.DEFAULT_LOG_FILE
        format_str = format_str or cls.DEFAULT_FORMAT
        date_format = date_format or cls.DEFAULT_DATE_FORMAT
        log_directory = log_directory or cls.DEFAULT_LOG_DIR

        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)

        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        formatter = logging.Formatter(format_str, date_format)

        if console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)

        if file:
            if log_directory:
                os.makedirs(log_directory, exist_ok=True)
                log_file_path = os.path.join(log_directory, log_file)
            else:
                log_file_path = log_file

            file_handler = RotatingFileHandler(
                log_file_path,
                maxBytes=cls.MAX_LOG_SIZE,
                backupCount=cls.BACKUP_COUNT,
            )
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)

        cls._setup_params = {
            'log_level': log_level,
            'log_file': log_file,
            'console': console,
            'file': file,
        }

    @classmethod
    def get_logger(cls, name):
        if not hasattr(cls, '_setup_params'):
            cls.setup()

        if name in _loggers:
            return _loggers[name]

        logger = logging.getLogger(name)
        _loggers[name] = logger
        return logger


def get_logger(name):
    return Logger.get_logger(name)


def setup_logging(**kwargs):
    Logger.setup(**kwargs)


Logger.setup()
