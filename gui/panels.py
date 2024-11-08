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

from gui.widgets import *


class Panel:

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


class ScrollablePanel:

    def __init__(self, parent, *args, width, height, fg=None, font=None, **kwargs):
        self._parent = parent
        self._width = width
        self._height = height
        self._background = kwargs.setdefault("bg", None)
        self._foreground = fg
        self._font = font
        self._frame = self._initialize_frame(*args, **kwargs)
        self._scrollbar = self._initialize_scrollbar()
        self._canvas = self._initialize_canvas()
        self._scrollbar.config(command=self._canvas.yview)

    def _initialize_frame(self, *args, **kwargs):
        frame = tk.Frame(self._parent, *args, **kwargs)
        frame.pack_propagate(False)
        return frame

    def _initialize_scrollbar(self):
        scrollbar = tk.Scrollbar(
            self._frame,
            orient="vertical"
        )
        scrollbar.pack(
            side="right",
            fill="y"
        )
        return scrollbar

    def _initialize_canvas(self):
        canvas = tk.Canvas(
            self._frame,
            bg=self._background,
            width=self._width,
            height=self._height,
            yscrollcommand=self._scrollbar.set,
        )
        canvas.pack(
           fill="x"
        )
        return canvas

    def grid(self, *args, **kwargs):
        self._frame.grid(*args, **kwargs)


class ValuePanel(Panel):

    def __init__(self, parent, *args, rows, columns, titles, **kwargs):
        super().__init__(
            parent,
            *args,
            rows=rows,
            columns=columns,
            **kwargs
        )
        self._entries = self._initialize_entries(titles)

    def _initialize_entries(self, titles):
        row = column = 0
        entries = []
        for title in titles:
            entry = LabeledEntry(
                self._frame,
                title=title,
                bg=self._background,
                fg=self._foreground,
                font=self._font
            )
            entry.grid(
                row=row,
                column=column,
            )
            row += 1
            if row >= self._rows:
                row = 0
                column += 1
            entries.append(entry)
        return entries

    def as_dict(self):
        return {entry.title: entry.value for entry in self._entries}

    def clear(self):
        for entry in self._entries:
            entry.clear()


class FilePanel(Panel):

    def __init__(self, parent, *args, titles, fg=None, font=None, **kwargs):
        super().__init__(
            parent,
            *args,
            rows=len(titles) + 1,
            columns=1,
            fg=fg,
            font=font,
            **kwargs
        )
        self._entries = self._initialize_entries(titles[:-1])
        self._checkbox = self._initialize_checkbox(titles[-1])

    def _initialize_entries(self, titles):
        row = 0
        entries = []
        for title in titles:
            entry = LabeledFileEntry(
                self._frame,
                title=title,
                bg=self._background,
                fg=self._foreground,
                font=self._font
            )
            entry.grid(
                row=row,
                column=0,
                sticky="EW"
            )
            row += 1
            entries.append(entry)
        return entries

    def _initialize_checkbox(self, title):
        checkbox = LabeledCheckbox(
            self._frame,
            title=title,
            bg=self._background,
            fg=self._foreground,
            font=self._font
        )
        checkbox.grid(
            row=self._rows - 1,
            column=0
        )
        checkbox.deselect()
        return checkbox

    def as_dict(self):
        values = {
            entry.title: entry.value
            for entry in self._entries
        }
        values[self._checkbox.title] = self._checkbox.value
        return values

    def clear(self):
        for entry in self._entries:
            entry.clear()
        self._checkbox.clear()


class ButtonPanel(Panel):

    def __init__(self, parent, *args, fg=None, font=None, **kwargs):
        super().__init__(
            parent,
            *args,
            rows=1,
            columns=0,
            fg=fg,
            font=font,
            **kwargs
        )
        self._buttons = []

    def add_button(self, title, command, **kwargs):
        button = tk.Button(
            self._frame,
            text=title,
            command=command,
            **kwargs
        )
        self._buttons.append(button)
        column = len(self._buttons)
        self._frame.columnconfigure(column, weight=1)
        button.grid(
            row=0,
            column=column,
            sticky="NSEW"
        )


class CheckerPanel(ScrollablePanel):

    def __init__(self, parent, *args, fg=None, font=None, **kwargs):
        super().__init__(
            parent,
            *args,
            width=200,
            height=800,
            fg=fg,
            font=font,
            **kwargs
        )
        self._checkers = []

    def add_checker(self, title, **kwargs):
        checker = CheckerWidget(
            self._canvas,
            title=title,
            **kwargs
        )
        self._checkers.append(checker)
        checker.pack(
            side=tk.TOP,
            fill=tk.X
        )

    def clear(self):
        for checker in self._checkers:
            checker.clear()

    def as_dict(self):
        output = {}
        for checker in self._checkers:
            output.update(checker.as_dict())
        return output
