"""
The MIT License

Copyright (c) 2023 Xavier Mercerweiss

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import multiprocessing as mp
import logging
import ctypes
import time

from src.operations import DETECTION_OPERATIONS
from src.config import Configuration
from src.daemon import Daemon
from src.devil import Devil


class Cyberus:
    """
    The root object of the Cyberus program
    """

    SHUTDOWN_EXCEPTIONS = (
        StopIteration,
        KeyboardInterrupt,
    )

    CONFIG_ERRORS = (
        TypeError,
        ValueError
    )

    STARTUP_MESSAGE = "Startup initiated"
    SHUTDOWN_MESSAGE = "Shutdown initiated"
    CLOSING_MESSAGE = "Closing root...\n"

    CHECKERS_SUCCESS_MESSAGE = "Successfully started checker"
    EXECUTOR_SUCCESS_MESSAGE = "Successfully started executor"

    def __init__(self):
        self._configuration = Configuration.instance
        self._current_threat_level = mp.Value(ctypes.c_uint)
        self._daemon = Daemon(self._current_threat_level, DETECTION_OPERATIONS)
        self._devil = Devil(self._current_threat_level)
        self._logger = self._build_logger()
        self._error_queue = mp.Queue()

    def start(self):
        """
        Begins execution of Cyberus
        """
        self._logger.info(self.STARTUP_MESSAGE)
        self._start_processes()
        self._handle_exceptions()

    def stop(self):
        """
        Ends execution of Cyberus safely
        """
        self._daemon.terminate_checkers()
        self._devil.terminate_executors()
        self._logger.info(self.CLOSING_MESSAGE)

    def _build_logger(self):
        """
        Builds a root logger based on the contents of the Configuration singleton
        :return: An appropriate logging.logger object
        """
        logger = logging.getLogger("root")
        handler = logging.FileHandler(self._configuration.root_log)
        handler.setFormatter(self._configuration.get_logging_formatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger

    def _start_processes(self):
        """
        Activates Cyberus processes based on the contents of the Configuration singleton
        """
        self._daemon.start_checkers(self._error_queue)
        self._logger.info(self.CHECKERS_SUCCESS_MESSAGE)
        self._devil.start_executor(self._error_queue)
        self._logger.info(self.EXECUTOR_SUCCESS_MESSAGE)

    def _handle_exceptions(self):
        """
        Ensures exceptions and shutdowns from all active Cyberus processes are handled; ensures safe shutdowns
        """
        try:
            self._await_errors()
        except self.SHUTDOWN_EXCEPTIONS:
            self._logger.info(self.SHUTDOWN_MESSAGE)
        except Exception as e:
            self._logger.critical(e)
            raise e
        finally:
            self.stop()

    def _await_errors(self):
        """
        Handles or forwards any exceptions raised within active Cyberus processes
        """
        while True:
            if self._error_queue.empty():
                time.sleep(self._configuration.delay)
            else:
                exception = self._error_queue.get()
                exception_type = type(exception)
                self._logger.error(f"{exception_type.__name__} : {exception}")
                self._handle_exception(exception, exception_type)

    def _handle_exception(self, exception, exception_type):
        """
        Handles an exception based on its type
        :param exception: An arbitrary exception
        :param exception_type: The class of 'exception'
        """
        if exception_type in self.CONFIG_ERRORS:
            self._configuration.raise_config_file_error()
        else:
            raise exception

