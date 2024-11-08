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

import secrets

import bitstring as bs

from encryptor.jigwise.manager import AccessManager


class Table(AccessManager):
    """
    Maps a series of bitstrings to a series of operations, and vice-versa
    """

    HEADER_SIZE = 8

    def __init__(self, operations, source=None, symbol_length=6):
        """
        Loads a table from a file if a source is given, otherwise generates a table randomly
        :param operations: A dict containing the operations to be mapped
        :param source: (Optional) The source file to load a table from
        :param symbol_length: The length of each mapped bitstring in bits
        """
        self.__operations = operations
        if source is None:
            self.__symbol_length = symbol_length
            self.__symb_to_op = self.__generate_mappings()
        else:
            imported = self.import_data(source, bs.Bits)
            self.__symbol_length = imported[:self.HEADER_SIZE].uint
            self.__symb_to_op = self.__read_mappings(imported)
        self.__op_to_symb = {v: k for k, v in self.__symb_to_op.items()}

    def __getitem__(self, item):
        """
        Returns the operation mapped to a given symbol, and vice-versa
        :param item: The operation or symbol mapped to the output content
        :return: The operation or symbol mapped to the input content
        """
        if item in self.__symb_to_op:
            return self.__symb_to_op[item]
        elif item in self.__op_to_symb:
            return self.__op_to_symb[item]
        else:
            msg = f"Invalid key passed to {type(self).__name__}"
            raise KeyError(msg)

    def __len__(self):
        """
        The number of mappings present within the table
        """
        return len(self.__operations)

    def __generate_mappings(self):
        """
        Maps the table's operations to a series of randomly generated bitstrings
        :return: The generated mappings as a dict
        """
        mappings = {}
        occupied = set()
        for operation in self.__operations.values():
            num = secrets.randbits(self.__symbol_length)
            while num in occupied:
                num = secrets.randbits(self.__symbol_length)
            occupied.add(num)
            symbol = bs.Bits(uint=num, length=self.__symbol_length)
            mappings[symbol] = operation
        return mappings

    def __read_mappings(self, imported):
        """
        Reads the mappings present within a given source file
        :param imported: The source file to be read from
        :return: The read mappings as a dict
        """
        mappings = {}
        length = len(imported)
        head = self.HEADER_SIZE
        while head < length:
            tail = head + 8
            symbol = imported[head:head+self.__symbol_length]
            code = str(imported[tail:tail+8].bytes, "ascii")
            if code not in self.__operations:
                msg = f"Incompatible '.table' file passed to {repr(type(self).__name__)} object"
                raise ValueError(msg)
            else:
                mappings[symbol] = self.__operations[code]
                head += 16
        return mappings

    def reset_mappings(self):
        """
        Overwrites the mappings present within the table with randomly generated ones
        """
        self.__symb_to_op = self.__generate_mappings()
        self.__op_to_symb = {v: k for k, v in self.__symb_to_op.items()}

    def export(self, destination):
        """
        Generates a table source file which may be read to retrieve the mappings currently present within the table
        :param destination:
        :return:
        """
        header = bs.Bits(uint=self.__symbol_length, length=self.HEADER_SIZE)
        with open(destination, "wb") as file:
            file.write(header.tobytes())
            for symbol, code in zip(self.__symb_to_op, self.__operations):
                file.write(symbol.tobytes())
                file.write(bytes(code, "ascii"))

    @property
    def symbols(self):
        """
        The set of bitstrings currently mapped within the table
        """
        return tuple(self.__symb_to_op.keys())

    @property
    def operations(self):
        """
        The set of operations currently mapped within the table
        """
        return tuple(self.__symb_to_op.values())

    @property
    def symbol_length(self):
        """
        The length of each bitstring symbol in bits
        """
        return self.__symbol_length
