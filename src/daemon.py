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

import logging
import time

from src.processes import HandledProcess
from src.config import Configuration


class Daemon:
    """
    Manages processes which constantly monitor the system
    """

    CHECKERS_STARTUP_MESSAGE = "Starting checker processes..."
    CHECKER_START_MESSAGE = "Started %s_checker"
    CHECKERS_STARTUP_SUCCESS_MESSAGE = "Successfully started all checker processes"

    VIOLATION_DETECTION_MESSAGE = "%s_checker detected a threat of "

    CHECKERS_CLOSING_MESSAGE = "Closing checker processes..."
    CHECKERS_CLOSING_SUCCESS_MESSAGE = "Successfully closed all checker processes"

    def __init__(self, current_threat_level, operations):
        self._configuration = Configuration.instance
        self._logger = self._build_logger()
        self._current_threat_level = current_threat_level
        self._checks = self._get_checks(operations)
        self._processes = []

    def start_checkers(self, error_queue):
        """
        Activates all monitoring ('checker') processes
        :param error_queue: A shared-memory queue to which any caught exceptions are added
        """
        self._logger.info(self.CHECKERS_STARTUP_MESSAGE)
        checkers = []
        for check in self._checks:
            check_name, check_function, args, kwargs = check
            checker = HandledProcess(
                error_queue,
                target=check_function,
                args=args,
                kwargs=kwargs
            )
            checkers.append(checker)
            checker.start()
            self._logger.info(self.CHECKER_START_MESSAGE % check_name)
        self._processes.extend(checkers)
        self._logger.info(self.CHECKERS_STARTUP_SUCCESS_MESSAGE)

    def terminate_checkers(self):
        """
        Terminates all active monitoring ('checker') processes
        """
        self._logger.info(self.CHECKERS_CLOSING_MESSAGE)
        for process in self._processes:
            process.terminate()
        self._logger.info(self.CHECKERS_CLOSING_SUCCESS_MESSAGE)

    def _build_logger(self):
        """
        Builds a daemon logger based on the contents of the Configuration singleton
        :return: An appropriate logging.logger object
        """
        logger = logging.getLogger("daemon")
        handler = logging.FileHandler(self._configuration.checker_log)
        handler.setFormatter(self._configuration.get_logging_formatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger

    def _get_checks(self, operations):
        """
        Determines which operations within a given set are contained within the Configuration singleton
        :param operations: A collection of arbitrary functions
        :return: A tuple of all chosen operations ('checks')
        """
        output = []
        for operation in operations:
            operation_name = operation.__name__
            if operation_name in self._configuration:
                check_function = self._build_check_function(operation)
                args = self._configuration.get_raw(operation_name)
                kwargs = self._configuration.get_epithets(operation_name)
                output.append(
                    (operation_name, check_function, args, kwargs)
                )
        return tuple(output)

    def _build_check_function(self, operation):
        """
        Builds a function which indefinitely performs a given operation as a method of monitoring
        :param operation: A chosen operation ('check') to be performed
        """
        detection_message = self.VIOLATION_DETECTION_MESSAGE % operation.__name__

        def perform_check(*args, weight=1, **kwargs):
            last_detected = 0
            for violations in operation(*args, **kwargs):
                detected = violations * weight
                change_in_detected = detected - last_detected
                with self._current_threat_level.get_lock():
                    self._current_threat_level.value += change_in_detected
                if change_in_detected > 0:
                    self._logger.warning(f"{detection_message}{detected}")
                last_detected = detected
                time.sleep(self._configuration.delay)

        return perform_check
