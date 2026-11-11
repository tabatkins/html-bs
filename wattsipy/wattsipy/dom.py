"""DOM representation for WattsiPy."""

from __future__ import annotations
from typing import Callable, Optional, Union

# Namespaces
NS_HTML = "http://www.w3.org/1999/xhtml"
NS_MATHML = "http://www.w3.org/1998/Math/MathML"
NS_SVG = "http://www.w3.org/2000/svg"

# Element Properties bitflags matching webdom.pas
PROP_HTML = 1 << 0
PROP_TABLE_SECTION = 1 << 1
PROP_TABLE_CELL = 1 << 2
PROP_HEADING = 1 << 3
PROP_VOID_ELEMENT = 1 << 4
PROP_RAW_TEXT_ELEMENT = 1 << 5
PROP_ESCAPABLE_RAW_TEXT_ELEMENT = 1 << 6
PROP_OPTIONAL_START_TAG = 1 << 7
PROP_OPTIONAL_END_TAG = 1 << 8
PROP_CANNOT_CONTAIN_PALPABLE_TEXT = 1 << 9
PROP_AUTOCLOSES_P = 1 << 16
PROP_FOSTER_PARENT = 1 << 17
PROP_GENERIC_SCOPE = 1 << 18
PROP_LIST_ITEM_SCOPE = 1 << 19
PROP_BUTTON_SCOPE = 1 << 20
PROP_TABLE_SCOPE = 1 << 21
PROP_SELECT_SCOPE = 1 << 22
PROP_TBODY_CONTEXT = 1 << 23
PROP_TR_CONTEXT = 1 << 24
PROP_SPECIAL = 1 << 25
PROP_SPECIALISH = 1 << 26
PROP_MATHML_TEXT_INTEGRATION_POINT = 1 << 27
PROP_HTML_INTEGRATION_POINT = 1 << 28
PROP_BODY_IMPLIED_END_TAG = 1 << 29
PROP_EOF_IMPLIED_END_TAG = 1 << 30
PROP_TEMPLATE_IMPLIED_END_TAG = 1 << 31

