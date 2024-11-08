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


class Devil:

    SHUTDOWN_EXCEPTION = StopIteration

    EXECUTOR_STARTUP_MESSAGE = "Starting executor process..."
    EXECUTOR_STARTUP_SUCCESS_MESSAGE = "Successfully started executor process"

    CONTINGENCY_EXECUTION_MESSAGE = "Threshold exceeded, executing contingency scripts!"

    EXECUTOR_CLOSING_MESSAGE = "Closing executor processes..."
    EXECUTOR_CLOSING_SUCCESS_MESSAGE = "Successfully closed all executor processes"

    @staticmethod
    def _execute(path):
        with open(path, "r") as file:
            exec(file.read())

    def __init__(self, threat):
        self._configuration = Configuration.instance
        self._logger = self._build_logger()
        self._threat = threat
        self._processes = []

    def start_executor(self, error_queue):
        self._logger.info(self.EXECUTOR_STARTUP_MESSAGE)
        executor = HandledProcess(
            error_queue,
            target=self._build_executor(
                self._configuration.get_raw("contingency_scripts")
            )
        )

        executor.start()
        self._processes.append(executor)
        self._logger.info(self.EXECUTOR_STARTUP_SUCCESS_MESSAGE)

    def terminate_executors(self):
        self._logger.info(self.EXECUTOR_CLOSING_MESSAGE)
        for process in self._processes:
            process.terminate()
        self._logger.info(self.EXECUTOR_CLOSING_SUCCESS_MESSAGE)

    def _build_logger(self):
        logger = logging.getLogger("devil")
        handler = logging.FileHandler(self._configuration.executor_log)
        handler.setFormatter(self._configuration.get_logging_formatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger

    def _build_executor(self, scripts):

        def await_execution():
            while True:
                if self._threat.value >= self._configuration.threshold:
                    self._logger.warning(self.CONTINGENCY_EXECUTION_MESSAGE)
                    for script in scripts:
                        self._execute(script)
                    if self._configuration.shutdown_on_contingency:
                        raise self.SHUTDOWN_EXCEPTION
                time.sleep(self._configuration.delay)

        return await_execution
