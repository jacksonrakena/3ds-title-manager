import tkinter
from enum import Enum

CI_VERSION = '3.0'


def disable_children(parent: tkinter.Frame):
    for child in parent.winfo_children():
        wtype = child.winfo_class()
        if wtype not in ('Frame', 'Labelframe', 'TFrame', 'TLabelframe'):
            child.configure(state='disable')
        else:
            disable_children(child)


def enable_children(parent: tkinter.Frame):
    for child in parent.winfo_children():
        wtype = child.winfo_class()
        print(wtype)
        if wtype not in ('Frame', 'Labelframe', 'TFrame', 'TLabelframe'):
            child.configure(state='normal')
        else:
            enable_children(child)


class InstallStatus(Enum):
    Waiting = 0
    Starting = 1
    Writing = 2
    Finishing = 3
    Done = 4
    Failed = 5