ELEMENT_PROPERTIES: dict[str, int] = {
    "a": 0,
    "abbr": 0,
    "address": PROP_SPECIAL | PROP_AUTOCLOSES_P,
    "applet": PROP_GENERIC_SCOPE | PROP_LIST_ITEM_SCOPE | PROP_BUTTON_SCOPE | PROP_SPECIAL | PROP_SPECIALISH,
    "area": PROP_SPECIAL | PROP_SPECIALISH | PROP_VOID_ELEMENT | PROP_CANNOT_CONTAIN_PALPABLE_TEXT,
    "article": PROP_SPECIAL | PROP_SPECIALISH | PROP_AUTOCLOSES_P,
    "aside": PROP_SPECIAL | PROP_SPECIALISH | PROP_AUTOCLOSES_P,
    "audio": 0,
    "b": 0,
    "base": PROP_SPECIAL | PROP_SPECIALISH | PROP_VOID_ELEMENT | PROP_CANNOT_CONTAIN_PALPABLE_TEXT,
    "basefont": PROP_SPECIAL | PROP_SPECIALISH,
    "bdi": 0,
    "bdo": 0,
    "bgsound": PROP_SPECIAL | PROP_SPECIALISH,
    "big": 0,
    "blink": 0,
    "blockquote": PROP_SPECIAL | PROP_SPECIALISH | PROP_AUTOCLOSES_P,
    "body": PROP_SPECIAL | PROP_SPECIALISH | PROP_EOF_IMPLIED_END_TAG | PROP_OPTIONAL_END_TAG,
    "br": PROP_SPECIAL | PROP_SPECIALISH | PROP_VOID_ELEMENT | PROP_CANNOT_CONTAIN_PALPABLE_TEXT,
    "button": PROP_BUTTON_SCOPE | PROP_SPECIAL | PROP_SPECIALISH,
    "canvas": 0,
    "caption": PROP_GENERIC_SCOPE | PROP_LIST_ITEM_SCOPE | PROP_BUTTON_SCOPE | PROP_SPECIAL | PROP_SPECIALISH | PROP_TEMPLATE_IMPLIED_END_TAG,
    "center": PROP_SPECIAL | PROP_SPECIALISH,
    "cite": 0,
    "code": 0,
    "col": PROP_SPECIAL | PROP_SPECIALISH | PROP_VOID_ELEMENT | PROP_CANNOT_CONTAIN_PALPABLE_TEXT,
    "colgroup": PROP_SPECIAL | PROP_SPECIALISH | PROP_TEMPLATE_IMPLIED_END_TAG | PROP_CANNOT_CONTAIN_PALPABLE_TEXT,
    "data": 0,
    "datalist": 0,
    "dd": PROP_BODY_IMPLIED_END_TAG | PROP_EOF_IMPLIED_END_TAG | PROP_SPECIAL | PROP_SPECIALISH | PROP_OPTIONAL_END_TAG | PROP_TEMPLATE_IMPLIED_END_TAG,
    "del": 0,
    "details": PROP_SPECIAL | PROP_SPECIALISH,
    "dfn": 0,
    "dialog": 0,
    "dir": PROP_SPECIAL | PROP_SPECIALISH,
    "div": PROP_SPECIAL | PROP_AUTOCLOSES_P,
    "dl": PROP_SPECIAL | PROP_SPECIALISH | PROP_AUTOCLOSES_P | PROP_CANNOT_CONTAIN_PALPABLE_TEXT,
    "dt": PROP_BODY_IMPLIED_END_TAG | PROP_EOF_IMPLIED_END_TAG | PROP_SPECIAL | PROP_SPECIALISH | PROP_OPTIONAL_END_TAG | PROP_TEMPLATE_IMPLIED_END_TAG,
    "em": 0,
    "embed": PROP_SPECIAL | PROP_SPECIALISH | PROP_VOID_ELEMENT | PROP_CANNOT_CONTAIN_PALPABLE_TEXT,
    "fieldset": PROP_SPECIAL | PROP_SPECIALISH | PROP_AUTOCLOSES_P,
    "figcaption": PROP_SPECIAL | PROP_SPECIALISH,
    "figure": PROP_SPECIAL | PROP_SPECIALISH,
    "font": 0,
    "footer": PROP_SPECIAL | PROP_SPECIALISH | PROP_AUTOCLOSES_P,
    "form": PROP_SPECIAL | PROP_SPECIALISH | PROP_AUTOCLOSES_P,
    "frame": PROP_SPECIAL | PROP_SPECIALISH,
    "frameset": PROP_SPECIAL | PROP_SPECIALISH,
    "h1": PROP_HEADING | PROP_SPECIAL | PROP_SPECIALISH | PROP_AUTOCLOSES_P,
    "h2": PROP_HEADING | PROP_SPECIAL | PROP_SPECIALISH | PROP_AUTOCLOSES_P,
    "h3": PROP_HEADING | PROP_SPECIAL | PROP_SPECIALISH | PROP_AUTOCLOSES_P,
    "h4": PROP_HEADING | PROP_SPECIAL | PROP_SPECIALISH | PROP_AUTOCLOSES_P,
    "h5": PROP_HEADING | PROP_SPECIAL | PROP_SPECIALISH | PROP_AUTOCLOSES_P,
    "h6": PROP_HEADING | PROP_SPECIAL | PROP_SPECIALISH | PROP_AUTOCLOSES_P,
    "head": PROP_SPECIAL | PROP_SPECIALISH | PROP_OPTIONAL_START_TAG | PROP_OPTIONAL_END_TAG | PROP_CANNOT_CONTAIN_PALPABLE_TEXT,
    "header": PROP_SPECIAL | PROP_SPECIALISH | PROP_AUTOCLOSES_P,
    "hgroup": PROP_SPECIAL | PROP_SPECIALISH | PROP_AUTOCLOSES_P | PROP_CANNOT_CONTAIN_PALPABLE_TEXT,
    "hr": PROP_SPECIAL | PROP_SPECIALISH | PROP_VOID_ELEMENT | PROP_AUTOCLOSES_P | PROP_CANNOT_CONTAIN_PALPABLE_TEXT,
    "html": PROP_GENERIC_SCOPE | PROP_LIST_ITEM_SCOPE | PROP_BUTTON_SCOPE | PROP_TABLE_SCOPE | PROP_TBODY_CONTEXT | PROP_TR_CONTEXT | PROP_SPECIAL | PROP_SPECIALISH | PROP_EOF_IMPLIED_END_TAG | PROP_BODY_IMPLIED_END_TAG | PROP_OPTIONAL_START_TAG | PROP_OPTIONAL_END_TAG | PROP_CANNOT_CONTAIN_PALPABLE_TEXT,
    "i": 0,
    "iframe": PROP_SPECIAL | PROP_SPECIALISH,
    "img": PROP_SPECIAL | PROP_SPECIALISH | PROP_VOID_ELEMENT | PROP_CANNOT_CONTAIN_PALPABLE_TEXT,
    "input": PROP_SPECIAL | PROP_SPECIALISH | PROP_VOID_ELEMENT | PROP_CANNOT_CONTAIN_PALPABLE_TEXT,
    "ins": 0,
    "isindex": PROP_SPECIAL | PROP_SPECIALISH,
    "kbd": 0,
    "keygen": PROP_VOID_ELEMENT | PROP_CANNOT_CONTAIN_PALPABLE_TEXT,
    "label": 0,
    "legend": 0,
    "li": PROP_BODY_IMPLIED_END_TAG | PROP_EOF_IMPLIED_END_TAG | PROP_SPECIAL | PROP_SPECIALISH | PROP_OPTIONAL_END_TAG | PROP_TEMPLATE_IMPLIED_END_TAG,
    "link": PROP_SPECIAL | PROP_SPECIALISH | PROP_VOID_ELEMENT | PROP_CANNOT_CONTAIN_PALPABLE_TEXT,
    "listing": PROP_SPECIAL | PROP_SPECIALISH,
    "main": PROP_SPECIAL | PROP_SPECIALISH | PROP_AUTOCLOSES_P,
    "map": 0,
    "mark": 0,
    "marquee": PROP_GENERIC_SCOPE | PROP_LIST_ITEM_SCOPE | PROP_BUTTON_SCOPE | PROP_SPECIAL | PROP_SPECIALISH,
    "menu": PROP_SPECIAL | PROP_SPECIALISH | PROP_AUTOCLOSES_P,
    "menuitem": PROP_SPECIAL | PROP_SPECIALISH | PROP_VOID_ELEMENT | PROP_CANNOT_CONTAIN_PALPABLE_TEXT,
    "meta": PROP_SPECIAL | PROP_SPECIALISH | PROP_VOID_ELEMENT | PROP_CANNOT_CONTAIN_PALPABLE_TEXT,
    "meter": 0,
    "multicol": 0,
    "nav": PROP_SPECIAL | PROP_SPECIALISH | PROP_AUTOCLOSES_P,
    "nextid": 0,
    "nobr": 0,
    "noembed": PROP_SPECIAL | PROP_SPECIALISH,
    "noframes": PROP_SPECIAL | PROP_SPECIALISH,
    "noscript": PROP_SPECIAL | PROP_SPECIALISH,
    "object": PROP_GENERIC_SCOPE | PROP_LIST_ITEM_SCOPE | PROP_BUTTON_SCOPE | PROP_SPECIAL | PROP_SPECIALISH,
    "ol": PROP_LIST_ITEM_SCOPE | PROP_SPECIAL | PROP_SPECIALISH | PROP_AUTOCLOSES_P | PROP_CANNOT_CONTAIN_PALPABLE_TEXT,
    "optgroup": PROP_SELECT_SCOPE | PROP_BODY_IMPLIED_END_TAG | PROP_EOF_IMPLIED_END_TAG | PROP_TEMPLATE_IMPLIED_END_TAG | PROP_OPTIONAL_END_TAG | PROP_CANNOT_CONTAIN_PALPABLE_TEXT,
    "option": PROP_SELECT_SCOPE | PROP_BODY_IMPLIED_END_TAG | PROP_OPTIONAL_END_TAG | PROP_TEMPLATE_IMPLIED_END_TAG,
    "output": 0,
    "p": PROP_BODY_IMPLIED_END_TAG | PROP_EOF_IMPLIED_END_TAG | PROP_SPECIAL | PROP_OPTIONAL_END_TAG | PROP_AUTOCLOSES_P | PROP_TEMPLATE_IMPLIED_END_TAG,
    "param": PROP_SPECIAL | PROP_SPECIALISH | PROP_VOID_ELEMENT | PROP_CANNOT_CONTAIN_PALPABLE_TEXT,
    "plaintext": PROP_SPECIAL | PROP_SPECIALISH,
    "pre": PROP_SPECIAL | PROP_SPECIALISH | PROP_AUTOCLOSES_P,
    "progress": 0,
    "q": 0,
    "rb": 0,
    "ref": 0,
    "rp": PROP_BODY_IMPLIED_END_TAG | PROP_OPTIONAL_END_TAG | PROP_TEMPLATE_IMPLIED_END_TAG,
    "rt": PROP_BODY_IMPLIED_END_TAG | PROP_OPTIONAL_END_TAG | PROP_TEMPLATE_IMPLIED_END_TAG,
    "ruby": 0,
    "s": 0,
    "samp": 0,
    "script": PROP_SPECIAL | PROP_SPECIALISH | PROP_RAW_TEXT_ELEMENT,
    "section": PROP_SPECIAL | PROP_SPECIALISH | PROP_AUTOCLOSES_P,
    "select": PROP_SPECIAL | PROP_SPECIALISH | PROP_CANNOT_CONTAIN_PALPABLE_TEXT,
    "small": 0,
    "source": PROP_SPECIAL | PROP_SPECIALISH | PROP_VOID_ELEMENT | PROP_CANNOT_CONTAIN_PALPABLE_TEXT,
    "spacer": 0,
    "span": 0,
    "strike": 0,
    "strong": 0,
    "style": PROP_SPECIAL | PROP_SPECIALISH | PROP_RAW_TEXT_ELEMENT,
    "sub": 0,
    "summary": PROP_SPECIAL | PROP_SPECIALISH,
    "sup": 0,
    "table": PROP_FOSTER_PARENT | PROP_GENERIC_SCOPE | PROP_LIST_ITEM_SCOPE | PROP_BUTTON_SCOPE | PROP_TABLE_SCOPE | PROP_SPECIAL | PROP_SPECIALISH | PROP_AUTOCLOSES_P | PROP_CANNOT_CONTAIN_PALPABLE_TEXT,
    "tbody": PROP_FOSTER_PARENT | PROP_TABLE_SECTION | PROP_TBODY_CONTEXT | PROP_SPECIAL | PROP_SPECIALISH | PROP_EOF_IMPLIED_END_TAG | PROP_TEMPLATE_IMPLIED_END_TAG | PROP_OPTIONAL_END_TAG | PROP_CANNOT_CONTAIN_PALPABLE_TEXT,
    "td": PROP_TABLE_CELL | PROP_GENERIC_SCOPE | PROP_LIST_ITEM_SCOPE | PROP_BUTTON_SCOPE | PROP_SPECIAL | PROP_SPECIALISH | PROP_EOF_IMPLIED_END_TAG | PROP_TEMPLATE_IMPLIED_END_TAG | PROP_OPTIONAL_END_TAG,
    "template": PROP_GENERIC_SCOPE | PROP_LIST_ITEM_SCOPE | PROP_BUTTON_SCOPE | PROP_TABLE_SCOPE | PROP_TBODY_CONTEXT | PROP_TR_CONTEXT | PROP_SPECIAL | PROP_SPECIALISH,
    "textarea": PROP_SPECIAL | PROP_SPECIALISH | PROP_ESCAPABLE_RAW_TEXT_ELEMENT,
    "tfoot": PROP_FOSTER_PARENT | PROP_TABLE_SECTION | PROP_TBODY_CONTEXT | PROP_SPECIAL | PROP_SPECIALISH | PROP_EOF_IMPLIED_END_TAG | PROP_TEMPLATE_IMPLIED_END_TAG | PROP_OPTIONAL_END_TAG | PROP_CANNOT_CONTAIN_PALPABLE_TEXT,
    "th": PROP_TABLE_CELL | PROP_GENERIC_SCOPE | PROP_LIST_ITEM_SCOPE | PROP_BUTTON_SCOPE | PROP_SPECIAL | PROP_SPECIALISH | PROP_EOF_IMPLIED_END_TAG | PROP_TEMPLATE_IMPLIED_END_TAG | PROP_OPTIONAL_END_TAG,
    "thead": PROP_FOSTER_PARENT | PROP_TABLE_SECTION | PROP_TBODY_CONTEXT | PROP_SPECIAL | PROP_SPECIALISH | PROP_EOF_IMPLIED_END_TAG | PROP_TEMPLATE_IMPLIED_END_TAG | PROP_OPTIONAL_END_TAG | PROP_CANNOT_CONTAIN_PALPABLE_TEXT,
    "time": 0,
    "title": PROP_SPECIAL | PROP_SPECIALISH | PROP_ESCAPABLE_RAW_TEXT_ELEMENT,
    "tr": PROP_FOSTER_PARENT | PROP_TR_CONTEXT | PROP_SPECIAL | PROP_SPECIALISH | PROP_EOF_IMPLIED_END_TAG | PROP_TEMPLATE_IMPLIED_END_TAG | PROP_OPTIONAL_END_TAG | PROP_CANNOT_CONTAIN_PALPABLE_TEXT,
    "track": PROP_SPECIAL | PROP_SPECIALISH | PROP_VOID_ELEMENT | PROP_CANNOT_CONTAIN_PALPABLE_TEXT,
    "tt": 0,
    "u": 0,
    "ul": PROP_LIST_ITEM_SCOPE | PROP_SPECIAL | PROP_SPECIALISH | PROP_AUTOCLOSES_P | PROP_CANNOT_CONTAIN_PALPABLE_TEXT,
    "var": 0,
    "video": 0,
    "wbr": PROP_SPECIAL | PROP_SPECIALISH | PROP_VOID_ELEMENT | PROP_CANNOT_CONTAIN_PALPABLE_TEXT,
    "xmp": PROP_SPECIAL | PROP_SPECIALISH,
}


