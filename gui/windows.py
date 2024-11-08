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

import pyautogui as pygui

from src.operations import DETECTION_OPERATIONS
from gui.panels import *


class RootWindow:

    TITLE = "Cyberus"
    SIZE = "1380x860"
    RESIZE = True

    STATIC_BACKGROUND = "#363c3d"
    STATIC_FOREGROUND = "#828485"

    DYNAMIC_BACKGROUND = "#828485"
    DYNAMIC_FOREGROUND = "#1c1d21"

    FONT = ("Courier New", "12", "bold")

    VALUES = [
        "Delay",
        "Threshold",
        "Log Message Format",
        "Log Time Format"
    ]

    FILES = [
        "Root Log",
        "Checker Log",
        "Executor Log",
        "Contingency Scripts",
        "Close after Contingency"
    ]

    BUILD_BUTTON_NAME = "Build"
    RUN_BUTTON_NAME = "Build + Run"
    CLEAR_BUTTON_NAME = "Clear"
    ADD_BUTTON_NAME = "Add Routine"

    @staticmethod
    def read_format_file(path):
        output = {}
        with open(path, "r") as file:
            for line in file.readlines():
                key, value = line.strip().split(":")
                output[key.lower()] = value
        return output

    @staticmethod
    def displayable(text):
        return text.replace("_", " ").title()

    def __init__(self, conf_in, conf_out):
        self._output = conf_out
        self._formatting = self.read_format_file(conf_in)
        self._checker_names = tuple(
            self.displayable(f.__name__) for f in DETECTION_OPERATIONS
        )
        self._root = self._initialize_root()
        self._static, self._dynamic = self._initialize_frames()
        self._value_panel, self._file_panel, self._button_panel, self._checker_panel = self._initialize_panels()
        self._popup = self._initialize_popup()
        self._populate_panels()
        self._execute_after_closing = False

    @staticmethod
    def _format_key(key, space):
        return space.join(key.split()).upper()

    @staticmethod
    def _format_value(key, delimiter):
        return delimiter.join(key.split(", "))

    def _initialize_root(self):
        root = tk.Tk()
        root.title(self.TITLE)
        root.geometry(self.SIZE)
        root.resizable(self.RESIZE, self.RESIZE)
        root.rowconfigure(0, weight=1)
        root.columnconfigure(0, weight=1)
        root.columnconfigure(1, weight=1)
        return root

    def _initialize_frames(self):
        static_frame = tk.Frame(self._root)
        static_frame.rowconfigure(0, weight=3)
        static_frame.rowconfigure(1, weight=6)
        static_frame.rowconfigure(2, weight=2)
        static_frame.columnconfigure(0, weight=1)
        static_frame.grid(
            row=0,
            column=0,
            sticky="NSEW"
        )

        dynamic_frame = tk.Frame(
            self._root,
        )
        dynamic_frame.rowconfigure(0, weight=9)
        dynamic_frame.rowconfigure(1, weight=2)
        dynamic_frame.columnconfigure(0, weight=1)
        dynamic_frame.grid(
            row=0,
            column=1,
            sticky="NSEW"
        )
        return static_frame, dynamic_frame

    def _initialize_panels(self):
        value_panel = ValuePanel(
            self._static,
            rows=2,
            columns=2,
            titles=self.VALUES,
            bg=self.STATIC_BACKGROUND,
            fg=self.STATIC_FOREGROUND,
            font=self.FONT,
            relief=tk.RAISED,
            borderwidth=7
        )
        value_panel.grid(
            row=0,
            column=0,
            sticky="NSEW"
        )

        file_panel = FilePanel(
            self._static,
            titles=self.FILES,
            bg=self.STATIC_BACKGROUND,
            fg=self.STATIC_FOREGROUND,
            font=self.FONT,
        )
        file_panel.grid(
            row=1,
            column=0,
            sticky="NSEW"
        )

        button_panel = ButtonPanel(
            self._static,
            bg=self.STATIC_BACKGROUND,
            font=self.FONT,
        )
        button_panel.grid(
            row=2,
            column=0,
            sticky="NSEW"
        )

        checker_panel = CheckerPanel(
            self._dynamic,
            bg=self.DYNAMIC_BACKGROUND,
            fg=self.DYNAMIC_FOREGROUND,
            relief=tk.SUNKEN,
            borderwidth=7,
        )
        checker_panel.grid(
            row=0,
            column=0,
            sticky="NSEW",
        )

        checker_button = tk.Button(
            self._dynamic,
            text=self.ADD_BUTTON_NAME,
            command=self._display_popup,
            fg="#22612f",
            font=self.FONT,
            relief=tk.RAISED,
            borderwidth=5
        )
        checker_button.grid(
            row=1,
            column=0,
            sticky="NSEW",
        )

        return value_panel, file_panel, button_panel, checker_panel

    def _initialize_popup(self):
        popup = tk.Menu(
            self._root,
            tearoff=0
        )
        for name in self._checker_names:
            popup.add_command(
                label=name,
                command=self._create_checker_widget(name)
            )
        return popup

    def _populate_panels(self):
        self._button_panel.add_button(
            self.BUILD_BUTTON_NAME,
            self._build,
            bg=self.STATIC_FOREGROUND,
            fg=self.STATIC_BACKGROUND,
            font=self.FONT,
            relief=tk.RAISED,
            borderwidth=4
        )
        self._button_panel.add_button(
            self.RUN_BUTTON_NAME,
            self._run,
            bg="#22612f",
            fg="#dedede",
            font=self.FONT,
            relief=tk.RAISED,
            borderwidth=4
        )
        self._button_panel.add_button(
            self.CLEAR_BUTTON_NAME,
            self._clear,
            bg="#942929",
            fg="#dedede",
            font=self.FONT,
            relief=tk.RAISED,
            borderwidth=4
        )

    def _display_popup(self):
        try:
            self._popup.tk_popup(*pygui.position())
        finally:
            self._popup.grab_release()

    def _create_checker_widget(self, name):
        def create():
            self._checker_panel.add_checker(
                name,
                font=self.FONT,
                relief=tk.GROOVE,
                borderwidth=3
            )
        return create

    def _build(self):
        assignment = self._formatting["assignment_delimiter"]
        delimiter = self._formatting["value_delimiter"]
        space = self._formatting["word_delimiter"]
        values = self._read_all_panels()
        with open(self._output, "w") as output:
            for key, value in values.items():
                formatted_key = self._format_key(key, space)
                formatted_value = self._format_value(value, delimiter)
                output.write(f"{formatted_key}{assignment}{formatted_value}\n")

    def _run(self):
        self._build()
        self._execute_after_closing = True
        self._root.destroy()

    def _clear(self):
        self._value_panel.clear()
        self._file_panel.clear()
        self._checker_panel.clear()

    def _read_all_panels(self):
        values = {}
        values.update(self._value_panel.as_dict())
        values.update(self._file_panel.as_dict())
        values.update(self._checker_panel.as_dict())
        return values

    def await_response(self):
        try:
            self._root.mainloop()
        finally:
            return self._execute_after_closing
