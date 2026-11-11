"""HTML Serializer for WattsiPy matching Pascal Wattsi's output rules."""

from __future__ import annotations
import os
from typing import TextIO, Optional

from .dom import (
    Node,
    Element,
    Text,
    Document,
    DocumentType,
    NS_HTML,
    PROP_HTML,
    PROP_VOID_ELEMENT,
    PROP_RAW_TEXT_ELEMENT,
    PROP_OPTIONAL_START_TAG,
    PROP_OPTIONAL_END_TAG,
    PROP_TABLE_SECTION,
    PROP_TABLE_CELL,
    PROP_AUTOCLOSES_P,
    walk_to_next,
    walk_to_next_skipping_children,
)

EXCLUDING_ATTRIBUTES = {
    "html": "w-nohtml",
    "dev": "w-nodev",
    "snap": "w-nosnap",
    "review": "w-noreview",
    "split": "w-nosplit",
}

ALL_EXCLUDING_ATTRIBUTES = set(EXCLUDING_ATTRIBUTES.values())


def autoclosed_by(before: Element, after: Node) -> bool:
    if not isinstance(after, Element):
        return False
    b_tag = before.local_name
    a_tag = after.local_name

    if (b_tag in ("dt", "dd")) and (a_tag in ("dt", "dd")):
        return True
    if b_tag == "p" and after.has_properties(PROP_AUTOCLOSES_P):
        return True
    if before.has_properties(PROP_TABLE_SECTION) and after.has_properties(PROP_TABLE_SECTION):
        return True
    if before.has_properties(PROP_TABLE_CELL) and after.has_properties(PROP_TABLE_CELL):
        return True
    if b_tag == "li" and a_tag == "li":
        return True
    if b_tag == "tr" and a_tag == "tr":
        return True
    if b_tag in ("html", "head", "body"):
        return True
    return False


def skippable_tbody_start_tag(element: Element) -> bool:
    if element.local_name != "tbody":
        return False
    first = element.first_child
    if not (first and isinstance(first, Element) and first.local_name == "tr"):
        return False  # empty tbody or first child not <tr> can't be omitted
    prev = element.previous_sibling
    if prev is None:
        return True
    if not isinstance(prev, Element):
        return True
    if prev.has_properties(PROP_TABLE_SECTION):
        return False
    return True


def determine_is_excluder(element: Element) -> tuple[bool, int]:
    """Returns (is_excluder, printable_attribute_count)."""
    if not element.attributes:
        return False, 0

    attr_count = len(element.attributes)
    has_excluding = False
    for ex_attr in ALL_EXCLUDING_ATTRIBUTES:
        if ex_attr in element.attributes:
            attr_count -= 1
            has_excluding = True

    if "data-x" in element.attributes and element.attributes["data-x"] == "":
        attr_count -= 1

    is_ex = has_excluding and (attr_count == 0) and (element.local_name in ("div", "span"))

    if "data-x" in element.attributes and element.attributes["data-x"] != "":
        attr_count -= 1
    if "subdfn" in element.attributes:
        attr_count -= 1
    if "data-x-href" in element.attributes:
        attr_count -= 1
    if "undefined" in element.attributes:
        attr_count -= 1
    if "split-filename" in element.attributes:
        attr_count -= 1
    if "split-filename-target" in element.attributes:
        attr_count -= 1

    return is_ex, attr_count


def escape_attribute(value: str) -> tuple[str, bool]:
    """Returns (escaped_value, needs_double_quotes)."""
    if not value:
        return "", True

    for ch in value:
        if ch in ("\n", " ", "=", "<", ">", "`", "&", "'"):
            # Force double quote escaping: " -> &quot;, & -> &amp;
            escaped = value.replace("&", "&amp;").replace('"', "&quot;")
            return escaped, True

    return value, False


def escape_text(value: str) -> str:
    """Wattsi escape text: only & and < are escaped."""
    return value.replace("&", "&amp;").replace("<", "&lt;")


