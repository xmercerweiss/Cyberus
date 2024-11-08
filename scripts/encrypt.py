"""
The MIT License

Cyberus:   Copyright (c) 2023 Xavier Mercerweiss
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

import logging

from encryptor.jigwise.operations import OPERATIONS
from encryptor.jigwise.encryptor import Encryptor


TO_BE_ENCRYPTED = [
    "<placeholder path>"  # Files and directories to be encrypted.
]

ENCRYPTED_CONTENT_PATH = "<placeholder path>"  # Destination file for encrypted data

SECURE_PATH = "<placeholder path>"  # Directory for keys, table, and config file

KEY_COUNT = 3  # Number of keys to be generated
KEY_LENGTH = 256  # Number of operations in each key


logger = logging.getLogger("devil")
logger.warning("!!! ENCRYPTING FILES !!!")

e = Encryptor(OPERATIONS, packet_size=128)
e.encrypt(
    *TO_BE_ENCRYPTED,
    content_destination=ENCRYPTED_CONTENT_PATH,
    misc_destination=SECURE_PATH,
    key_count=KEY_COUNT,
    key_length=KEY_LENGTH
)