class Node:
    def __init__(self):
        self.parent_node: Optional[Node] = None
        self.previous_sibling: Optional[Node] = None
        self.next_sibling: Optional[Node] = None

    def has_child_nodes(self) -> bool:
        return False

    def remove(self) -> None:
        if self.parent_node:
            self.parent_node.remove_child(self)

    @property
    def text_content(self) -> str:
        return ""

    def clone_node(self, deep: bool = False) -> Node:
        raise NotImplementedError


class Document(Node):
    def __init__(self):
        super().__init__()
        self.child_nodes: list[Node] = []
        self.doctype: Optional[DocumentType] = None
        self.document_element: Optional[Element] = None

    def has_child_nodes(self) -> bool:
        return bool(self.child_nodes)

    @property
    def first_child(self) -> Optional[Node]:
        return self.child_nodes[0] if self.child_nodes else None

    @property
    def last_child(self) -> Optional[Node]:
        return self.child_nodes[-1] if self.child_nodes else None

    def get_document_element(self) -> Optional[Element]:
        return self.document_element

    def append_child(self, node: Node) -> Node:
        if node.parent_node:
            node.parent_node.remove_child(node)
        if self.child_nodes:
            self.child_nodes[-1].next_sibling = node
            node.previous_sibling = self.child_nodes[-1]
        node.next_sibling = None
        self.child_nodes.append(node)
        node.parent_node = self
        if isinstance(node, Element) and self.document_element is None:
            self.document_element = node
        elif isinstance(node, DocumentType) and self.doctype is None:
            self.doctype = node
        return node

    def insert_before(self, new_node: Node, ref_node: Optional[Node]) -> Node:
        if new_node.parent_node:
            new_node.parent_node.remove_child(new_node)
        if ref_node is None:
            return self.append_child(new_node)
        idx = self.child_nodes.index(ref_node)
        prev = ref_node.previous_sibling
        if prev:
            prev.next_sibling = new_node
        new_node.previous_sibling = prev
        new_node.next_sibling = ref_node
        ref_node.previous_sibling = new_node
        new_node.parent_node = self
        self.child_nodes.insert(idx, new_node)
        if isinstance(new_node, Element) and (self.document_element is None or self.document_element == ref_node):
            self.document_element = new_node
        return new_node

    def remove_child(self, node: Node) -> Node:
        idx = self.child_nodes.index(node)
        prev = node.previous_sibling
        nxt = node.next_sibling
        if prev:
            prev.next_sibling = nxt
        if nxt:
            nxt.previous_sibling = prev
        self.child_nodes.pop(idx)
        node.parent_node = None
        node.previous_sibling = None
        node.next_sibling = None
        if self.document_element == node:
            self.document_element = None
        if self.doctype == node:
            self.doctype = None
        return node

    def clone_node(self, deep: bool = True) -> Document:
        clone = Document()
        if deep:
            for c in self.child_nodes:
                clone.append_child(c.clone_node(True))
        return clone


