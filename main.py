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

from src.config import Configuration
from gui.windows import RootWindow
from src.cyberus import Cyberus

CONF_PATH = "conf"
METACONF_PATH = "metaconf"


def main(conf, metaconf):
    response = run_gui(conf, metaconf)
    if response:
        run_cyberus(conf, metaconf)


def run_gui(conf, metaconf):
    window = RootWindow(metaconf, conf)
    return window.await_response()


def run_cyberus(conf, metaconf):
    Configuration(conf, metaconf)
    root = Cyberus()
    root.start()


if __name__ == "__main__":
    main(CONF_PATH, METACONF_PATH)
