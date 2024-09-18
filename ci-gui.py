#!/usr/bin/env python3

# This file is a part of custom-install.py.
#
# custom-install is copyright (c) 2019-2020 Ian Burgwin
# This file is licensed under The MIT License (MIT).
# You can find the full license text in LICENSE.md in the root of this project.

import sys
import tkinter as tk
import tkinter.filedialog as fd
import tkinter.messagebox as mb
import tkinter.ttk as ttk
from os import environ, scandir
from os.path import abspath, basename, dirname, isfile, join
from threading import Lock, Thread
from time import strftime
from traceback import format_exception
from typing import TYPE_CHECKING

from pyctr.crypto import CryptoEngine, MissingSeedError, load_seeddb
from pyctr.crypto.engine import b9_paths
from pyctr.type.cdn import CDNError
from pyctr.type.cia import CIAError
from pyctr.type.tmd import TitleMetadataError
from pyctr.util import config_dirs

from custominstall import (CI_VERSION, CustomInstall, InstallStatus,
                           InvalidCIFinishError, load_cifinish)

if TYPE_CHECKING:
    from os import PathLike
    from typing import Dict, List, Union

frozen = getattr(sys, 'frozen', None)
is_windows = sys.platform == 'win32'
taskbar = None
if is_windows:
    if frozen:
        # attempt to fix loading tcl/tk when running from a path with non-latin characters
        tkinter_path = dirname(tk.__file__)
        tcl_path = join(tkinter_path, 'tcl8.6')
        environ['TCL_LIBRARY'] = 'lib/tkinter/tcl8.6'
    try:
        import comtypes.client as cc

        tbl = cc.GetModule('TaskbarLib.tlb')

        taskbar = cc.CreateObject(
            '{56FDF344-FD6D-11D0-958A-006097C9A090}', interface=tbl.ITaskbarList3)
        taskbar.HrInit()
    except (ModuleNotFoundError, UnicodeEncodeError, AttributeError):
        pass

file_parent = dirname(abspath(__file__))

# automatically load boot9 if it's in the current directory
b9_paths.insert(0, join(file_parent, 'boot9.bin'))
b9_paths.insert(0, join(file_parent, 'boot9_prot.bin'))

seeddb_paths = [join(x, 'seeddb.bin') for x in config_dirs]
try:
    seeddb_paths.insert(0, environ['SEEDDB_PATH'])
except KeyError:
    pass
# automatically load seeddb if it's in the current directory
seeddb_paths.insert(0, join(file_parent, 'seeddb.bin'))


def clamp(n, smallest, largest):
    return max(smallest, min(n, largest))


def find_first_file(paths):
    for p in paths:
        if isfile(p):
            return p


# find boot9, seeddb, and movable.sed to auto-select in the gui
default_b9_path = find_first_file(b9_paths)
default_seeddb_path = find_first_file(seeddb_paths)
default_movable_sed_path = find_first_file([join(file_parent, 'movable.sed')])

if default_seeddb_path:
    load_seeddb(default_seeddb_path)

statuses = {
    InstallStatus.Waiting: 'Waiting',
    InstallStatus.Starting: 'Starting',
    InstallStatus.Writing: 'Writing',
    InstallStatus.Finishing: 'Finishing',
    InstallStatus.Done: 'Done',
    InstallStatus.Failed: 'Failed',
}


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