class DocumentType(Node):
    def __init__(self, name: str, public_id: str = "", system_id: str = ""):
        super().__init__()
        self.name = name
        self.public_id = public_id or ""
        self.system_id = system_id or ""

    def clone_node(self, deep: bool = False) -> DocumentType:
        return DocumentType(self.name, self.public_id, self.system_id)


class Element(Node):
    def __init__(self, local_name: str, namespace_url: str = NS_HTML, attributes: Optional[dict[str, str]] = None):
        super().__init__()
        self.local_name: str = local_name
        self.namespace_url: str = namespace_url
        self.attributes: dict[str, str] = dict(attributes) if attributes else {}
        self.child_nodes: list[Node] = []

    def has_child_nodes(self) -> bool:
        return bool(self.child_nodes)

    @property
    def first_child(self) -> Optional[Node]:
        return self.child_nodes[0] if self.child_nodes else None

    @property
    def last_child(self) -> Optional[Node]:
        return self.child_nodes[-1] if self.child_nodes else None

    @property
    def first_element_child(self) -> Optional[Element]:
        for c in self.child_nodes:
            if isinstance(c, Element):
                return c
        return None

    @property
    def last_element_child(self) -> Optional[Element]:
        for c in reversed(self.child_nodes):
            if isinstance(c, Element):
                return c
        return None

    @property
    def next_element_sibling(self) -> Optional[Element]:
        node = self.next_sibling
        while node:
            if isinstance(node, Element):
                return node
            node = node.next_sibling
        return None

    @property
    def previous_element_sibling(self) -> Optional[Element]:
        node = self.previous_sibling
        while node:
            if isinstance(node, Element):
                return node
            node = node.previous_sibling
        return None

    @property
    def rank(self) -> int:
        if len(self.local_name) == 2 and self.local_name[0] == 'h' and self.local_name[1] in '123456':
            return int(self.local_name[1])
        return 1

    def has_attribute(self, name: str) -> bool:
        return name in self.attributes

    def get_attribute(self, name: str) -> str:
        return self.attributes.get(name, "")

    def set_attribute(self, name: str, value: str) -> None:
        self.attributes[name] = value

    def remove_attribute(self, name: str) -> None:
        self.attributes.pop(name, None)

    def append_child(self, node: Node) -> Node:
        if node.parent_node:
            node.parent_node.remove_child(node)
        if self.child_nodes:
            self.child_nodes[-1].next_sibling = node
            node.previous_sibling = self.child_nodes[-1]
        node.next_sibling = None
        self.child_nodes.append(node)
        node.parent_node = self
        return node

    def insert_before(self, new_node: Node, ref_node: Optional[Node]) -> Node:
        if new_node.parent_node:
            new_node.parent_node.remove_child(new_node)
        if ref_node is None:
            return self.append_child(new_node)
        idx = self.child_nodes.index(ref_node)
        prev = ref_node.previous_sibling
        if prev:
            prev.next_sibling = new_node
        new_node.previous_sibling = prev
        new_node.next_sibling = ref_node
        ref_node.previous_sibling = new_node
        new_node.parent_node = self
        self.child_nodes.insert(idx, new_node)
        return new_node

    def remove_child(self, node: Node) -> Node:
        idx = self.child_nodes.index(node)
        prev = node.previous_sibling
        nxt = node.next_sibling
        if prev:
            prev.next_sibling = nxt
        if nxt:
            nxt.previous_sibling = prev
        self.child_nodes.pop(idx)
        node.parent_node = None
        node.previous_sibling = None
        node.next_sibling = None
        return node

    def replace_child(self, new_node: Node, old_node: Node) -> Node:
        if new_node.parent_node:
            new_node.parent_node.remove_child(new_node)
        idx = self.child_nodes.index(old_node)
        prev = old_node.previous_sibling
        nxt = old_node.next_sibling
        if prev:
            prev.next_sibling = new_node
        new_node.previous_sibling = prev
        if nxt:
            nxt.previous_sibling = new_node
        new_node.next_sibling = nxt
        new_node.parent_node = self
        old_node.parent_node = None
        old_node.previous_sibling = None
        old_node.next_sibling = None
        self.child_nodes[idx] = new_node
        return old_node

    def replace_child_with_children(self, old_node: Element) -> None:
        idx = self.child_nodes.index(old_node)
        children = list(old_node.child_nodes)
        if not children:
            self.remove_child(old_node)
            return
        for c in children:
            c.parent_node = self
        prev = old_node.previous_sibling
        nxt = old_node.next_sibling
        if prev:
            prev.next_sibling = children[0]
            children[0].previous_sibling = prev
        else:
            children[0].previous_sibling = None
        if nxt:
            nxt.previous_sibling = children[-1]
            children[-1].next_sibling = nxt
        else:
            children[-1].next_sibling = None
        old_node.parent_node = None
        old_node.previous_sibling = None
        old_node.next_sibling = None
        old_node.child_nodes = []
        self.child_nodes[idx:idx+1] = children

    def swap_child_nodes(self, other: Element) -> None:
        self.child_nodes, other.child_nodes = other.child_nodes, self.child_nodes
        for c in self.child_nodes:
            c.parent_node = self
        for c in other.child_nodes:
            c.parent_node = other

    def swap_attributes(self, other: Element) -> None:
        self.attributes, other.attributes = other.attributes, self.attributes

    @property
    def text_content(self) -> str:
        parts: list[str] = []
        def collect(node: Node) -> None:
            if isinstance(node, Text):
                parts.append(node.data)
            elif isinstance(node, Element):
                for c in node.child_nodes:
                    collect(c)
        collect(self)
        return "".join(parts)

    def is_identity(self, namespace_url: str, local_name: str) -> bool:
        if namespace_url:
            return self.namespace_url == namespace_url and self.local_name == local_name
        return self.local_name == local_name

    def has_properties(self, prop: int) -> bool:
        if prop == PROP_HTML:
            return self.namespace_url == NS_HTML
        tag_props = ELEMENT_PROPERTIES.get(self.local_name, 0)
        return bool(tag_props & prop)

    def clone_node(self, deep: bool = True) -> Element:
        clone = Element(self.local_name, self.namespace_url)
        clone.attributes = dict(self.attributes)
        if deep:
            for c in self.child_nodes:
                clone.append_child(c.clone_node(True))
        return clone


