import tkinter as tk
import tkinter.ttk as ttk
from typing import List


class ConsoleFrame(ttk.Frame):
    def __init__(self, parent: tk.BaseWidget = None, starting_lines: 'List[str]' = None):
        super().__init__(parent)
        self.parent = parent

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL)
        scrollbar.grid(row=0, column=1, sticky=tk.NSEW)

        self.text = tk.Text(self, highlightthickness=0,
                            wrap='word', yscrollcommand=scrollbar.set)
        self.text.grid(row=0, column=0, sticky=tk.NSEW)

        scrollbar.config(command=self.text.yview)

        if starting_lines:
            for l in starting_lines:
                self.text.insert(tk.END, l + '\n')

        self.text.see(tk.END)
        self.text.configure(state=tk.DISABLED)

    def log(self, *message, end='\n', sep=' '):
        self.text.configure(state=tk.NORMAL)
        self.text.insert(tk.END, sep.join(message) + end)
        self.text.see(tk.END)
        self.text.configure(state=tk.DISABLED)
