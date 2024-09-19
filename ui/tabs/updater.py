import tkinter as tk
import tkinter.ttk as ttk
from threading import Thread

from hshop.data import find_candidate_linked_content, find_hshop_title
from hshop.types import RelatedTitle
from sdfs.titles import collect_existing_titles, get_existing_title_ids


class UpdaterFrame(ttk.Frame):

    def __init__(self, file_picker_textboxes, queue: ttk.Treeview, parent: tk.Tk = None):
        super().__init__(parent, padding='10')
        self.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=1)
        self.queue = queue

        self.treeview = ttk.Treeview(self)
        self.treeview.grid(row=2, column=0, sticky=tk.NSEW)
        self.file_picker_textboxes = file_picker_textboxes

        def search_existing():
            sd_root = self.file_picker_textboxes['sd'].get(
                '1.0', tk.END).strip()
            seeddb = self.file_picker_textboxes['seeddb'].get(
                '1.0', tk.END).strip()
            movable_sed = self.file_picker_textboxes['movable.sed'].get(
                '1.0', tk.END).strip()
            boot9 = self.file_picker_textboxes['boot9'].get(
                '1.0', tk.END).strip()
            self.update_search_text.configure(text='Reading title IDs')
            t_ids = get_existing_title_ids(boot9, movable_sed, sd_root)
            titles_searched = 0

            install_queue = []
            titles = collect_existing_titles(boot9, movable_sed, sd_root)
            for r in titles:
                self.update_search_progress.configure(
                    value=titles_searched, maximum=len(t_ids)-1)
                self.update_search_text.configure(
                    text=f'{titles_searched+1}/{len(t_ids)}: checking updates and DLC for {r.title.short_desc}')
                titles_searched += 1
                self.treeview.insert('', tk.END, iid=r.id, text=f'{r.id} {
                    r.title.short_desc} by {r.title.publisher}', open=True)
                dlc_available = False
                update_available = False
                update: RelatedTitle = None
                dlc: RelatedTitle = None
                if r.dlc_id is None or r.update_id is None:
                    hshop_title = find_hshop_title(r.id)
                    if hshop_title is None:
                        continue
                    related_content = find_candidate_linked_content(
                        hshop_title.hshop_id)
                    for rc in related_content:
                        if rc.relation_type == 'Downloadable Content':
                            dlc_available = True
                            dlc = rc
                        elif rc.relation_type == 'Update':
                            update_available = True
                            update = rc
                if r.dlc_id is not None or dlc_available:
                    text = None
                    id = r.dlc_id
                    if r.dlc_id is not None:
                        text = 'Already installed:'
                    else:
                        text = 'Available:'
                        id = dlc.title_id
                        install_queue.append(dlc)
                    self.treeview.insert(
                        r.id, tk.END, text=f'{text} Downloadable Content ({id}) for {r.title.short_desc}')
                if r.update_id is not None or update_available:
                    text = None
                    id = r.update_id
                    if r.update_id is not None:
                        text = 'Already installed:'
                    else:
                        text = 'Available:'
                        id = update.title_id
                        install_queue.append(update)
                    self.treeview.insert(
                        r.id, tk.END, text=f'{text} Update ({id}) for {r.title.short_desc}')

            for q in install_queue:
                self.queue.insert('', tk.END, text=q.hshop_id, iid=q.hshop_id,
                                  values=(q.hshop_id, q.name))

        load_all_btn = ttk.Button(
            self, text='Search for existing games', command=lambda: Thread(target=search_existing).start())
        load_all_btn.grid(row=0, column=0, sticky=tk.NSEW)

        label_pair_frame = ttk.Frame(self)
        label_pair_frame.grid(row=1, column=0, sticky=tk.NSEW)
        label_pair_frame.rowconfigure(0, weight=1)
        label_pair_frame.columnconfigure(0, weight=1)
        label_pair_frame.columnconfigure(1, weight=1)

        self.update_search_progress = ttk.Progressbar(
            label_pair_frame, orient=tk.HORIZONTAL, mode='determinate')
        self.update_search_progress.grid(
            row=0, column=1, sticky=tk.NSEW)

        self.update_search_text = ttk.Label(
            label_pair_frame, text='Not searching')
        self.update_search_text.grid(row=0, column=0, sticky=tk.NSEW)