class Text(Node):
    def __init__(self, data: str):
        super().__init__()
        self.data: str = data

    @property
    def text_content(self) -> str:
        return self.data

    def clone_node(self, deep: bool = False) -> Text:
        return Text(self.data)


class Comment(Node):
    def __init__(self, data: str):
        super().__init__()
        self.data: str = data

    @property
    def text_content(self) -> str:
        return self.data

    def clone_node(self, deep: bool = False) -> Comment:
        return Comment(self.data)


TWalkOutCallback = Optional[Callable[[Element], None]]


def walk_to_next(current: Node, top: Node, walk_out_callback: TWalkOutCallback = None) -> Optional[Node]:
    """Walk to the next node in depth-first order. Returns the next node, or None if finished."""
    if current.has_child_nodes():
        if isinstance(current, Element):
            return current.first_child
        if isinstance(current, Document):
            return current.first_child
    return walk_to_next_skipping_children(current, top, walk_out_callback)


def walk_to_next_skipping_children(current: Node, top: Node, walk_out_callback: TWalkOutCallback = None) -> Optional[Node]:
    """Walk to the next sibling or ancestor's sibling, skipping current node's children."""
    def walk_out(node: Node) -> None:
        if isinstance(node, Element) and walk_out_callback is not None:
            walk_out_callback(node)

    if current == top:
        walk_out(current)
        return None

    if current.next_sibling is None:
        curr = current
        while curr.next_sibling is None:
            old = curr
            curr = curr.parent_node
            walk_out(old)
            if curr is None or curr == top:
                if curr is not None:
                    walk_out(curr)
                return None
        old = curr
        curr = curr.next_sibling
        walk_out(old)
        return curr

    old = current
    nxt = current.next_sibling
    walk_out(old)
    return nxt


