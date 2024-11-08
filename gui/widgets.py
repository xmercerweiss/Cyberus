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

from tkinter import filedialog
import tkinter as tk

from gui.errors import *


class EmptyWidget:

    def __init__(self, parent, *args, rows, columns, fg=None, font=None, **kwargs):
        self._parent = parent
        self._rows = rows
        self._columns = columns
        self._background = kwargs.setdefault("bg", None)
        self._foreground = fg
        self._font = font
        self._frame = self._initialize_frame(*args, **kwargs)

    def _initialize_frame(self, *args, **kwargs):
        frame = tk.Frame(self._parent, *args, **kwargs)
        for r in range(self._rows):
            frame.rowconfigure(r, weight=1)
        for c in range(self._columns):
            frame.columnconfigure(c, weight=1)
        return frame

    def grid(self, *args, **kwargs):
        self._frame.grid(*args, **kwargs)

    def pack(self, *args, **kwargs):
        self._frame.pack(*args, **kwargs)

    def clear(self):
        msg = f"Attempted to call abstract method 'clear' from {repr(type(self).__name__)}"
        raise AbstractMethodCallException(msg)


class LabeledWidget(EmptyWidget):

    def __init__(self, parent, *args, title, rows, columns, **kwargs):
        super().__init__(
            parent,
            *args,
            rows=rows,
            columns=columns,
            **kwargs
        )
        self._title = title
        self._label = self._initialize_label()

    def _initialize_label(self):
        label = tk.Label(
            self._frame,
            text=self._title,
            bg=self._background,
            fg=self._foreground,
            font=self._font
        )
        label.grid(
            row=0,
            column=0,
            sticky="NSEW"
        )
        return label

    @property
    def title(self):
        return self._title

    @property
    def value(self):
        return None


class LabeledEntry(LabeledWidget):

    def __init__(self, parent, *args, title, **kwargs):
        super().__init__(
            parent,
            *args,
            title=title,
            rows=1,
            columns=2,
            **kwargs
        )
        self._entry = self._initialize_entry()

    def _initialize_entry(self):
        entry = tk.Entry(
            self._frame,
            bg=self._foreground
        )
        entry.grid(
            row=0,
            column=1,
            sticky="NSEW"
        )
        return entry

    def clear(self):
        length = len(self._entry.get())
        self._entry.delete(0, length)

    @property
    def value(self):
        return self._entry.get()


class LabeledFileEntry(LabeledEntry):

    def __init__(self, parent, *args, title, **kwargs):
        super().__init__(
            parent,
            *args,
            title=title,
            **kwargs
        )
        self._frame.columnconfigure(2, weight=1)
        self._button = self._initialize_button()

    def _initialize_button(self):
        button = tk.Button(
            self._frame,
            text="...",
            bg=self._foreground,
            fg=self._background,
            command=self._prompt_file
        )
        button.grid(
            row=0,
            column=2,
            sticky="NSEW"
        )
        return button

    def _prompt_file(self):
        filename = filedialog.askopenfilename(
            initialdir="/",
            title=f"Select a {self._title}",
            filetypes=(("all files", "*"),)
        )
        self.clear()
        self._entry.insert(0, filename)


class LabeledCheckbox(LabeledWidget):

    def __init__(self, parent, *args, title, **kwargs):
        super().__init__(
            parent,
            *args,
            title=title,
            rows=1,
            columns=2,
            **kwargs
        )
        self._checkbox = self._initialize_checkbox()
        self._is_selected = False
        self._checkbox.deselect()

    def _initialize_checkbox(self):
        checkbox = tk.Checkbutton(
            self._frame,
            bg=self._background,
            fg=self._foreground,
            activebackground=self._background,
            activeforeground=self._foreground,
            command=self._toggle
        )
        checkbox.grid(
            row=0,
            column=1,
            sticky="NSEW"
        )
        return checkbox

    def _toggle(self):
        self._is_selected = not self._is_selected

    def clear(self):
        self._is_selected = False
        self._checkbox.deselect()

    def select(self):
        self._checkbox.select()

    def deselect(self):
        self._checkbox.deselect()

    @property
    def value(self):
        return str(self._is_selected).lower()


class CheckerWidget(EmptyWidget):

    def __init__(self, parent, *args, title, **kwargs):
        super().__init__(
            parent,
            *args,
            rows=2,
            columns=1,
            **kwargs
        )
        self._title = title
        self._args_entry, self._weight_entry = self._initialize_entries()

    def _initialize_entries(self):
        args_entry = LabeledEntry(
            self._frame,
            title=self._title,
            bg=self._background,
            fg=self._foreground,
            font=self._font,
        )
        args_entry.grid(
            row=0,
            column=0,
            sticky="EW"
        )

        weight_entry = LabeledEntry(
            self._frame,
            title="Weight",
            bg=self._background,
            fg=self._foreground,
            font=self._font,
        )
        weight_entry.grid(
            row=1,
            column=0,
            sticky="EW"
        )

        return args_entry, weight_entry

    def clear(self):
        self._frame.destroy()

    def as_dict(self):
        weight = self._weight_entry.value
        return {
            self._title: self._args_entry.value,
            f"{self._title} weight": weight if weight != "" else "1"
        }
