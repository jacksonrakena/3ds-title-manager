import tkinter as tk
import tkinter.ttk as ttk
from os.path import isfile
from typing import List

from utils import InstallStatus


def clamp(n, smallest, largest):
    return max(smallest, min(n, largest))


def simple_listbox_frame(parent, title: 'str', items: 'List[str]'):
    frame = ttk.LabelFrame(parent, text=title)
    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)

    scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL)
    scrollbar.grid(row=0, column=1, sticky=tk.NSEW)

    box = tk.Listbox(frame, highlightthickness=0,
                     yscrollcommand=scrollbar.set, selectmode=tk.EXTENDED)
    box.grid(row=0, column=0, sticky=tk.NSEW)
    scrollbar.config(command=box.yview)

    box.insert(tk.END, *items)

    box.config(height=clamp(len(items), 3, 10))

    return frame


statuses = {
    InstallStatus.Waiting: 'Waiting',
    InstallStatus.Starting: 'Starting',
    InstallStatus.Writing: 'Writing',
    InstallStatus.Finishing: 'Finishing',
    InstallStatus.Done: 'Done',
    InstallStatus.Failed: 'Failed',
}


def find_first_file(paths):
    for p in paths:
        if isfile(p):
            return p
