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

from collections import namedtuple

import bitstring as bs


def reverse(bits, *args, **kwargs):
    """
    Reverses a given bitstring
    :param bits: A bitstring
    """
    bits.reverse()


def inverse(bits, *args, **kwargs):
    """
    Inverts a given bitstring
    :param bits: A bitstring
    """
    bits.invert()


def rotate_left(bits, *args, opposite=False, **kwargs):
    """
    Rotates a given bitstring a given number of places to the left
    :param bits: A bitstring
    :param args: A tuple starting with the number of places to rotate the given bits
    :param opposite: Whether the inverse of the operation should be performed
    """
    spaces = args[0]
    rotate(bits, spaces, not opposite)


def rotate_right(bits, *args, opposite=False, **kwargs):
    """
    Rotates a given bitstring a given number of places to the right
    :param bits: A bitstring
    :param args: A tuple starting with the number of places to rotate the given bits
    :param opposite: Whether the inverse of the operation should be performed
    """
    spaces = args[0]
    rotate(bits, spaces, opposite)


def rotate(bits, spaces, is_right=True):
    """
    Rotates a given bitstring by a given number of places
    :param bits: A bitstring
    :param spaces: The number of places to rotate the given bits by
    :param is_right: Whether the bits are to be rotated to the right
    """
    if is_right:
        bits.ror(spaces)
    else:
        bits.rol(spaces)


def add(bits, *args, opposite=False, **kwargs):
    """
    Performs wrap-around addition on a given bitstring
    :param bits: A bitstring
    :param args: A tuple starting with the operand to be added to the bits
    :param opposite: Whether the inverse of the operation should be performed
    """
    operand = args[0]
    wrap_around_addition(bits, operand, opposite)


def sub(bits, *args, opposite=False, **kwargs):
    """
    Performs wrap-around subtraction on a given bitstring
    :param bits: A bitstring
    :param args: A tuple starting with the operand to be subtracted from the bits
    :param opposite: Whether the inverse of the operation should be performed
    """
    operand = args[0]
    wrap_around_addition(bits, operand, not opposite)


def wrap_around_addition(bits, operand, negative=False):
    """
    Performs wrap-around addition on a given bitstring
    :param bits: A bitstring
    :param operand: The amount to be added to the bits
    :param negative: Whether the operand should be inverted
    """
    if negative:
        operand *= -1
    length = len(bits)
    maximum = 2 ** length
    result = bits.uint + operand
    if result < 0 or result >= maximum:
        result %= maximum
    overwrite = bs.Bits(uint=result, length=length)
    bits.overwrite(overwrite, 0)


Operation = namedtuple("Operation", "function args")

OPERATIONS = {
    "v": Operation(reverse, 0),
    "x": Operation(inverse, 0),
    "a": Operation(add, 1),
    "s": Operation(sub, 1),
    "l": Operation(rotate_left, 1),
    "r": Operation(rotate_right, 1),
}
