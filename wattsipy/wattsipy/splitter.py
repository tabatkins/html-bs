"""Specification splitter for WattsiPy."""

from __future__ import annotations
import os
from typing import Optional

from .dom import (
    Node,
    Element,
    Document,
    Text,
    NS_HTML,
    E,
    T,
    walk_to_next,
    walk_to_next_skipping_children,
)
from .serializer import save_document


def trim(new_toc: Element, section_name: str) -> None:
    def trim_out(candidate: Element) -> None:
        if not candidate.has_child_nodes():
            candidate.remove()

    current = new_toc
    while current is not None:
        if (
            isinstance(current, Element)
            and current.is_identity(NS_HTML, "a")
            and current.get_attribute("split-filename-target") != section_name
        ):
            while current.has_child_nodes():
                assert current.first_child is not None
                current.first_child.remove()
        current = walk_to_next(current, new_toc, trim_out)


def split_specification(
    document: Document,
    big_toc: Optional[Element],
    base_dir: str,
    variant: str = "html",
    bikeshed_pass: int = 0,
) -> bool:
    os.makedirs(base_dir, exist_ok=True)

    link_fixup = E("script", ["src", "/link-fixup.js", "defer", ""])
    doc_elem = document.get_document_element()
    assert doc_elem is not None
    doc_elem.insert_before(link_fixup, doc_elem.first_child)

    # Find body
    body = None
    curr = document
    while curr is not None:
        if isinstance(curr, Element) and curr.is_identity(NS_HTML, "body"):
            body = curr
            break
        curr = walk_to_next(curr, document, None)
    assert body is not None

    # Find links and targets
    targets: dict[str, Element] = {}
    links: list[Element] = []
    curr = document
    while curr is not None:
        if isinstance(curr, Element):
            if curr.is_identity(NS_HTML, "a"):
                links.append(curr)
            if curr.has_attribute("id"):
                targets[curr.get_attribute("id")] = curr
        curr = walk_to_next(curr, document, None)

    # Extract sections
    sections = Element("list", "")
    section_names: set[str] = {"index"}
    current_section: Optional[Element] = None

    child = body.first_child
    while child is not None:
        curr = child
        child = child.next_sibling
        if isinstance(curr, Element) and curr.has_attribute("split-filename"):
            sec_name = curr.get_attribute("split-filename")
            if sec_name == "index":
                raise RuntimeError('split-filename "index" specified')
            if sec_name in section_names:
                raise RuntimeError(f"duplicate split-filename specified: {sec_name}")
            section_names.add(sec_name)
            current_section = Element("chapter", "")
            current_section.set_attribute("filename", sec_name)
            current_section.set_attribute("heading", curr.text_content)
            sections.append_child(current_section)

        if current_section is not None:
            curr.remove()
            current_section.append_child(curr)

    # Fragment links JSON
    fragment_links_path = os.path.join(base_dir, "fragment-links.json")
    with open(fragment_links_path, "w", encoding="utf-8") as f:
        f.write("{")
        first_target = True
        for target_id, target_elem in targets.items():
            if not first_target:
                f.write(",")
            first_target = False
            f.write(f'"{target_id}":"')
            home = target_elem
            while home.parent_node and isinstance(home.parent_node, Element) and not home.is_identity("", "chapter"):
                home = home.parent_node
            fn = home.get_attribute("filename") if home else ""
            f.write(fn)
            f.write('"')
        f.write("}")

    # Update all hyperlinks
    for a_link in links:
        if a_link.has_attribute("href"):
            href = a_link.get_attribute("href")
            if href.startswith("#") and len(href) > 1:
                target_id = href[1:]
                if target_id in targets:
                    link_home = a_link
                    while link_home.parent_node and isinstance(link_home.parent_node, Element) and not link_home.is_identity("", "chapter"):
                        link_home = link_home.parent_node

                    target_elem = targets[target_id]
                    target_home = target_elem
                    while target_home.parent_node and isinstance(target_home.parent_node, Element) and not target_home.is_identity("", "chapter"):
                        target_home = target_home.parent_node

                    if link_home != target_home:
                        target_file = target_home.get_attribute("filename")
                        a_link.set_attribute("href", f"{target_file}.html{href}")
                        a_link.set_attribute("split-filename-target", target_file)

    # Save table of contents section
    section_doc = document.clone_node(True)
    sec_doc_elem = section_doc.get_document_element()
    assert sec_doc_elem is not None
    sec_doc_elem.set_attribute("class", "split index")
    save_document(
        section_doc,
        os.path.join(base_dir, "index.html"),
        variant=variant,
        in_split=False,
        bikeshed_pass=bikeshed_pass,
    )

    if big_toc is not None:
        big_toc.remove()

    # Save each section
    curr_sec_node = sections.first_child
    while curr_sec_node is not None:
        assert isinstance(curr_sec_node, Element)
        sec_name = curr_sec_node.get_attribute("filename")
        section_doc = document.clone_node(True)
        sec_doc_elem = section_doc.get_document_element()
        assert sec_doc_elem is not None
        sec_doc_elem.set_attribute("class", "split")

        # Find body in section_doc
        sec_body = None
        c = section_doc
        while c is not None:
            if isinstance(c, Element) and c.is_identity(NS_HTML, "body"):
                sec_body = c
                break
            c = walk_to_next(c, section_doc, None)
        assert sec_body is not None

        # Build nav links
        link_home = E("nav")
        prev_sec = curr_sec_node.previous_sibling
        if prev_sec and isinstance(prev_sec, Element):
            prev_heading = prev_sec.get_attribute("heading")
            prev_fn = prev_sec.get_attribute("filename")
            link_prev = E("a", ["href", f"{prev_fn}.html"], [T("← "), T(prev_heading)])
            link_home.append_child(link_prev)
            link_home.append_child(T(" — "))

        link_toc = E("a", ["href", "./"], [T("Table of Contents")])
        link_home.append_child(link_toc)

        next_sec = curr_sec_node.next_sibling
        if next_sec and isinstance(next_sec, Element):
            next_heading = next_sec.get_attribute("heading")
            next_fn = next_sec.get_attribute("filename")
            link_home.append_child(T(" — "))
            link_next = E("a", ["href", f"{next_fn}.html"], [T(next_heading), T(" →")])
            link_home.append_child(link_next)

        sec_body.append_child(link_home)

        if big_toc is not None:
            new_toc = big_toc.clone_node(True)
            trim(new_toc, sec_name)
            sec_body.append_child(new_toc)

        # Insert section content
        while curr_sec_node.child_nodes:
            item = curr_sec_node.child_nodes[0]
            item.remove()
            sec_body.append_child(item)

        # Duplicate nav at bottom
        sec_body.append_child(link_home.clone_node(True))

        save_document(
            section_doc,
            os.path.join(base_dir, f"{sec_name}.html"),
            variant=variant,
            in_split=True,
            bikeshed_pass=bikeshed_pass,
        )

        curr_sec_node = curr_sec_node.next_sibling

    return True
