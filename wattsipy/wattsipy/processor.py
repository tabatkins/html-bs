"""Document Processor for WattsiPy."""

from __future__ import annotations
import datetime
import os
import re
from typing import Optional, Union

from .dom import (
    Node,
    Element,
    Text,
    Comment,
    Document,
    NS_HTML,
    PROP_HEADING,
    PROP_RAW_TEXT_ELEMENT,
    PROP_CANNOT_CONTAIN_PALPABLE_TEXT,
    PROP_AUTOCLOSES_P,
    E,
    T,
    has_ancestor,
    has_ancestor_with_properties,
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

MONTHS = [
    "",
    "January", "February", "March", "April",
    "May", "June", "July", "August", "September",
    "October", "November", "December",
]

DFN_TYPES = (
    "abstract-op", "property", "value", "at-rule", "descriptor", "type",
    "function", "selector", "element", "element-attr", "attr-value",
    "element-state", "event", "interface", "namespace", "extended-attribute",
    "constructor", "method", "argument", "attribute", "callback", "dictionary",
    "dict-member", "enum", "enum-value", "exception", "const", "typedef",
    "stringifier", "serializer", "iterator", "maplike", "setlike", "grammar",
    "scheme", "state", "mode", "context", "facet", "http-header", "dfn",
)


def munge_for_json_output(original: str) -> str:
    # Replace all " with \" and \n with space, then squash sequences of spaces
    res = original.replace("\n", " ").replace('"', '\\"')
    return re.sub(r" +", " ", res)


def munge_topic_to_id(original: str) -> str:
    if not original:
        return ""
    res = []
    had_space = True
    for ch in original:
        if ch in (" ", "\n", "<", ">", "[", "\\", "]", "^", "{", "|", "}", "%"):
            if not had_space:
                res.append("-")
                had_space = True
        elif ch in ('"', "?", "`"):
            pass
        elif "A" <= ch <= "Z":
            res.append(ch.lower())
            had_space = False
        else:
            res.append(ch)
            had_space = False
    if had_space and res:
        res.pop()
    return "".join(res)


def munge_string_to_topic(original: str) -> str:
    if not original:
        return ""
    res = []
    had_space = False
    for ch in original:
        if ch == "#":
            pass
        elif ch in (" ", "\n"):
            if not had_space:
                res.append(" ")
                had_space = True
        elif "A" <= ch <= "Z":
            res.append(ch.lower())
            had_space = False
        else:
            res.append(ch)
            had_space = False
    if had_space and res:
        res.pop()
    return "".join(res)


def get_topic_identifier(element: Element) -> str:
    if element.has_attribute("data-x"):
        text = element.get_attribute("data-x")
    else:
        if len(element.child_nodes) == 1 and isinstance(element.first_child, Element):
            return get_topic_identifier(element.first_child)
        text = element.text_content
    return munge_string_to_topic(text)


def ensure_id(element: Element, suggested_id: str, ids: dict[str, Element]) -> str:
    if not element.has_attribute("id"):
        if suggested_id in ids:
            idx = 2
            while f"{suggested_id}-{idx}" in ids:
                idx += 1
            candidate = f"{suggested_id}-{idx}"
        else:
            candidate = suggested_id
        ids[candidate] = element
        element.set_attribute("id", candidate)
    return element.get_attribute("id")


def translate_bikeshed_syntax(element: Element) -> None:
    if element.has_attribute("lt"):
        raise RuntimeError(f'Element with lt="" found, use data-x="" instead; dfn is <{element.local_name}>')
    if element.has_attribute("for"):
        val = element.get_attribute("for")
        element.set_attribute("data-dfn-for", val)
        element.remove_attribute("for")
    if element.has_attribute("export"):
        element.set_attribute("data-export", "")
        element.remove_attribute("export")
    if element.has_attribute("noexport"):
        element.set_attribute("data-noexport", "")
        element.remove_attribute("noexport")
    for dfn_type in DFN_TYPES:
        if element.has_attribute(dfn_type):
            if dfn_type == "dfn" and element.is_identity(NS_HTML, "dfn"):
                raise RuntimeError('<dfn> element found with redundant dfn="" attribute')
            element.set_attribute("data-dfn-type", dfn_type)
            element.remove_attribute(dfn_type)
    if element.has_attribute("data-dfn-type") and element.has_attribute("data-export"):
        if element.get_attribute("data-dfn-type") != "dfn":
            raise RuntimeError("Element found with dfn type name and redundant export attribute")


class DFNEntry:
    def __init__(self):
        self.dfn_element: Optional[Element] = None
        self.sub_dfn_element: Optional[Element] = None
        self.usage_count: int = 0


class CrossRefRecord:
    def __init__(
        self,
        element: Element,
        topic: str,
        last_heading: str,
        last_heading_text: str,
        split_filename: str,
        kind: str,
    ):
        self.element = element
        self.topic = topic
        self.last_heading = last_heading
        self.last_heading_text = last_heading_text
        self.split_filename = split_filename
        self.kind = kind  # 'explicit' or 'implicit'


class Processor:
    def __init__(
        self,
        document: Document,
        variant: str,
        source_git_sha: str,
        output_directory: str,
        bikeshed_pass: int = 0,
    ):
        self.document = document
        self.variant = variant
        self.source_git_sha = source_git_sha
        self.output_directory = output_directory
        self.bikeshed_pass = bikeshed_pass

        self.ids: dict[str, Element] = {}
        self.dfns: dict[str, DFNEntry] = {}
        self.cross_references: list[CrossRefRecord] = []
        self.references: dict[str, list[Element]] = {}
        self.missing_references: dict[str, list[Element]] = {}
        self.xrefs_by_dfn_anchor: dict[str, dict[str, list[str]]] = {}
        self.heading_text_by_section_number: dict[str, str] = {}

        self.big_toc: Optional[Element] = None
        self.big_toc_bookmark: Optional[Node] = None
        self.small_toc: Optional[Element] = None
        self.small_toc_bookmark: Optional[Node] = None
        self.last_toc_ol: Optional[Element] = None
        self.last_toc_li: Optional[Element] = None
        self.last_heading_rank: int = 1
        self.current_section_number: list[int] = [0] * 7

        self.split_filename: str = ""
        self.split_filename_class_name: str = ""
        self.last_seen_heading_text: str = ""
        self.last_seen_heading_id: str = ""
        self.last_seen_reference_name: str = ""

        self.in_heading: Optional[Element] = None
        self.in_dfn: Optional[Element] = None
        self.in_references: Optional[Element] = None

        self.search_index_file = None
        self.is_first_search_index_item = True
        self.errors = 0

    def fail(self, message: str) -> None:
        cleaned = message.replace("\n", " ")
        print(f"Error: {cleaned}")
        self.errors += 1

    def first_pass(self) -> None:
        current = self.document
        excl_attr = EXCLUDING_ATTRIBUTES.get(self.variant, "")

        while current is not None:
            if isinstance(current, Element):
                elem = current
                if (excl_attr and elem.has_attribute(excl_attr)) or (
                    self.variant != "dev" and elem.has_attribute("w-dev")
                ):
                    nxt = walk_to_next_skipping_children(current, self.document, None)
                    current.remove()
                    current = nxt
                    continue
                elif elem.has_attribute("id"):
                    id_str = elem.get_attribute("id")
                    if id_str in self.ids:
                        self.fail(f'Multiple elements found with ID "{id_str}"')
                    self.ids[id_str] = elem
                elif elem.attributes:
                    attr_count = 0
                    for sub_var in ("html", "dev", "snap", "review"):
                        if elem.has_attribute(EXCLUDING_ATTRIBUTES[sub_var]):
                            attr_count += 1
                    if (
                        attr_count > 0
                        and attr_count == len(elem.attributes)
                        and elem.local_name in ("div", "span")
                    ):
                        if elem.has_child_nodes():
                            first_child = elem.first_child
                            assert elem.parent_node is not None
                            elem.parent_node.replace_child_with_children(elem)
                            current = first_child
                            continue
                        else:
                            nxt = walk_to_next_skipping_children(current, self.document, None)
                            current.remove()
                            current = nxt
                            continue
            elif isinstance(current, Text):
                assert current.parent_node is not None
                if current.parent_node.has_properties(PROP_CANNOT_CONTAIN_PALPABLE_TEXT):
                    nxt = walk_to_next_skipping_children(current, self.document, None)
                    current.remove()
                    current = nxt
                    continue

            current = walk_to_next(current, self.document, None)

    def save_cross_reference(self, element: Element) -> None:
        cross_ref_name = get_topic_identifier(element)
        if not cross_ref_name:
            return

        if self.bikeshed_pass == 1:
            if element.has_attribute("subdfn"):
                element.set_attribute("data-x", cross_ref_name)
            else:
                element.set_attribute("data-wattsi-x", cross_ref_name)
                element.set_attribute("data-x-lt", cross_ref_name)

        if cross_ref_name not in self.dfns:
            self.dfns[cross_ref_name] = DFNEntry()
        dfn_entry = self.dfns[cross_ref_name]

        if element.has_attribute("subdfn"):
            if dfn_entry.sub_dfn_element is not None:
                self.fail(f'Multiple secondary definitions (subdfn) for term "{cross_ref_name}"')
            dfn_entry.sub_dfn_element = element
            if self.variant != "dev":
                ensure_id(element, munge_topic_to_id(cross_ref_name + "-dev"), self.ids)
            else:
                ensure_id(element, munge_topic_to_id(cross_ref_name), self.ids)

        sec_nums = [
            str(self.current_section_number[r])
            for r in range(2, self.last_heading_rank + 1)
        ]
        sec_num_str = ".".join(sec_nums)
        dfn_entry.usage_count += 1

        if self.split_filename_class_name == "no-num":
            last_heading_text = self.last_seen_heading_text
        else:
            last_heading_text = f"{sec_num_str} {self.last_seen_heading_text}".strip()

        if (
            element.has_attribute("data-x")
            or element.is_identity(NS_HTML, "code")
            or (element.is_identity(NS_HTML, "span") and not element.attributes)
        ):
            kind = "explicit"
        else:
            kind = "implicit"

        self.cross_references.append(
            CrossRefRecord(
                element=element,
                topic=cross_ref_name,
                last_heading=self.last_seen_heading_id,
                last_heading_text=last_heading_text,
                split_filename=self.split_filename,
                kind=kind,
            )
        )

    def process_node(self, node: Node) -> tuple[bool, Node]:
        """Returns (keep, node) tuple. False to drop, True to keep."""
        if isinstance(node, Element):
            elem = node
            class_val = elem.get_attribute("class")

            # Check heading
            if elem.has_properties(PROP_HEADING):
                translate_bikeshed_syntax(elem)
                class_name = elem.get_attribute("class")
                rank = elem.rank
                if rank > 1:
                    self.in_heading = elem
                    if elem.has_attribute("split-filename"):
                        self.split_filename = elem.get_attribute("split-filename")
                        self.split_filename_class_name = elem.get_attribute("class")
                    self.last_seen_heading_text = elem.text_content
                    self.last_seen_heading_id = munge_topic_to_id(elem.text_content)
                    if not self.last_seen_heading_id:
                        self.last_seen_heading_id = "blank-heading"
                    self.last_seen_heading_id = ensure_id(elem, self.last_seen_heading_id, self.ids)

                    # Self link
                    if class_name != "no-num no-toc":
                        heading_self_link = E(
                            "a",
                            ["class", "self-link", "href", "#" + self.last_seen_heading_id],
                        )
                        elem.append_child(heading_self_link)

                    # Heading rank adjustment
                    if rank > self.last_heading_rank:
                        self.last_heading_rank += 1
                        if rank > self.last_heading_rank:
                            self.fail(f'heading rank failure - jumped a heading with text "{elem.text_content}"')
                            self.last_heading_rank = rank
                        self.current_section_number[self.last_heading_rank] = 0
                        if class_name != "no-num no-toc" and self.last_heading_rank > 2:
                            if self.last_toc_ol is not None:
                                if self.last_toc_li is None:
                                    self.fail("First heading after Table of Contents must be an <h2> also")
                                else:
                                    new_ol = E("ol")
                                    self.last_toc_li.append_child(new_ol)
                                    self.last_toc_ol = new_ol
                    else:
                        while rank < self.last_heading_rank:
                            self.last_heading_rank -= 1
                            if class_name != "no-num no-toc" and self.last_toc_ol is not None:
                                if (
                                    self.last_toc_ol.parent_node
                                    and self.last_toc_ol.parent_node.parent_node
                                    and isinstance(self.last_toc_ol.parent_node.parent_node, Element)
                                ):
                                    self.last_toc_ol = self.last_toc_ol.parent_node.parent_node

                    if class_name != "no-num no-toc":
                        if class_name != "no-num":
                            self.current_section_number[self.last_heading_rank] += 1
                            sec_nums = [
                                str(self.current_section_number[r])
                                for r in range(2, self.last_heading_rank + 1)
                            ]
                            sec_num_str = ".".join(sec_nums)
                            if self.variant == "dev" and self.search_index_file:
                                h_id = elem.get_attribute("id")
                                heading_text = munge_for_json_output(elem.text_content)
                                if not self.is_first_search_index_item:
                                    self.search_index_file.write(",")
                                self.is_first_search_index_item = False
                                self.search_index_file.write("{")
                                self.search_index_file.write(f'"url":"{self.split_filename}.html#{h_id}",')
                                self.search_index_file.write(f'"text":"{heading_text}",')
                                if "." in sec_num_str:
                                    parent_sec = sec_num_str.rsplit(".", 1)[0]
                                    parent_ht = self.heading_text_by_section_number.get(parent_sec, "")
                                    self.search_index_file.write(f'"section":"{sec_num_str} \u2014 {parent_ht}"')
                                else:
                                    self.search_index_file.write(f'"section":"{sec_num_str}"')
                                self.search_index_file.write("}")
                                self.heading_text_by_section_number[sec_num_str] = heading_text

                            new_span = E("span", ["class", "secno"], [T(sec_num_str)])
                            elem.insert_before(T(" "), elem.first_child)
                            elem.insert_before(new_span, elem.first_child)
                        else:
                            if self.variant == "dev" and self.search_index_file:
                                h_id = elem.get_attribute("id")
                                heading_text = munge_for_json_output(elem.text_content)
                                self.search_index_file.write(",{")
                                self.search_index_file.write(f'"url": "{self.split_filename}.html#{h_id}",')
                                self.search_index_file.write(f'"text": "{heading_text}",')
                                if self.split_filename == "indices" and h_id != "index":
                                    self.search_index_file.write('"section": " \u2014 Index"')
                                else:
                                    self.search_index_file.write('"section": ""')
                                self.search_index_file.write("}")

                        if self.last_toc_ol is not None or self.small_toc is not None:
                            new_li = E("li")
                            new_link = E("a", ["href", "#" + elem.get_attribute("id")])
                            temp_element = elem.clone_node(True)
                            cand = temp_element.first_child
                            if cand:
                                cand.remove()
                                new_link.append_child(cand)
                            cand = temp_element.first_child
                            in_skipped_node = False
                            while cand and not (
                                isinstance(cand, Element) and cand.get_attribute("class") == "self-link"
                            ):
                                selected_for_transfer = None
                                if isinstance(cand, Element) and (
                                    cand.is_identity(NS_HTML, "dfn") or cand.is_identity(NS_HTML, "span")
                                ):
                                    in_skipped_node = True
                                    if cand.has_child_nodes():
                                        cand = cand.first_child
                                        selected_for_transfer = cand
                                else:
                                    selected_for_transfer = cand

                                if cand and cand.next_sibling:
                                    cand = cand.next_sibling
                                elif in_skipped_node:
                                    cand = cand.parent_node.next_sibling if cand and cand.parent_node else None
                                    in_skipped_node = False
                                else:
                                    cand = None

                                if selected_for_transfer:
                                    selected_for_transfer.remove()
                                    new_link.append_child(selected_for_transfer)

                            new_li.append_child(new_link)
                            used_li = False
                            if self.last_toc_ol is not None:
                                self.last_toc_ol.append_child(new_li)
                                self.last_toc_li = new_li
                                used_li = True
                            if self.small_toc is not None and self.last_heading_rank == 2:
                                if used_li:
                                    second_li = new_li.clone_node(True)
                                    extracted_id = ensure_id(new_li, "toc-" + self.last_seen_heading_id, self.ids)
                                    if second_li.first_child and isinstance(second_li.first_child, Element):
                                        second_li.first_child.set_attribute("href", "#" + extracted_id)
                                else:
                                    second_li = new_li
                                self.small_toc.append_child(second_li)

            elif elem.is_identity(NS_HTML, "body") and self.variant == "snap":
                elem.set_attribute("class", "status-LS-COMMIT")

            elif elem.is_identity(NS_HTML, "span"):
                class_name = elem.get_attribute("class")
                if class_name in ("pubdate", "pubyear", "secno"):
                    if not elem.has_child_nodes() or not isinstance(elem.first_child, Text):
                        self.fail(f"{class_name} span must contain exactly one text node")
                    else:
                        today = datetime.date.today()
                        if class_name == "pubdate":
                            date_str = f"{today.day} {MONTHS[today.month]} {today.year}"
                        else:
                            date_str = str(today.year)
                        elem.first_child.data = date_str
                else:
                    if elem.has_attribute("lt"):
                        self.fail('<span> with lt="" found, use data-x="" instead')
                    if self.in_dfn is not None:
                        self.fail("<span> inside <dfn>")
                    else:
                        self.save_cross_reference(elem)

            elif elem.is_identity(NS_HTML, "title") and self.variant == "snap":
                elem.append_child(T(f" (Commit Snapshot {self.source_git_sha})"))

            elif elem.is_identity(NS_HTML, "dfn"):
                translate_bikeshed_syntax(elem)
                cross_ref_name = get_topic_identifier(elem)
                if self.bikeshed_pass == 1:
                    elem.set_attribute("data-x", cross_ref_name)
                if self.in_dfn is not None:
                    self.fail("Nested <dfn>")
                self.in_dfn = elem
                if cross_ref_name:
                    if cross_ref_name not in self.dfns:
                        self.dfns[cross_ref_name] = DFNEntry()
                    dfn_entry = self.dfns[cross_ref_name]
                    if dfn_entry.dfn_element is not None:
                        self.fail(f'Multiple definitions for term "{cross_ref_name}"')
                    if self.in_heading is not None:
                        dfn_entry.dfn_element = self.in_heading
                        if elem.has_attribute("data-x-href"):
                            self.fail("A deferring definition can't be in a heading")
                    else:
                        dfn_entry.dfn_element = elem
                        ensure_id(elem, munge_topic_to_id(cross_ref_name), self.ids)
                        if elem.has_attribute("data-x-href"):
                            data_x_href = elem.get_attribute("data-x-href")
                            new_link = E("a", ["href", data_x_href])
                            elem.swap_child_nodes(new_link)
                            elem.append_child(new_link)

            elif elem.is_identity(NS_HTML, "code") and self.in_dfn is None:
                if elem.has_attribute("lt"):
                    self.fail('<code> with lt="" found, use data-x="" instead')
                self.save_cross_reference(elem)

            elif elem.is_identity(NS_HTML, "a") and elem.get_attribute("href") == "/commit-snapshots/[SHA]":
                elem.set_attribute("href", f"/commit-snapshots/{self.source_git_sha}/")

            elif (
                elem.is_identity(NS_HTML, "a")
                and elem.get_attribute("class") == "sha-link"
                and self.variant == "snap"
            ):
                elem.append_child(T(self.source_git_sha))
                elem.append_child(T(" commit"))
                elem.set_attribute("href", f"https://github.com/whatwg/html/commit/{self.source_git_sha}")

            elif elem.is_identity(NS_HTML, "a") and not elem.has_attribute("href"):
                self.fail(f"<a> without href found")

            elif (
                elem.is_identity(NS_HTML, "i")
                and self.in_dfn is None
                and elem.has_attribute("data-x")
            ):
                if not elem.get_attribute("data-x"):
                    self.fail('<i> with empty data-x=""')
                self.save_cross_reference(elem)

            elif (
                elem.is_identity(NS_HTML, "var")
                and self.in_dfn is None
                and elem.has_attribute("data-x")
            ):
                if not elem.get_attribute("data-x"):
                    self.fail('<var> with empty data-x=""')
                self.save_cross_reference(elem)

            elif elem.is_identity(NS_HTML, "ref"):
                ref_name = elem.text_content
                if ref_name not in self.references:
                    self.references[ref_name] = []
                    self.missing_references[ref_name] = []
                self.references[ref_name].append(elem)
                self.missing_references[ref_name].append(elem)

                new_link = E("a", ["href", "#refs" + ref_name], [T(f"[{ref_name}]")])
                assert elem.parent_node is not None
                elem.parent_node.replace_child(new_link, elem)
                return self.process_node(new_link)

            elif elem.is_identity(NS_HTML, "dl") and elem.get_attribute("id") == "ref-list":
                self.in_references = elem

            elif self.in_references is not None and elem.is_identity(NS_HTML, "dt"):
                ref_id = elem.get_attribute("id")
                if len(ref_id) > 4:
                    self.last_seen_reference_name = ref_id[4:]
                    if self.last_seen_reference_name not in self.references:
                        if self.variant != "dev":
                            self.fail(f"Unused reference: [{self.last_seen_reference_name}]")
                        return False, elem
                    else:
                        self.missing_references.pop(self.last_seen_reference_name, None)
                else:
                    self.last_seen_reference_name = ""

            elif self.in_references is not None and elem.is_identity(NS_HTML, "dd"):
                if self.last_seen_reference_name not in self.references:
                    return False, elem

        elif isinstance(node, Comment):
            instruction = node.data
            if instruction == "toc":
                if self.last_heading_rank != 2:
                    self.fail("Table of Contents must be in the context of an <h2>")
                else:
                    self.big_toc = E("ol", ["class", "toc"])
                    self.big_toc_bookmark = node
                    self.last_toc_ol = self.big_toc
            elif instruction == "smalltoc" and self.variant != "dev":
                if self.last_heading_rank != 2:
                    self.fail("Small Table of Contents must be in the context of an <h2>")
                else:
                    self.small_toc = E("ol", ["class", "brief toc", "w-nosplit", ""])
                    self.small_toc_bookmark = node
            elif instruction == " NON-NORMATIVE SECTION " and self.variant != "dev":
                new_p = E("p", [E("i", [T("This section is non-normative.")])])
                assert node.parent_node is not None
                node.parent_node.replace_child(new_p, node)
                return self.process_node(new_p)
            elif instruction == "INSERT TRACKING" and self.variant != "dev":
                temp_elem = E(
                    "span",
                    [
                        "data-x", "tracking vector",
                        "title", "There is a tracking vector here.",
                        "class", "tracking-vector",
                    ],
                    [
                        E("img", [
                            "src", "https://resources.whatwg.org/tracking-vector.svg",
                            "alt", "(This is a tracking vector.)",
                            "width", "46",
                            "height", "64",
                            "class", "darkmode-aware",
                            "crossorigin", "",
                        ])
                    ],
                )
                assert node.parent_node is not None
                node.parent_node.replace_child(temp_elem, node)
                return self.process_node(temp_elem)
            else:
                return False, node

        return True, node

    def process_node_exit(self, node: Element) -> None:
        if node == self.in_heading:
            self.in_heading = None
        elif node == self.in_dfn:
            self.in_dfn = None
        elif node == self.in_references:
            self.in_references = None

    def second_pass(self) -> None:
        current = self.document
        while current is not None:
            keep, current = self.process_node(current)
            if not keep:
                last = current
                nxt = walk_to_next_skipping_children(current, self.document, self.process_node_exit)
                last.remove()
                current = nxt
            else:
                current = walk_to_next(current, self.document, self.process_node_exit)

    def insert_cross_references(self) -> None:
        for ref in self.cross_references:
            if has_ancestor(ref.element, NS_HTML, "a"):
                continue

            dfn_entry = self.dfns.get(ref.topic)
            dfn = None
            if dfn_entry:
                if dfn_entry.dfn_element:
                    dfn = dfn_entry.dfn_element
                else:
                    dfn = dfn_entry.sub_dfn_element

            if dfn == ref.element:
                dfn = None

            if dfn is not None:
                if ref.element.has_attribute("undefined"):
                    self.fail(f'Use of defined term "{ref.topic}" marked as undefined')

                dfn_anchor = ensure_id(dfn, munge_topic_to_id(ref.topic), self.ids)
                ensure_id(ref.element, f"{ref.last_heading}:{dfn_anchor}", self.ids)

                new_link = E("a")
                ref.element.swap_child_nodes(new_link)

                if self.variant != "dev":
                    sec_name = munge_for_json_output(ref.last_heading_text)
                    anchor_str = f"{ref.split_filename}.html#{ref.element.get_attribute('id')}"
                    if dfn_anchor not in self.xrefs_by_dfn_anchor:
                        self.xrefs_by_dfn_anchor[dfn_anchor] = {}
                    if sec_name not in self.xrefs_by_dfn_anchor[dfn_anchor]:
                        self.xrefs_by_dfn_anchor[dfn_anchor][sec_name] = []
                    if anchor_str not in self.xrefs_by_dfn_anchor[dfn_anchor][sec_name]:
                        self.xrefs_by_dfn_anchor[dfn_anchor][sec_name].append(anchor_str)

                if ref.element.is_identity(NS_HTML, "span"):
                    if ref.element.has_attribute("id"):
                        self.ids[ref.element.get_attribute("id")] = new_link
                    ref.element.swap_attributes(new_link)
                    new_link.remove_attribute("data-x")
                    assert ref.element.parent_node is not None
                    ref.element.parent_node.replace_child(new_link, ref.element)
                else:
                    ref.element.append_child(new_link)
                    ref.element.remove_attribute("data-x")

                if dfn.has_attribute("data-x-href"):
                    data_x_href = dfn.get_attribute("data-x-href")
                    new_link.set_attribute("href", data_x_href)
                    new_link.set_attribute("data-x-internal", dfn_anchor)
                else:
                    new_link.set_attribute("href", "#" + dfn_anchor)

            else:
                if (
                    self.variant != "dev"
                    and not (
                        ref.element.is_identity(NS_HTML, "code")
                        and ref.element.parent_node
                        and isinstance(ref.element.parent_node, Element)
                        and ref.element.parent_node.is_identity(NS_HTML, "pre")
                    )
                ):
                    if ref.kind == "explicit":
                        if not ref.element.has_attribute("undefined"):
                            usage = dfn_entry.usage_count if dfn_entry else 1
                            if usage == 1:
                                self.fail(f'missing <dfn> for topic "{ref.topic}" explicitly')
                            else:
                                self.fail(f'missing <dfn> for topic "{ref.topic}" from {usage} sites including explicitly')
                    elif dfn_entry and dfn_entry.usage_count > 1:
                        self.fail(f'missing <dfn> for topic "{ref.topic}" from {dfn_entry.usage_count} sites including implicitly')

        if self.variant != "dev":
            self.write_xrefs_json()

        if self.big_toc_bookmark and self.big_toc:
            assert self.big_toc_bookmark.parent_node is not None
            self.big_toc_bookmark.parent_node.replace_child(self.big_toc, self.big_toc_bookmark)
            self.big_toc_bookmark = None

        if self.small_toc_bookmark and self.small_toc:
            assert self.small_toc_bookmark.parent_node is not None
            self.small_toc_bookmark.parent_node.replace_child(self.small_toc, self.small_toc_bookmark)
            self.small_toc_bookmark = None

        if self.variant != "dev":
            for missing_name in list(self.missing_references.keys()):
                self.fail(f"Missing reference: [{missing_name}]")

    def write_xrefs_json(self) -> None:
        xrefs_path = os.path.join(self.output_directory, "xrefs.json")
        with open(xrefs_path, "w", encoding="utf-8") as f:
            f.write("{")
            first_dfn = True
            for dfn_anchor, sec_map in self.xrefs_by_dfn_anchor.items():
                if not first_dfn:
                    f.write(",")
                first_dfn = False
                f.write(f'"{dfn_anchor}":{{')
                first_sec = True
                for sec_name, anchors in sec_map.items():
                    if not first_sec:
                        f.write(",")
                    first_sec = False
                    f.write(f'"{sec_name}":[')
                    first_anc = True
                    for anc in anchors:
                        if not first_anc:
                            f.write(",")
                        first_anc = False
                        f.write(f'"{anc}"')
                    f.write("]")
                f.write("}")
            f.write("}")

    def run(self) -> Optional[Element]:
        self.first_pass()

        if self.variant == "dev":
            dev_dir = os.path.join(self.output_directory, "multipage-dev")
            os.makedirs(dev_dir, exist_ok=True)
            search_index_path = os.path.join(dev_dir, "search-index.json")
            self.search_index_file = open(search_index_path, "w", encoding="utf-8")
            self.search_index_file.write("[")
            self.second_pass()
            self.search_index_file.write("]")
            self.search_index_file.close()
            self.search_index_file = None
        else:
            self.second_pass()

        self.insert_cross_references()
        return self.big_toc


def process_document(
    document: Document,
    variant: str,
    source_git_sha: str,
    output_directory: str,
    bikeshed_pass: int = 0,
) -> Optional[Element]:
    processor = Processor(
        document=document,
        variant=variant,
        source_git_sha=source_git_sha,
        output_directory=output_directory,
        bikeshed_pass=bikeshed_pass,
    )
    return processor.run()
