from bs4 import PageElement

from hshop.types import TitleMeta


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
