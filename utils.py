import tkinter


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
