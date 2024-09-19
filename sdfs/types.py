from dataclasses import dataclass

from pyctr.type.smdh import AppTitle


@dataclass
class InstalledTitle:
    id: str
    title: AppTitle
    update_id: str | None
    dlc_id: str | None