class TitleReadFailResults(tk.Toplevel):
    def __init__(self, parent: tk.Tk = None, *, failed: 'Dict[str, str]'):
        super().__init__(parent)
        self.parent = parent

        self.wm_withdraw()
        self.wm_transient(self.parent)
        self.grab_set()
        self.wm_title('Failed to add titles')

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        outer_container = ttk.Frame(self)
        outer_container.grid(sticky=tk.NSEW)
        outer_container.rowconfigure(0, weight=0)
        outer_container.rowconfigure(1, weight=1)
        outer_container.columnconfigure(0, weight=1)

        message_label = ttk.Label(
            outer_container, text="Some titles couldn't be added.")
        message_label.grid(row=0, column=0, sticky=tk.NSEW, padx=10, pady=10)

        treeview_frame = ttk.Frame(outer_container)
        treeview_frame.grid(row=1, column=0, sticky=tk.NSEW)
        treeview_frame.rowconfigure(0, weight=1)
        treeview_frame.columnconfigure(0, weight=1)

        treeview_scrollbar = ttk.Scrollbar(treeview_frame, orient=tk.VERTICAL)
        treeview_scrollbar.grid(row=0, column=1, sticky=tk.NSEW)

        treeview = ttk.Treeview(
            treeview_frame, yscrollcommand=treeview_scrollbar.set)
        treeview.grid(row=0, column=0, sticky=tk.NSEW, padx=10, pady=(0, 10))
        treeview.configure(columns=('filepath', 'reason'), show='headings')

        treeview.column('filepath', width=200, anchor=tk.W)
        treeview.heading('filepath', text='File path')
        treeview.column('reason', width=400, anchor=tk.W)
        treeview.heading('reason', text='Reason')

        treeview_scrollbar.configure(command=treeview.yview)

        for path, reason in failed.items():
            treeview.insert('', tk.END, text=path, iid=path,
                            values=(basename(path), reason))

        ok_frame = ttk.Frame(outer_container)
        ok_frame.grid(row=2, column=0, sticky=tk.NSEW, padx=10, pady=(0, 10))
        ok_frame.rowconfigure(0, weight=1)
        ok_frame.columnconfigure(0, weight=1)

        ok_button = ttk.Button(ok_frame, text='OK', command=self.destroy)
        ok_button.grid(row=0, column=0)

        self.wm_deiconify()


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