def has_ancestor(element: Node, namespace_url: str, local_name: str) -> bool:
    curr = element.parent_node
    while curr:
        if isinstance(curr, Element) and curr.is_identity(namespace_url, local_name):
            return True
        curr = curr.parent_node
    return False


def has_ancestor_with_properties(element: Node, prop: int) -> bool:
    curr = element.parent_node
    while curr:
        if isinstance(curr, Element) and curr.has_properties(prop):
            return True
        curr = curr.parent_node
    return False


def E(tag_name: str, attrs_or_children=None, children_or_doc=None, children=None) -> Element:
    """Convenience constructor mimicking Pascal E(tag, [attrs], [children])."""
    attrs: dict[str, str] = {}
    child_list: list[Node] = []

    if isinstance(attrs_or_children, dict):
        attrs = dict(attrs_or_children)
    elif isinstance(attrs_or_children, list):
        if attrs_or_children and isinstance(attrs_or_children[0], str):
            # Key-value pairs list ['k1', 'v1', 'k2', 'v2']
            it = iter(attrs_or_children)
            for k in it:
                attrs[k] = next(it, "")
        else:
            child_list = list(attrs_or_children)

    if isinstance(children_or_doc, list):
        child_list = list(children_or_doc)

    if isinstance(children, list):
        child_list = list(children)

    elem = Element(tag_name, NS_HTML, attrs)
    for c in child_list:
        elem.append_child(c)
    return elem


def T(text: str) -> Text:
    return Text(text)
