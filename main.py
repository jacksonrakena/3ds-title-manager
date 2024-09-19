import tkinter as tk

from ui.gui import CustomInstallGUI
from utils import CI_VERSION

if __name__ == '__main__':
    window = tk.Tk()
    window.title(f'Jackson\'s 3DS Title Manager {CI_VERSION}')
    frame = CustomInstallGUI(window)
    frame.pack(fill=tk.BOTH, expand=True)
    window.mainloop()
