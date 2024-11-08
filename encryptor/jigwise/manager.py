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

import os
import ctypes
import shutil
import multiprocessing as mp
from collections import deque
from itertools import accumulate

import bitstring as bs


class AccessManager:
    """
    Allows classes to easily import and export data
    """

    @staticmethod
    def import_data(path_in, cls):
        """
        Retrieves the data from a given file, then converts it into the specified format
        :param path_in: The path of the file to retrieve data from
        :param cls: The class to which the data is to be converted
        :return: The formatted data
        """
        if path_in is None:
            return cls()
        else:
            with open(path_in, "rb") as imported:
                content = imported.read()
                if cls == bytes:
                    return content
                return cls(content)

    @staticmethod
    def export_data(path_out, content, is_bits=False):
        """
        Saves a bytes or bitstring object to a given file
        :param path_out: The file to which the data is to be saved
        :param content: The bytes or bitstring data
        :param is_bits: Whether the data is a bitstring object
        """
        if path_out is not None:
            with open(path_out, "wb") as exported:
                if is_bits:
                    content.tofile(exported)
                else:
                    exported.write(content)


class FileManager:
    """
    Allows files to be converted into bitstrings, and vice-versa
    """

    ENCODING = "utf-8"
    NAME_BITS = 16
    CONTENT_BITS = 64

    OMITTED = (
        os.path.expanduser("~/Desktop"),
        os.path.expanduser("~/Documents"),
        os.path.expanduser("~/Downloads"),
        os.path.expanduser("~/Music"),
        os.path.expanduser("~/Pictures"),
        os.path.expanduser("~/Public"),
        os.path.expanduser("~/Templates"),
        os.path.expanduser("~/Videos"),
        os.path.expanduser("~"),
        "/usr/bin",
        "/usr/man",
        "/usr/lib",
        "/usr/local",
        "/usr/share",
        "/var/log",
        "/var/lock",
        "/var/tmp",
        "/usr",
        "/var",
        "/bin",
        "/dev",
        "/etc",
        "/home",
        "/lib",
        "/sbin",
        "/tmp",
        "/",
    )

    ### Bits to Files ###

    @classmethod
    def disassemble(cls, bits, location=""):
        """
        Coverts an assembled bitstring back into the files it represents, then exports the files
        :param bits: An assembled bitstring
        :param location: (Optional) A directory within which the disassembled content is to be stored
        """
        stream = bs.BitStream(bits)
        length = len(stream)
        location = location + "/" if not location.endswith("/") else location
        while stream.pos < length:
            name_length = stream.read(f"uint{cls.NAME_BITS}")
            name = stream.read(f"bytes{name_length // 8}").decode(cls.ENCODING)
            content_length = stream.read(f"uint{cls.CONTENT_BITS}")
            content = stream.read(f"bytes{content_length}")
            path = location + name
            cls.create_file(path, content)

    @staticmethod
    def create_file(path, content=None):
        """
        Recreates the file structure in the given path, then saves the content (if given) to the file of said path
        :param path: The path to be reconstructed
        :param content: (Optional) The data to be saved to the file of the given path
        """
        split = path.split(os.sep)[:-1]
        if os.sep == "/":
            split.insert(0, "/")
        for directory in (d for d in accumulate(split, os.path.join) if d != ""):
            if not os.path.exists(directory):
                os.mkdir(directory)
        if content is not None:
            with open(path, "wb") as file:
                file.write(content)

    ### Files to Bits ###

    @classmethod
    def assemble(cls, *paths):
        """
        Converts a series of files and directories into a bitstring which may be used to reconstruct them
        :param paths: The paths or directories to be converted into a bitstring
        :return: The assembled bitstring
        """
        stream = bs.BitStream()
        flat = cls.flatten_directories(paths)
        for path in flat:
            stream.append(cls.get_bit_representation(path))
        return stream

    @staticmethod
    def flatten_directories(paths):
        """
        Retrieves all leaf nodes from a given series of paths
        :param paths: The directories to be flattened
        :return: All leaf nodes within the given paths
        """
        lost = deque(paths)
        found = set()
        while lost:
            path = lost.popleft()
            if os.path.isdir(path):
                lost.extend(f"{path}{os.sep}{file}" for file in os.listdir(path))
            else:
                found.add(path)
        return found

    @classmethod
    def get_bit_representation(cls, path):
        """
        Converts a file into its bitstring representation within an assembled bitstring
        :param path: The path of the file to be converted
        :return: The bitstring representation of the given file
        """
        pruned = cls.prune_path(path)
        name = bs.Bits(bytes(pruned, cls.ENCODING))
        with open(path, "rb") as file:
            content = bs.Bits(file.read())
        name_length = bs.Bits(uint=len(name), length=cls.NAME_BITS)
        content_length = bs.Bits(uint=len(content) // 8, length=cls.CONTENT_BITS)
        return name_length + name + content_length + content

    @classmethod
    def prune_path(cls, path):
        """
        Removes system and user level directories from a given path.
        :param path: The path to be pruned
        :return: The pruned path
        """
        for omitted in cls.OMITTED:
            if path.startswith(omitted):
                return path.replace(omitted, "")
        return path

    ### Misc ###

    @staticmethod
    def delete(*paths):
        """
        Deletes all given files and directories
        :param paths: The paths of files and directories to be deleted
        """
        for path in paths:
            try:
                os.remove(path)
            except IsADirectoryError:
                shutil.rmtree(path, True)


class PacketManager:
    """
    Allows the performance of bitstring operations to be split among any given number of Python processes
    """

    def __init__(self, content, packet_size, subdivision_count):
        """
        Splits the given bitstring into subdivisions and packets which may be operated on
        :param content: The bitstring to be operated on
        :param packet_size: The size of each packet in bytes
        :param subdivision_count: The number of Python processes to be created as the content is operated on
        """
        self.__content = content if isinstance(content, bs.BitStream) else bs.BitStream(content)
        self.__bits = len(content)
        self.__bytes = self.__bits // 8

        self.__subdivision_size = self.__bytes // subdivision_count
        self.__subdivision_count = subdivision_count
        self.__subdivisions = self.__subdivide_bits()

        self.__packet_size = packet_size
        self.__packet_count, self.__packets_per_subdivision = self.__count_packets()

    def __len__(self):
        """
        :return: The length of the content in bits
        """
        return len(self.__content)

    def instruct(self, instructions, is_opposite=False):
        """
        Creates one new process for each content subdivision, then performs the given operations on each subdivision
        :param instructions: The instructions to be performed
        :param is_opposite: Whether the inverse of each operation is to be performed
        """
        subdivision_size = self.__subdivision_size
        packets_per_subdivision = self.__packets_per_subdivision
        output = mp.Array(ctypes.c_uint, self.__bytes)
        processes = []
        for i, subdivision in enumerate(self.__subdivisions):
            byte_index = i * subdivision_size
            packet_index = i * packets_per_subdivision
            process = mp.Process(
                target=self.__instruct_packets,
                args=(subdivision, instructions, is_opposite, byte_index, packet_index, output)
            )
            process.start()
            processes.append(process)
        for process in processes:
            process.join()
        self.__content = bs.BitStream(bytes(output))
        self.__subdivisions = self.__subdivide_bits()

    def __subdivide_bits(self):
        """
        Divides the PacketManager's content into a number of subdivisions which may be operated on
        :return: A tuple containing each subdivision as a bitstring
        """
        bits = self.__content
        length = self.__bits
        size = self.__subdivision_size * 8
        output = []
        read_format = f"bits{size}"
        bits.pos = 0
        while length - bits.pos >= size:
            output.append(bits.read(read_format))
        output[-1].append(bits[bits.pos:])
        return tuple(output)

    def __count_packets(self):
        """
        Determines the number of packets each subdivision may be split into
        :return: The number of total packets, the number of packets per subdivision
        """
        packet_size = self.__packet_size
        subdivisions = self.__subdivisions
        subdivision_size = self.__subdivision_size
        if packet_size > subdivision_size:
            return len(subdivisions), 1
        else:
            packets = (subdivision_size // packet_size) + int(subdivision_size % packet_size != 0)
            total = packets * len(subdivisions)
            spare = subdivisions[-1][subdivision_size*8:]
            spare_size = len(spare) // 8
            total += (spare_size // packet_size) + int(spare_size % packet_size != 0)
            return total, packets

    def __instruct_packets(self, bits, instructions, is_opposite, byte_index, packet_index, output):
        """
        Performs the given instructions on each packet within the given subdivision
        :param bits: The subdivision bitstring to be operated on
        :param instructions: The operations to be performed
        :param is_opposite: Whether the inverse of each operation is to be performed
        :param byte_index: The index of the first byte of the subdivision within the entirety of the content
        :param packet_index: The index of the first packet of the subdivision within the entirety of the content
        :param output: A byte array which exists in shared memory to which the output may be saved
        """
        for packet in self.__get_packets(bits):
            for instruction in instructions:
                operation, start, stop, args = instruction
                if start <= packet_index < stop:
                    operation.function(packet, *args, opposite=is_opposite)
            length = len(packet)
            packet.pos = 0
            while packet.pos < length:
                i = packet.read("uint8")
                output[byte_index] = i
                byte_index += 1
            packet_index += 1

    def __get_packets(self, bits):
        """
        Yields each packet from the given subdivision
        :param bits: A subdivision bitstring
        """
        packet_bits = self.__packet_size * 8
        length = len(bits)
        read_format = "bits" + str(packet_bits)
        while length - bits.pos >= (packet_bits*2):
            yield bits.read(read_format)
        yield bits[bits.pos:]

    @property
    def content(self):
        """
        The current content as a bitstring
        """
        return self.__content

    @property
    def packet_count(self):
        """
        The number of packets the content has been split into
        """
        return self.__packet_count
