import tkinter as tk
import tkinter.ttk as ttk
from typing import Dict, List

from ui.utils import simple_listbox_frame


class InstallResults(tk.Toplevel):
    def __init__(self, parent: tk.Tk = None, *, install_state: 'Dict[str, List[str]]', copied_3dsx: bool,
                 application_count: int):
        super().__init__(parent)
        self.parent = parent

        self.wm_withdraw()
        self.wm_transient(self.parent)
        self.grab_set()
        self.wm_title('Install results')

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        outer_container = ttk.Frame(self)
        outer_container.grid(sticky=tk.NSEW)
        outer_container.rowconfigure(0, weight=0)
        outer_container.columnconfigure(0, weight=1)

        if install_state['failed'] and install_state['installed']:
            # some failed and some worked
            message = ('Some titles were installed, some failed. Please check the output for more details.\n'
                       'The ones that were installed can be finished with custom-install-finalize.')
        elif install_state['failed'] and not install_state['installed']:
            # all failed
            message = 'All titles failed to install. Please check the output for more details.'
        elif install_state['installed'] and not install_state['failed']:
            # all worked
            message = 'All titles were installed.'
        else:
            message = 'Nothing was installed.'

        if install_state['installed'] and copied_3dsx:
            message += '\n\ncustom-install-finalize has been copied to the SD card.'

        if application_count >= 300:
            message += (f'\n\nWarning: {application_count} installed applications were detected.\n'
                        f'The HOME Menu will only show 300 icons.\n'
                        f'Some applications (not updates or DLC) will need to be deleted.')

        message_label = ttk.Label(outer_container, text=message)
        message_label.grid(row=0, column=0, sticky=tk.NSEW, padx=10, pady=10)

        if install_state['installed']:
            outer_container.rowconfigure(1, weight=1)
            frame = simple_listbox_frame(
                outer_container, 'Installed', install_state['installed'])
            frame.grid(row=1, column=0, sticky=tk.NSEW, padx=10, pady=(0, 10))

        if install_state['failed']:
            outer_container.rowconfigure(2, weight=1)
            frame = simple_listbox_frame(
                outer_container, 'Failed', install_state['failed'])
            frame.grid(row=2, column=0, sticky=tk.NSEW, padx=10, pady=(0, 10))

        ok_frame = ttk.Frame(outer_container)
        ok_frame.grid(row=3, column=0, sticky=tk.NSEW, padx=10, pady=(0, 10))
        ok_frame.rowconfigure(0, weight=1)
        ok_frame.columnconfigure(0, weight=1)

        ok_button = ttk.Button(ok_frame, text='OK', command=self.destroy)
        ok_button.grid(row=0, column=0)

        self.wm_deiconify()
