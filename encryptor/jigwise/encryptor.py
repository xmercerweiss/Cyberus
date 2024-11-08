"""
The MIT License

Jigwise:   Copyright (c) 2023 Xavier Mercerweiss
bitstring: Copyright (c) 2006 Scott Griffiths

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

import math
import string
import random
import secrets
import multiprocessing as mp
from collections import deque

import bitstring as bs

from encryptor.jigwise.table import Table
from encryptor.jigwise.manager import AccessManager, FileManager, PacketManager


class Encryptor(AccessManager):
    """
    Used to encrypt a given set of files according to the Jigwise encryption scheme
    """

    KEY_EXTENSION = "key"
    TABLE_EXTENSION = "table"
    CONFIG_EXTENSION = "conf"

    @staticmethod
    def __fewest_bits(num):
        """
        Determines the number of bits required to represent a given unsigned integer
        :param num: An unsigned integer
        :return: The number of bits needed to represent the given unsigned integer
        """
        if num == 0:
            return 1
        return math.floor(math.log2(num)) + 1

    @staticmethod
    def __get_ordinal_bit_increment(keys, bit_count):
        """
        Generates the spacing between each ordinal bit in the ordered keys
        :param keys: All unordered keys
        :param bit_count: The length of the smallest key in bits
        :return: The spacing between each ordinal bit in the ordered keys
        """
        minimum_length = min(len(k) for k in keys)
        rng = secrets.randbelow(minimum_length) + 1
        return math.ceil(minimum_length / (bit_count * rng))

    @staticmethod
    def __get_ordered_keys(keys, ordinal_bit_increment, ordinal_bit_count):
        """
        Inserts ordinal bits into each key such that the order in which they were used may be determined
        :param keys: All unordered keys
        :param ordinal_bit_increment: The spacing between each ordinal bit in the ordered keys
        :param ordinal_bit_count: The number of ordinal bits in the ordered keys
        :return: All ordered keys
        """
        output = []
        for order, key in enumerate(keys):
            bits = key.content
            ordinal_bits = bs.ConstBitStream(uint=order, length=ordinal_bit_count)
            for i in range(ordinal_bit_count):
                index = i * ordinal_bit_increment
                ordinal_bit = ordinal_bits.read("bits1")
                bits.insert(ordinal_bit, index)
            output.append(bits)
        return output

    @staticmethod
    def __random_chars(count=1):
        """
        Generates a string containing a given number of random ASCII letters
        :param count: The length of the output string
        :return: The output string
        """
        output = ""
        for _ in range(count):
            output += random.choice(string.ascii_letters)
        return output

    def __init__(self, operations, packet_size=256, symbol_length=6):
        """
        :param operations: A collection of 'Operation' namedtuples
        :param symbol_length: The number of bits to be used for the 'symbol' portion of each key
        """
        self.__table = Table(operations, symbol_length=symbol_length)
        self.__packet_size = packet_size
        self.__symbol_length = self.__table.symbol_length
        self.__remaining_length = 8 - self.__symbol_length

    def encrypt(self,
                *sources, content_destination=None, misc_destination=None,
                key_count=1, key_length=64, delete_source=True
                ):
        """
        Encrypts all given source files and directories, saves the encrypted content to 'content_destination,' and the
        keys, table, and config file to the 'misc_destination'
        :param sources: All files and directories to be encrypted
        :param content_destination: The file to which the encrypted data will be saved
        :param misc_destination: The directory to which the keys, table, and config file will be saved
        :param key_count: The number of keys to be used
        :param key_length: The length of each key to be used, in operations
        :param delete_source: Whether the sources files should be deleted once encrypted
        """
        cpu_count = mp.cpu_count()
        self.__table.reset_mappings()
        data = PacketManager(FileManager.assemble(*sources), self.__packet_size, cpu_count)
        if delete_source:
            FileManager.delete(*sources)
        keys = deque()
        for _ in range(key_count):
            instructions = self.__generate_instructions(key_length, data.packet_count)
            data.instruct(instructions)
            for k in keys:
                k.instruct(instructions)
            key = self.__build_key(instructions)
            keys.append(PacketManager(key, 1, cpu_count))
        ordinal_bit_count = self.__fewest_bytes(key_count) * 8
        ordinal_bit_increment = self.__get_ordinal_bit_increment(keys, ordinal_bit_count)
        ordered_keys = self.__get_ordered_keys(keys, ordinal_bit_increment, ordinal_bit_count)
        config = self.__build_config(cpu_count, ordinal_bit_increment, ordinal_bit_count)
        if content_destination is not None and misc_destination is not None:
            self.__export_products(content_destination, misc_destination, data.content, config, *ordered_keys)

    def __generate_instructions(self, instruction_length, content_length):
        """
        Generates a set of operations to be used to encrypt the input data
        :param instruction_length: The number of operations to be generated
        :param content_length: The length of the input data in packets
        """
        output = []
        for _ in range(instruction_length):
            operation = secrets.choice(self.__table.operations)
            start, stop = secrets.randbelow(content_length), secrets.randbelow(content_length)
            if stop < start:
                start, stop = stop, start
            additional = [secrets.randbelow(content_length) for _ in range(operation.args)]
            output.append((operation, start, stop, additional))
        return output

    def __build_key(self, instructions):
        """
        Builds a string of bits representing a given instruction set, the 'key'
        :param instructions: The instruction set to be converted into a key
        :return: The completed key
        """
        key = bs.BitStream()
        instructions.reverse()
        for instruction in instructions:
            op, start, stop, additional = instruction
            arguments = start, stop, *additional
            fewest_bytes = max(self.__fewest_bytes(a) for a in arguments)
            fewest_bits = fewest_bytes * 8
            key.append(self.__table[op])
            key.append(bs.Bits(uint=len(additional), length=self.__remaining_length))
            key.append(bs.Bits(uint=fewest_bytes, length=8))
            for arg in arguments:
                key.append(bs.Bits(uint=arg, length=fewest_bits))
        return key

    def __build_config(self, subdivision_count, ordinal_bit_increment, ordinal_bit_count):
        """
        Builds a string of bits representing the encryptor's configuration
        :param subdivision_count: The number of subdivisions the data was split into
        :param ordinal_bit_increment: The spacing between each ordinal bit in the ordered keys
        :param ordinal_bit_count: The number of ordinal bits in the ordered keys
        :return: The completed config bits
        """
        config = bs.BitArray()
        config.append(self.__build_config_value(self.__packet_size))
        config.append(self.__build_config_value(subdivision_count))
        config.append(self.__build_config_value(ordinal_bit_increment))
        config.append(self.__build_config_value(ordinal_bit_count))
        return config

    def __export_products(self, content_destination, misc_destination, encrypted, config, *keys):
        """
        Saves the encrypted data, keys, table, and config to their respective locations
        :param content_destination: The file to which the encrypted data will be saved
        :param misc_destination: The directory to which the keys, table, and config file will be saved
        :param encrypted: The encrypted data bits
        :param config: The config bits
        :param keys: All ordered keys
        """
        misc_destination = f"{misc_destination}/" if not misc_destination.endswith('/') else misc_destination
        FileManager.create_file(misc_destination)
        char_generator = self.__original_chars(5)
        self.export_data(content_destination, encrypted, is_bits=True)
        self.export_data(f"{misc_destination}config", config, is_bits=True)
        self.__table.export(f"{misc_destination}table")
        for key in keys:
            path = f"{misc_destination}{next(char_generator)}.{self.KEY_EXTENSION}"
            self.export_data(path, key, is_bits=True)

    def __fewest_bytes(self, num):
        """
        Determines the number of full bytes required to represent a given unsigned integer
        :param num: An unsigned integer
        :return: The number of full bytes required to represent a given unsigned integer
        """
        return math.ceil(self.__fewest_bits(num) / 8)

    def __build_config_value(self, value):
        """
        Converts a given unsigned integer into its representation within the config bits
        :param value:
        :return:
        """
        value_bytes = self.__fewest_bytes(value)
        value_length_bits = bs.Bits(uint=value_bytes, length=8)
        value_bits = bs.Bits(uint=value, length=value_bytes * 8)
        return value_length_bits + value_bits

    def __original_chars(self, length):
        """
        Generates a unique string of random characters of a given length
        :param length: The number of characters in the output string
        :return: A unique string of random characters
        """
        occupied = set()
        while True:
            generated = self.__random_chars(length)
            while generated in occupied:
                generated = self.__random_chars(length)
            occupied.add(generated)
            yield generated
