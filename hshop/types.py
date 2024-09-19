from dataclasses import dataclass


@dataclass
class TitleMeta:
    hshop_id: str
    title_id: str
    size: str
    version: str
    type: str
    product_code: str


@dataclass
class Title(TitleMeta):
    name: str


@dataclass
class RelatedTitle(Title):
    relation_type: str
