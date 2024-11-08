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
import math


class Configuration:
    """
    A singleton representing the contents of an arbitrary configuration file
    """

    DEFAULT_VALUES = {
        "log_message_format": ("%time% : %level% : %message%",),
        "log_time_format": ("",),
        "shutdown_on_contingency": (False,),
    }

    LOG_FORMAT_TOKENS = {
        "%module%": "%(module)-16s",
        "%level%": "%(levelname)-8s",
        "%name%": "%(name)-6s",
        "%line%": "%(lineno)-5s",
        "%time%": "%(asctime)s",
        "%message%": "%(message)s",
        "%file%": "%(filename)s",
    }

    instance = None

    @staticmethod
    def as_number(value):
        """
        Converts a given string into a float or integer if such a conversion is valid
        :param value: A string
        :return: The input's representation as a float or integer, if valid
        """
        try:
            part = float(value)
            whole = math.floor(part)
            return whole if whole == part else part
        except ValueError:
            return None

    @classmethod
    def detoken_log_format(cls, log_format):
        """
        Converts any tokens present within the given string with those used by the logging module Formatter class
        :param log_format:
        :return:
        """
        output = log_format
        for token, value in cls.LOG_FORMAT_TOKENS.items():
            output = output.replace(token, value)
        return output

    def __new__(cls, *args, **kwargs):
        cls.instance = super().__new__(cls)
        return cls.instance

    def __init__(self, conf_path, metaconf_path):
        """
        Generates an arbitrary configuration based on the provided conf and metaconf paths
        :param conf_path: The path to a config file to be represented by the Configuration singleton
        :param metaconf_path: The path to a colon-delimited config file describing the formatting used by the config
        file
        """
        self._conf_error = ValueError(
            f"Invalid config file passed to {repr(type(self).__name__)}, examine {conf_path}"
        )
        self._metaconf_error = ValueError(
            f"Invalid metaconfig file passed to {repr(type(self).__name__)}, examine {metaconf_path}"
        )
        self._config_dict = self.DEFAULT_VALUES
        try:
            metaconfig_dict = self.read_config_file(metaconf_path, ":")
            self._assigner = metaconfig_dict["assignment_delimiter"][0]
            self._separator = metaconfig_dict["value_delimiter"][0]
            self._commenter = metaconfig_dict["comment_signature"][0]
            self._spacer = metaconfig_dict["word_delimiter"][0]
        except (ValueError, KeyError):
            self.raise_metaconfig_file_error()

        try:
            self._config_dict.update(
                self.read_config_file(
                    conf_path,
                    self._assigner,
                    self._separator,
                    self._commenter,
                )
            )
        except ValueError:
            self.raise_config_file_error()

        true_log_format = self.detoken_log_format(self.log_message_format)
        self._config_dict["log_message_format"] = (true_log_format,)

    def __getattr__(self, item):
        return self.__getitem__(item)

    def __setattr__(self, key, value):
        if key.startswith("_") or key not in self._config_dict:
            super().__setattr__(key, value)
        else:
            self.__setitem__(key, value)

    def __getitem__(self, item):
        if item in self._config_dict:
            value = self._config_dict[item]
            return value[0] if len(value) == 1 else value
        else:
            msg = f"{repr(type(self).__name__)} has no attribute {repr(item)}"
            raise AttributeError(msg)

    def __setitem__(self, key, value):
        msg = f"Attempted to write to config value; all config values are read-only"
        raise AttributeError(msg)

    def __contains__(self, item):
        return item in self._config_dict

    def __str__(self):
        output = ""
        for k, v in self._config_dict.items():
            output += f"{k}: {v}\n"
        return output

    def get(self, value, default=None):
        """
        Returns the value mapped to the given string if present, otherwise returns a non-None default value if provided
        :param value: A string
        :param default: (Optional) a non-None value to be returned if the given value has no mapping in the config
        :return: the value mapped to the given string or a non-None default
        """
        return self._get_value(value, default, is_raw=False)

    def get_raw(self, value, default=None):
        """
        Returns the value mapped to the given string as represented within the Configuration singleton if present,
        otherwise returns a non-None default value if provided
        :param value: A string
        :param default: (Optional) a non-None value to be returned if the given value has no mapping in the config
        :return: the value mapped to the given string as internally represented or a non-None default
        """
        return self._get_value(value, default, is_raw=True)

    def get_epithets(self, term):
        """
        Returns all values present within the config whose titles start with the given term (each 'epithet') as a dict
        :param term: The term against which each value's title is to be checked
        :return: A dict mapping each epithet to its value
        """
        epithets = {}
        term_length = len(term.split(self._spacer))
        for key in self._config_dict:
            lowered = key.lower()
            if lowered != term and lowered.startswith(term):
                split = lowered.split(self._spacer)
                epithet = self._spacer.join(split[term_length:])
                epithets[epithet] = self[key]
        return epithets

    def get_logging_formatter(self):
        """
        Generates a logging.Formatter instance based on the contents of the config
        :return: A logging.Formatter instance matching the contents of the config
        """
        return logging.Formatter(self.log_message_format, self.log_time_format)

    def raise_config_file_error(self):
        """
        Raises an exception stating that an error is present within the given config file
        """
        raise self._conf_error

    def raise_metaconfig_file_error(self):
        """
        Raises an exception stating that an error is present within the given metaconfig file
        """
        raise self._metaconf_error

    def read_config_file(self, conf_path, assignment_delimiter, value_delimiter=None, comment_signature=None):
        """
        Reads the contents of a given config file based on the specified formatting
        :param conf_path: The path to a config file
        :param assignment_delimiter: A character representing value assignment within the config file
        :param value_delimiter: A character representing value delimitation within the config file
        :param comment_signature: A character representing the start of a comment within the config file
        :return: The contents of the config as a dict
        """
        output = {}
        with open(conf_path, "r") as conf_file:
            for line in conf_file.readlines():
                if comment_signature is None:
                    interpreted = line.strip()
                else:
                    interpreted = line.strip().split(comment_signature)[0]
                if interpreted:
                    key, values = interpreted.split(assignment_delimiter)
                    output[key.lower()] = self._process_values(values, value_delimiter)
        return output

    def _get_value(self, value, default, is_raw):
        """
        Gets the value mapped to the given string within the config if present, otherwise returns the default if the
        default is a non-None value, otherwise raises an exception
        :param value: A string
        :param default: A default value
        :param is_raw: Whether the mapped value, if present, should be returned as its internal representation
        :return: The value mapped to the given string within the config if present, otherwise the default if the
        default is a non-None value
        """
        try:
            if is_raw:
                return self._config_dict[value]
            else:
                return self[value]
        except (KeyError, AttributeError) as e:
            if default is None:
                raise e
            else:
                return default

    def _process_values(self, values, value_delimiter):
        """
        Splits a string of values along a given delimiter, then converts each value to its true data type
        :param values: A string of one or more values from a config file
        :param value_delimiter: A value delimiter
        :return: A tuple containing each value within the string as its true data type
        """
        values = tuple(values.strip().split(value_delimiter))
        length = len(values)
        if length == 0:
            msg = "Missing or invalid value in config file"
            raise ValueError(msg)
        else:
            return tuple(self._process_value(v) for v in values)

    def _process_value(self, value):
        """
        Converts a string into its representation within the Configuration singleton
        :param value: A string
        :return: The string's true value
        """
        capped = value.capitalize()
        number = self.as_number(value)
        if number is not None:
            return number
        elif capped == "True" or capped == "False":
            return eval(capped)
        else:
            return value