def insert_wpt_tests_block(element: Element, out: TextIO, variant: str) -> None:
    if variant in ("dev", "review"):
        return
    prefix = element.get_attribute("pathprefix").strip() or "/html/"
    text = element.text_content
    lines = text.split("\n")

    out.write("<div class=wpt-tests-margin>\n")
    out.write('<input onclick="toggleStatus(this)" value="⋰" type="button">\n')
    out.write("<dl>\n")
    for raw_subpath in lines:
        subpath = raw_subpath.strip()
        if not subpath:
            continue
        path = prefix + subpath
        filename = os.path.basename(path)
        scheme = "https" if (".https." in filename or ".serviceworker." in filename) else "http"
        out.write("<dt>")
        out.write(f'<a title="{filename}" href="https://wpt.fyi/results{path}">{filename}</a></dt>\n')
        out.write(f'<dd><a href="{scheme}://web-platform-tests.live{path}">(live test)</a>')
        out.write(f' <a href="https://github.com/web-platform-tests/wpt/blob/master{path}">(source)</a></dd>\n')
    out.write("</dl>\n")
    out.write("</div>\n")


def serialize_node(
    document: Document,
    out: TextIO,
    variant: str = "html",
    in_split: bool = False,
    bikeshed_pass: int = 0,
) -> None:
    out.write("<!DOCTYPE html>")
    current = document.get_document_element()
    if current is None:
        return

    current_element: Optional[Element] = None

    def walk_out(element: Element) -> None:
        nonlocal current_element
        if element.local_name == "pre" and element.text_content == "":
            return
        if element.local_name == "wpt":
            return
        if in_split and element.has_attribute("w-nosplit"):
            return

        is_excluder, attr_count = determine_is_excluder(element)
        is_void = element.has_properties(PROP_VOID_ELEMENT)
        is_optional_end = element.has_properties(PROP_OPTIONAL_END_TAG)
        can_omit_end = is_optional_end and (
            element.next_sibling is None or autoclosed_by(element, element.next_sibling)
        )

        if not (is_excluder or is_void or can_omit_end):
            out.write(f"</{element.local_name}>")

        if element.parent_node and isinstance(element.parent_node, Element):
            current_element = element.parent_node
        else:
            current_element = None

    while current is not None:
        if isinstance(current, Element):
            elem = current
            if elem.local_name == "wpt":
                insert_wpt_tests_block(elem, out, variant)
                current = walk_to_next_skipping_children(current, document, walk_out)
                continue

            if in_split and elem.has_attribute("w-nosplit"):
                current = walk_to_next_skipping_children(current, document, walk_out)
                continue

            # Drop empty <pre>
            if elem.local_name == "pre" and elem.text_content == "":
                current = walk_to_next_skipping_children(current, document, walk_out)
                continue

            is_excluder, attr_count = determine_is_excluder(elem)
            can_omit_start = (attr_count == 0) and (
                elem.has_properties(PROP_OPTIONAL_START_TAG) or skippable_tbody_start_tag(elem)
            )

            if not is_excluder and not can_omit_start:
                out.write(f"<{elem.local_name}")
                if attr_count > 0:
                    for attr_name, attr_val in elem.attributes.items():
                        if attr_name in ALL_EXCLUDING_ATTRIBUTES:
                            continue
                        if attr_name == "w-dev":
                            continue
                        if attr_name == "data-x" and bikeshed_pass != 1:
                            continue
                        if attr_name in (
                            "subdfn",
                            "data-x-href",
                            "undefined",
                            "split-filename",
                            "split-filename-target",
                        ):
                            continue

                        escaped_val, needs_quotes = escape_attribute(attr_val)
                        escaped_name = attr_name
                        if not elem.has_properties(PROP_HTML):
                            escaped_name = escaped_name.replace(" ", ":")

                        if needs_quotes:
                            out.write(f' {escaped_name}="{escaped_val}"')
                        else:
                            out.write(f" {escaped_name}={escaped_val}")
                out.write(">")

            current_element = elem
            current = walk_to_next(current, document, walk_out)

        elif isinstance(current, Text):
            assert current_element is not None
            if current_element.has_properties(PROP_RAW_TEXT_ELEMENT):
                out.write(current.data)
            else:
                out.write(escape_text(current.data))
            current = walk_to_next(current, document, walk_out)
        else:
            # Comment, DocumentType, etc. (Comments are omitted in Save)
            current = walk_to_next(current, document, walk_out)


def save_document(
    document: Document,
    file_path: str,
    variant: str = "html",
    in_split: bool = False,
    bikeshed_pass: int = 0,
) -> None:
    with open(file_path, "w", encoding="utf-8") as f:
        serialize_node(document, f, variant, in_split, bikeshed_pass)
        f.write("\n")
