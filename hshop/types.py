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
class TitleRelation:
    base_item: Title
    related_item: Title
    relation_type: str