class CustomInstallGUI(ttk.Frame):
    console = None
    b9_loaded = False

    def __init__(self, parent: tk.Tk = None):
        super().__init__(parent)
        self.parent = parent

        # readers to give to CustomInstall at the install
        self.readers = {}

        self.lock = Lock()

        self.log_messages = []

        self.hwnd = None  # will be set later

        self.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=1)

        if taskbar:
            # this is so progress can be shown in the taskbar
            def setup_tab():
                self.hwnd = int(parent.wm_frame(), 16)
                taskbar.ActivateTab(self.hwnd)

            self.after(100, setup_tab)

        # ---------------------------------------------------------------- #
        # create file pickers for base files
        file_pickers = ttk.Frame(self)
        file_pickers.grid(row=0, column=0, sticky=tk.EW)
        file_pickers.columnconfigure(1, weight=1)

        self.file_picker_textboxes = {}

        def sd_callback():
            f = fd.askdirectory(parent=parent, title='Select SD root (the directory or drive that contains '
                                                     '"Nintendo 3DS")', initialdir=file_parent, mustexist=True)
            if f:
                cifinish_path = join(f, 'cifinish.bin')
                try:
                    load_cifinish(cifinish_path)
                except InvalidCIFinishError:
                    self.show_error(f'{cifinish_path} was corrupt!\n\n'
                                    f'This could mean an issue with the SD card or the filesystem. Please check it for errors.\n'
                                    f'It is also possible, though less likely, to be an issue with custom-install.\n\n'
                                    f'Stopping now to prevent possible issues. If you want to try again, delete cifinish.bin from the SD card and re-run custom-install.')
                    return

                sd_selected.delete('1.0', tk.END)
                sd_selected.insert(tk.END, f)

                for filename in ['boot9.bin', 'seeddb.bin', 'movable.sed']:
                    path = auto_input_filename(self, f, filename)
                    if filename == 'boot9.bin':
                        self.check_b9_loaded()
                        self.enable_buttons()
                    if filename == 'seeddb.bin':
                        load_seeddb(path)

        sd_type_label = ttk.Label(file_pickers, text='SD root')
        sd_type_label.grid(row=0, column=0)

        sd_selected = tk.Text(file_pickers, wrap='none', height=1)
        sd_selected.grid(row=0, column=1, sticky=tk.EW)

        sd_button = ttk.Button(file_pickers, text='...', command=sd_callback)
        sd_button.grid(row=0, column=2)

        self.file_picker_textboxes['sd'] = sd_selected

        def auto_input_filename(self, f, filename):
            sd_msed_path = find_first_file(
                [join(f, 'gm9', 'out', filename), join(f, filename)])
            if sd_msed_path:
                self.log('Found ' + filename +
                         ' on SD card at ' + sd_msed_path)
                if filename.endswith('bin'):
                    filename = filename.split('.')[0]
                box = self.file_picker_textboxes[filename]
                box.delete('1.0', tk.END)
                box.insert(tk.END, sd_msed_path)
                return sd_msed_path
        # This feels so wrong.

        def create_required_file_picker(type_name, types, default, row, callback=lambda filename: None):
            def internal_callback():
                f = fd.askopenfilename(parent=parent, title='Select ' + type_name, filetypes=types,
                                       initialdir=file_parent)
                if f:
                    selected.delete('1.0', tk.END)
                    selected.insert(tk.END, f)
                    callback(f)

            type_label = ttk.Label(file_pickers, text=type_name)
            type_label.grid(row=row, column=0)

            selected = tk.Text(file_pickers, wrap='none', height=1)
            selected.grid(row=row, column=1, sticky=tk.EW)
            if default:
                selected.insert(tk.END, default)

            button = ttk.Button(file_pickers, text='...',
                                command=internal_callback)
            button.grid(row=row, column=2)

            self.file_picker_textboxes[type_name] = selected

        def b9_callback(path: 'Union[PathLike, bytes, str]'):
            self.check_b9_loaded()
            self.enable_buttons()

        def seeddb_callback(path: 'Union[PathLike, bytes, str]'):
            load_seeddb(path)

        create_required_file_picker(
            'boot9', [('boot9 file', '*.bin')], default_b9_path, 1, b9_callback)
        create_required_file_picker(
            'seeddb', [('seeddb file', '*.bin')], default_seeddb_path, 2, seeddb_callback)
        create_required_file_picker(
            'movable.sed', [('movable.sed file', '*.sed')], default_movable_sed_path, 3)

        # ---------------------------------------------------------------- #
        # create buttons to add cias
        titlelist_buttons = ttk.Frame(self)
        titlelist_buttons.grid(row=1, column=0)

        def add_cias_callback():
            files = fd.askopenfilenames(parent=parent, title='Select CIA files', filetypes=[('CIA files', '*.cia')],
                                        initialdir=file_parent)
            results = {}
            for f in files:
                success, reason = self.add_cia(f)
                if not success:
                    results[f] = reason

            if results:
                title_read_fail_window = TitleReadFailResults(
                    self.parent, failed=results)
                title_read_fail_window.focus()
            self.sort_treeview()

        add_cias = ttk.Button(
            titlelist_buttons, text='Add CIAs', command=add_cias_callback)
        add_cias.grid(row=0, column=0)

        def add_cdn_callback():
            d = fd.askdirectory(parent=parent, title='Select folder containing title contents in CDN format',
                                initialdir=file_parent)
            if d:
                if isfile(join(d, 'tmd')):
                    success, reason = self.add_cia(d)
                    if not success:
                        self.show_error(
                            f"Couldn't add {basename(d)}: {reason}")
                    else:
                        self.sort_treeview()
                else:
                    self.show_error(
                        'tmd file not found in the CDN directory:\n' + d)

        add_cdn = ttk.Button(
            titlelist_buttons, text='Add CDN title folder', command=add_cdn_callback)
        add_cdn.grid(row=0, column=1)

        def add_dirs_callback():
            d = fd.askdirectory(
                parent=parent, title='Select folder containing CIA files', initialdir=file_parent)
            if d:
                results = {}
                for f in scandir(d):
                    if f.name.lower().endswith('.cia'):
                        success, reason = self.add_cia(f.path)
                        if not success:
                            results[f] = reason

                if results:
                    title_read_fail_window = TitleReadFailResults(
                        self.parent, failed=results)
                    title_read_fail_window.focus()
                self.sort_treeview()

        add_dirs = ttk.Button(
            titlelist_buttons, text='Add folder', command=add_dirs_callback)
        add_dirs.grid(row=0, column=2)

        def remove_selected_callback():
            for entry in self.treeview.selection():
                self.remove_cia(entry)

        remove_selected = ttk.Button(
            titlelist_buttons, text='Remove selected', command=remove_selected_callback)
        remove_selected.grid(row=0, column=3)

        search_frame = ttk.Frame(self)
        search_frame.grid(row=2, column=0, sticky=tk.NSEW)
        search_frame.rowconfigure(0, weight=1)
        search_frame.columnconfigure(0, weight=1)

        def begin_search():
            import requests
            from bs4 import BeautifulSoup
            query_page = requests.get(
                'https://hshop.erista.me/c/games/s/north-america')
            soup = BeautifulSoup(query_page.text, 'html.parser')
            for game in soup.find_all(name='a', attrs={
                    'class': 'list-entry block-link'}):
                title_node = game.find(name='h3', attrs={
                    'class': 'green bold nospace'})
                if title_node is not None:
                    name = title_node.contents[0]
                    print(title_node.contents)
                    self.search.insert('', tk.END, text=name, iid=name,
                                       values=(game.attrs['href'], name, name, name))
            pass
        search_start = ttk.Button(
            search_frame, text='Search', command=begin_search)
        search_start.grid(row=1, column=0, sticky=tk.NSEW)

        search_frame_scrollbar = ttk.Scrollbar(
            search_frame, orient=tk.VERTICAL)
        search_frame_scrollbar.grid(row=0, column=1, sticky=tk.NSEW)

        self.search = ttk.Treeview(
            search_frame, yscrollcommand=search_frame_scrollbar.set)
        self.search.grid(row=0, column=0, sticky=tk.NSEW)
        self.search.configure(
            columns=('id', 'name', 'region', 'type'), show='headings')
        self.search.column('id', width=200, anchor=tk.W)
        self.search.column('name', width=200, anchor=tk.W)
        self.search.column('region', width=200, anchor=tk.W)
        self.search.column('type', width=200, anchor=tk.W)
        self.search.heading('id', text='Title ID')
        self.search.heading('name', text='Title name')
        self.search.heading('region', text='Region')
        self.search.heading('type', text='Type')

        def on_search_item_clicked(event):
            item = self.search.item(self.search.identify(
                'item', event.x, event.y), "values")
            id = item[0]
            name = item[1]
            self.queue.insert('', tk.END, text=id, iid=id,
                              values=(id, name))
            print(item)
        self.search.bind('<Double-1>', on_search_item_clicked)

        self.queue = ttk.Treeview(search_frame)
        self.queue.grid(row=0, column=1, sticky=tk.NSEW)
        self.queue.config(columns=('id', 'name'), show='headings')
        self.queue.column('id', width=200, anchor=tk.W)
        self.queue.heading('id', text='Title ID')
        self.queue.column('name', width=200, anchor=tk.W)
        self.queue.heading('name', text='Title name')

        def sizeof_fmt(num, suffix="B"):
            for unit in ("", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"):
                if abs(num) < 1024.0:
                    return f"{num:3.1f}{unit}{suffix}"
                num /= 1024.0
            return f"{num:.1f}Yi{suffix}"

        def start_downloads():
            completed = 0
            self.download_item_progress.configure(
                maximum=len(self.queue.get_children()), value=0)
            fnames = []
            for item in self.queue.get_children():
                target_item_url = 'https://hshop.erista.me' + item
                import cgi

                import requests
                from bs4 import BeautifulSoup
                self.pg_text.configure(
                    text='Fetching download URL for ' + item)
                text = requests.get(
                    target_item_url).text
                bsoup = BeautifulSoup(text, 'html.parser')
                download_url = bsoup.find_all(name='div', attrs={
                    'class': 'ddl-section'})[0].find_all(name='a')[0].attrs['href']

                import random
                self.pg_text.configure(text='Starting download for ' + item)
                file_resp = requests.get(download_url, stream=True)
                size = int(file_resp.headers['Content-Length'])
                self.current_download_progress.configure(maximum=size)
                _, params = cgi.parse_header(
                    file_resp.headers['Content-Disposition'])
                fname = params['filename']
                print(fname)
                lsz = 0
                with open('downloads/' + fname, 'wb') as handle:
                    for data in file_resp.iter_content(chunk_size=8192):
                        lsz += len(data)
                        self.current_download_progress.configure(value=lsz)
                        handle.write(data)
                        self.pg_text.configure(
                            text=sizeof_fmt(lsz) + '/'+sizeof_fmt(size))
                completed += 1
                self.download_item_progress.configure(value=completed)
                fnames.append('downloads/' + fname)
            self.pg_text.configure(
                text='Completed ' + str(len(self.queue.get_children())) + ' downloads')

            results = {}
            for f in fnames:
                success, reason = self.add_cia(f)
                if not success:
                    results[f] = reason

            if results:
                title_read_fail_window = TitleReadFailResults(
                    self.parent, failed=results)
                title_read_fail_window.focus()
            self.sort_treeview()

        def start_queue():
            Thread(target=start_downloads).start()
        download_button = ttk.Button(
            search_frame, text='Download', command=start_queue)
        download_button.grid(row=1, column=1, sticky=tk.NSEW)

        self.download_item_progress = ttk.Progressbar(
            search_frame, orient=tk.HORIZONTAL, mode='determinate')
        self.download_item_progress.grid(row=3, column=1, sticky=tk.NSEW)

        self.pg_text = ttk.Label(search_frame, text='')
        self.pg_text.grid(row=4, column=1, sticky=tk.NSEW)
        self.current_download_progress = ttk.Progressbar(
            search_frame, orient=tk.HORIZONTAL, mode='determinate')
        self.current_download_progress.grid(row=2, column=1, sticky=tk.NSEW)

        # ---------------------------------------------------------------- #
        # create treeview
        treeview_frame = ttk.Frame(self)
        treeview_frame.grid(row=3, column=0, sticky=tk.NSEW)
        treeview_frame.rowconfigure(0, weight=1)
        treeview_frame.columnconfigure(0, weight=1)

        treeview_scrollbar = ttk.Scrollbar(treeview_frame, orient=tk.VERTICAL)
        treeview_scrollbar.grid(row=0, column=1, sticky=tk.NSEW)

        self.treeview = ttk.Treeview(
            treeview_frame, yscrollcommand=treeview_scrollbar.set)
        self.treeview.grid(row=0, column=0, sticky=tk.NSEW)
        self.treeview.configure(
            columns=('filepath', 'titleid', 'titlename', 'status'), show='headings')

        self.treeview.column('filepath', width=200, anchor=tk.W)
        self.treeview.heading('filepath', text='File path')
        self.treeview.column('titleid', width=70, anchor=tk.W)
        self.treeview.heading('titleid', text='Title ID')
        self.treeview.column('titlename', width=150, anchor=tk.W)
        self.treeview.heading('titlename', text='Title name')
        self.treeview.column('status', width=20, anchor=tk.W)
        self.treeview.heading('status', text='Status')

        treeview_scrollbar.configure(command=self.treeview.yview)

        # ---------------------------------------------------------------- #
        # create progressbar

        self.progressbar = ttk.Progressbar(
            self, orient=tk.HORIZONTAL, mode='determinate')
        self.progressbar.grid(row=4, column=0, sticky=tk.NSEW)

        # ---------------------------------------------------------------- #
        # create start and console buttons

        control_frame = ttk.Frame(self)
        control_frame.grid(row=5, column=0)

        self.skip_contents_var = tk.IntVar()
        skip_contents_checkbox = ttk.Checkbutton(control_frame, text='Skip contents (only add to title database)',
                                                 variable=self.skip_contents_var)
        skip_contents_checkbox.grid(row=0, column=0)

        self.overwrite_saves_var = tk.IntVar()
        overwrite_saves_checkbox = ttk.Checkbutton(control_frame, text='Overwrite existing saves',
                                                   variable=self.overwrite_saves_var)
        overwrite_saves_checkbox.grid(row=0, column=1)

        show_console = ttk.Button(
            control_frame, text='Show console', command=self.open_console)
        show_console.grid(row=0, column=2)

        start = ttk.Button(control_frame, text='Start install',
                           command=self.start_install)
        start.grid(row=0, column=3)

        self.status_label = ttk.Label(self, text='Waiting...')
        self.status_label.grid(row=6, column=0, sticky=tk.NSEW)

        self.log(
            f'custom-install {CI_VERSION} - https://github.com/ihaveamac/custom-install', status=False)

        if is_windows and not taskbar:
            self.log('Note: Could not load taskbar lib.')
            self.log('Note: Progress will not be shown in the Windows taskbar.')

        self.log('Ready.')

        self.require_boot9 = (add_cias, add_cdn, add_dirs,
                              remove_selected, start)

        self.disable_buttons()
        self.check_b9_loaded()
        self.enable_buttons()
        if not self.b9_loaded:
            self.log(
                'Note: boot9 was not auto-detected. Please choose it before adding any titles.')

    def sort_treeview(self):
        l = [(self.treeview.set(k, 'titlename'), k)
             for k in self.treeview.get_children()]
        # sort by title name
        l.sort(key=lambda x: x[0].lower())

        for idx, pair in enumerate(l):
            self.treeview.move(pair[1], '', idx)

    def check_b9_loaded(self):
        if not self.b9_loaded:
            boot9 = self.file_picker_textboxes['boot9'].get(
                '1.0', tk.END).strip()
            try:
                tmp_crypto = CryptoEngine(boot9=boot9)
                self.b9_loaded = tmp_crypto.b9_keys_set
            except:
                return False
        return self.b9_loaded

    def update_status(self, path: 'Union[PathLike, bytes, str]', status: InstallStatus):
        self.treeview.set(path, 'status', statuses[status])

    def add_cia(self, path):
        if not self.check_b9_loaded():
            # this shouldn't happen
            return False, 'Please choose boot9 first'
        path = abspath(path)
        if path in self.readers:
            return False, 'File already in list'
        try:
            reader = CustomInstall.get_reader(path)
        except (CIAError, CDNError, TitleMetadataError):
            return False, 'Failed to read as a CIA or CDN title, probably corrupt'
        except MissingSeedError:
            return False, 'Latest seeddb.bin is required, check the README for details'
        except Exception as e:
            return False, f'Exception occurred: {type(e).__name__}: {e}'

        if reader.tmd.title_id.startswith('00048'):
            return False, 'DSiWare is not supported'
        try:
            title_name = reader.contents[0].exefs.icon.get_app_title(
            ).short_desc
        except:
            title_name = '(No title)'
        self.treeview.insert('', tk.END, text=path, iid=path,
                             values=(path, reader.tmd.title_id, title_name, statuses[InstallStatus.Waiting]))
        self.readers[path] = reader
        return True, ''

    def remove_cia(self, path):
        self.treeview.delete(path)
        del self.readers[path]

    def open_console(self):
        if self.console:
            self.console.parent.lift()
            self.console.focus()
        else:
            console_window = tk.Toplevel()
            console_window.title('custom-install Console')

            self.console = ConsoleFrame(console_window, self.log_messages)
            self.console.pack(fill=tk.BOTH, expand=True)

            def close():
                with self.lock:
                    try:
                        console_window.destroy()
                    except:
                        pass
                    self.console = None

            console_window.focus()

            console_window.protocol('WM_DELETE_WINDOW', close)

    def log(self, line, status=True):
        with self.lock:
            log_msg = f"{strftime('%H:%M:%S')} - {line}"
            self.log_messages.append(log_msg)
            if self.console:
                self.console.log(log_msg)

            if status:
                self.status_label.config(text=line)

    def show_error(self, message):
        mb.showerror('Error', message, parent=self.parent)

    def ask_warning(self, message):
        return mb.askokcancel('Warning', message, parent=self.parent)

    def show_info(self, message):
        mb.showinfo('Info', message, parent=self.parent)

    def disable_buttons(self):
        for b in self.require_boot9:
            b.config(state=tk.DISABLED)
        for b in self.file_picker_textboxes.values():
            b.config(state=tk.DISABLED)

    def enable_buttons(self):
        if self.b9_loaded:
            for b in self.require_boot9:
                b.config(state=tk.NORMAL)
        for b in self.file_picker_textboxes.values():
            b.config(state=tk.NORMAL)

    def start_install(self):
        sd_root = self.file_picker_textboxes['sd'].get('1.0', tk.END).strip()
        seeddb = self.file_picker_textboxes['seeddb'].get(
            '1.0', tk.END).strip()
        movable_sed = self.file_picker_textboxes['movable.sed'].get(
            '1.0', tk.END).strip()

        if not sd_root:
            self.show_error('SD root is not specified.')
            return
        if not movable_sed:
            self.show_error('movable.sed is not specified.')
            return

        if not seeddb:
            if not self.ask_warning('seeddb was not specified. Titles that require it will fail to install.\n'
                                    'Continue?'):
                return

        if not len(self.readers):
            self.show_error('There are no titles added to install.')
            return

        for path in self.readers.keys():
            self.update_status(path, InstallStatus.Waiting)
        self.disable_buttons()

        if taskbar:
            taskbar.SetProgressState(self.hwnd, tbl.TBPF_NORMAL)

        installer = CustomInstall(movable=movable_sed,
                                  sd=sd_root,
                                  skip_contents=self.skip_contents_var.get() == 1,
                                  overwrite_saves=self.overwrite_saves_var.get() == 1)

        if not installer.check_for_id0():
            self.show_error(f'id0 {installer.crypto.id0.hex()} was not found inside "Nintendo 3DS" on the SD card.\n'
                            f'\n'
                            f'Before using custom-install, you should use this SD card on the appropriate console.\n'
                            f'\n'
                            f'Otherwise, make sure the correct movable.sed is being used.')
            return

        self.log('Starting install...')

        # use the treeview which has been sorted alphabetically
        readers_final = []
        for k in self.treeview.get_children():
            filepath = self.treeview.set(k, 'filepath')
            readers_final.append((self.readers[filepath], filepath))

        installer.readers = readers_final

        finished_percent = 0
        max_percentage = 100 * len(self.readers)
        self.progressbar.config(maximum=max_percentage)

        def ci_on_log_msg(message, *args, **kwargs):
            # ignoring end
            self.log(message)

        def ci_update_percentage(total_percent, total_read, size):
            self.progressbar.config(value=total_percent + finished_percent)
            if taskbar:
                taskbar.SetProgressValue(self.hwnd, int(
                    total_percent + finished_percent), max_percentage)

        def ci_on_error(exc):
            if taskbar:
                taskbar.SetProgressState(self.hwnd, tbl.TBPF_ERROR)
            for line in format_exception(*exc):
                for line2 in line.split('\n')[:-1]:
                    installer.log(line2)
            self.show_error('An error occurred during installation.')
            self.open_console()

        def ci_on_cia_start(idx):
            nonlocal finished_percent
            finished_percent = idx * 100
            if taskbar:
                taskbar.SetProgressValue(
                    self.hwnd, finished_percent, max_percentage)

        installer.event.on_log_msg += ci_on_log_msg
        installer.event.update_percentage += ci_update_percentage
        installer.event.on_error += ci_on_error
        installer.event.on_cia_start += ci_on_cia_start
        installer.event.update_status += self.update_status

        if self.skip_contents_var.get() != 1:
            total_size, free_space = installer.check_size()
            if total_size > free_space:
                self.show_error(f'Not enough free space.\n'
                                f'Combined title install size: {total_size / (1024 * 1024):0.2f} MiB\n'
                                f'Free space: {free_space / (1024 * 1024):0.2f} MiB')
                self.enable_buttons()
                return

        def install():
            try:
                result, copied_3dsx, application_count = installer.start()
                if result:
                    result_window = InstallResults(self.parent,
                                                   install_state=result,
                                                   copied_3dsx=copied_3dsx,
                                                   application_count=application_count)
                    result_window.focus()
                elif result is None:
                    self.show_error("An error occurred when trying to run save3ds_fuse.\n"
                                    "Either title.db doesn't exist, or save3ds_fuse couldn't be run.")
                    self.open_console()
            except:
                installer.event.on_error(sys.exc_info())
            finally:
                self.enable_buttons()

        Thread(target=install).start()


window = tk.Tk()
window.title(f'custom-install {CI_VERSION}')
frame = CustomInstallGUI(window)
frame.pack(fill=tk.BOTH, expand=True)
window.mainloop()
