from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup, PageElement


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
    pass


def _compile_meta_node(meta_node: PageElement):
    hshop_id = None
    title_id = None
    size = None
    version = None
    title_type = None
    prd_code = None

    data_nodes = meta_node.find_all(
        name='div', attrs={'class': 'meta-content'})

    for node in data_nodes:
        members = node.findChildren('span')
        if len(members) < 2:
            continue
        name = members[-1].text
        data = members[-2].text
        if name == 'ID':
            hshop_id = data
        elif name == 'Title ID':
            title_id = data
        elif name == 'Size':
            size = members[-3].text
        elif name == 'Version':
            version = data
        elif name == 'ID':
            hshop_id = data
        elif name == 'Content Type':
            title_type = data
        elif name == 'Product Code':
            prd_code = data
    return TitleMeta(hshop_id, title_id, size, version, title_type, prd_code)


def find_hshop_title(title_id: str):
    text = requests.get(
        f'https://hshop.erista.me/search/results?q={title_id}&qt=TitleID').text
    bsoup = BeautifulSoup(text, 'html.parser')
    all_metas = bsoup.find_all(name='a', attrs={
        'class': 'list-entry block-link'})
    if all_metas is None or len(all_metas) == 0:
        return None
    meta_section = all_metas[0]
    meta = _compile_meta_node(meta_section)
    title = meta_section.find_all(
        name='h3', attrs={'class': 'green bold nospace'})[0].text
    return Title(meta.hshop_id, meta.title_id, meta.size, meta.version, meta.type, meta.product_code, title)


def get_related_content(hshop_id: str) -> list[TitleRelation]:
    text = requests.get(f'https://hshop.erista.me/t/' + hshop_id).text
    bsoup = BeautifulSoup(text, 'html.parser')
    rc = related_content = bsoup.find_all(name='div', class_='related')
    if rc is None or len(rc) == 0:
        return []
    related_content = rc[0]
    results = []
    for related_item in related_content.find_all(name='a', class_='list-entry'):
        name = related_item.find_all(
            name='h3', class_='green bold nospace')[0].text

        meta_blocks = related_item.find_all(name='div', class_='meta')

        relation_type = related_item.find_all(
            name='span', class_='bold')[0].text.replace('Relation: ', '')
        meta_info = _compile_meta_node(meta_blocks[1])
        relation = TitleRelation(None, Title(meta_info.hshop_id, meta_info.title_id, meta_info.size,
                                 meta_info.version, meta_info.type, meta_info.product_code, name), relation_type)
        results.append(relation)
    return results


def find_all_linked_content(hshop_id: str, seen=[]) -> list[TitleRelation]:
    related_content = get_related_content(hshop_id)

    results = []
    for r in related_content:
        if r.relation_type == 'Base Title':
            continue
        results.append(r)
        if r.related_item.hshop_id not in seen:
            seen.append(r.related_item.hshop_id)
            results.extend(find_all_linked_content(
                r.related_item.hshop_id, seen))

    seen = set()
    final_results = []
    for x in results:
        if x.related_item.hshop_id not in seen:
            final_results.append(x)
            seen.add(x.related_item.hshop_id)
    return final_results


def find_candidate_linked_content(hshop_id: str) -> list[TitleRelation]:
    related_content = find_all_linked_content(hshop_id)
    DESIRED_TYPES = ['Downloadable Content', 'Update Data']
    return [x for x in related_content if x.relation_type in DESIRED_TYPES]


if __name__ == '__main__':
    title = find_hshop_title('00040000000EDF00')
    print(title)
    related_content = find_candidate_linked_content(title.hshop_id)
    for r in related_content:
        print(f'{r.related_item.hshop_id}: {
            r.relation_type}')
