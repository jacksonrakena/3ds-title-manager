import tkinter as tk

from ui.gui import TitleManagerWindow
from utils import CI_VERSION

if __name__ == '__main__':
    window = tk.Tk()
    window.title(f'Jackson\'s 3DS Title Manager {CI_VERSION}')
    frame = TitleManagerWindow(window)
    frame.pack(fill=tk.BOTH, expand=True)
    window.mainloop()
