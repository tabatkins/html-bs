"""HTML Parser for WattsiPy using html5lib."""

from __future__ import annotations
import html5lib
from xml.dom import minidom
from typing import Optional, Union

from .dom import Document, DocumentType, Element, Text, Comment, NS_HTML, NS_MATHML, NS_SVG


def _convert_minidom(m_node, parent: Optional[Union[Document, Element]] = None):
    nt = m_node.nodeType
    if nt == minidom.Node.ELEMENT_NODE:
        ns = m_node.namespaceURI or NS_HTML
        node = Element(m_node.tagName, ns)
        if m_node.attributes:
            for i in range(m_node.attributes.length):
                attr = m_node.attributes.item(i)
                node.attributes[attr.name] = attr.value
    elif nt == minidom.Node.TEXT_NODE:
        node = Text(m_node.data)
    elif nt == minidom.Node.COMMENT_NODE:
        node = Comment(m_node.data)
    elif nt == minidom.Node.DOCUMENT_TYPE_NODE:
        node = DocumentType(m_node.name, m_node.publicId, m_node.systemId)
    elif nt == minidom.Node.DOCUMENT_NODE:
        node = Document()
    else:
        return None

    node.parent_node = parent
    if hasattr(m_node, "childNodes") and m_node.childNodes:
        children = []
        last_child = None
        for c in m_node.childNodes:
            conv = _convert_minidom(c, node)
            if conv is not None:
                # Merge adjacent text nodes just like Wattsi does
                if isinstance(conv, Text) and isinstance(last_child, Text):
                    last_child.data += conv.data
                else:
                    if last_child is not None:
                        last_child.next_sibling = conv
                        conv.previous_sibling = last_child
                    children.append(conv)
                    last_child = conv
        node.child_nodes = children
        if isinstance(node, Document):
            for c in children:
                if isinstance(c, Element) and node.document_element is None:
                    node.document_element = c
                elif isinstance(c, DocumentType) and node.doctype is None:
                    node.doctype = c
    return node


def parse_html(source: Union[str, bytes]) -> Document:
    """Parse HTML source text or bytes into a WattsiPy Document."""
    if isinstance(source, str):
        source = source.encode("utf-8")
    m_doc = html5lib.parse(source, treebuilder="dom", namespaceHTMLElements=False)
    doc = _convert_minidom(m_doc)
    assert isinstance(doc, Document)
    return doc
