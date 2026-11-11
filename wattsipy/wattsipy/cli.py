"""Command line interface for WattsiPy."""

from __future__ import annotations
import os
import sys
from typing import Optional

from . import __version__
from .parser import parse_html
from .processor import process_document
from .serializer import save_document
from .splitter import split_specification


def print_usage_and_halt() -> None:
    print("syntax:")
    print("  wattsi [--quiet] [--single-page-only] <source-file> <source-git-sha> <output-directory> <default-or-review> [<highlight-server-url>]")
    print("  wattsi --version")
    sys.exit(1)


def main(argv: Optional[list[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        print("wattsi: missing required arguments")
        print_usage_and_halt()

    quiet = False
    single_page_only = False
    bikeshed_pass = 0
    highlight_server_url = ""

    args: list[str] = []
    for arg in argv:
        if arg == "--help":
            print_usage_and_halt()
        elif arg == "--version":
            print(f"Wattsi {__version__}")
            return 0
        elif arg == "--quiet":
            quiet = True
        elif arg == "--single-page-only":
            single_page_only = True
        elif arg == "--bikeshed":
            if bikeshed_pass == 0:
                bikeshed_pass = 1
        elif arg.startswith("--pass="):
            try:
                bikeshed_pass = int(arg[7:])
            except ValueError:
                bikeshed_pass = 0
        else:
            args.append(arg)

    if len(args) < 4:
        print("wattsi: invalid arguments")
        print_usage_and_halt()

    source_file = args[0]
    source_git_sha = args[1]
    output_directory = args[2]
    build_type = args[3]
    if len(args) > 4:
        if args[4].startswith("http://") or args[4].startswith("https://"):
            highlight_server_url = args[4]
        elif len(args) > 5:
            highlight_server_url = args[5]

    def inform(msg: str) -> None:
        if not quiet:
            print(msg)

    inform("Parsing...")
    if bikeshed_pass > 0:
        inform(f"Bikeshed Pass: {bikeshed_pass}")

    with open(source_file, "rb") as f:
        source_data = f.read()

    doc_html = parse_html(source_data)

    os.makedirs(output_directory, exist_ok=True)

    if build_type == "default":
        doc_dev = doc_html.clone_node(True)
        doc_snap = doc_html.clone_node(True)

        # 1. HTML variant
        inform("Generating HTML variant...")
        big_toc_html = process_document(
            document=doc_html,
            variant="html",
            source_git_sha=source_git_sha,
            output_directory=output_directory,
            bikeshed_pass=bikeshed_pass,
        )
        inform("Saving index-html")
        save_document(
            doc_html,
            os.path.join(output_directory, "index-html"),
            variant="html",
            in_split=False,
            bikeshed_pass=bikeshed_pass,
        )
        if not single_page_only:
            inform("Splitting...")
            split_specification(
                doc_html,
                big_toc_html,
                os.path.join(output_directory, "multipage-html"),
                variant="html",
                bikeshed_pass=bikeshed_pass,
            )

        if single_page_only:
            return 0

        # 2. DEV variant
        inform("Generating DEV variant...")
        big_toc_dev = process_document(
            document=doc_dev,
            variant="dev",
            source_git_sha=source_git_sha,
            output_directory=output_directory,
            bikeshed_pass=bikeshed_pass,
        )
        if not single_page_only:
            inform("Splitting...")
            split_specification(
                doc_dev,
                big_toc_dev,
                os.path.join(output_directory, "multipage-dev"),
                variant="dev",
                bikeshed_pass=bikeshed_pass,
            )

        # 3. SNAP variant
        inform("Generating SNAP variant...")
        big_toc_snap = process_document(
            document=doc_snap,
            variant="snap",
            source_git_sha=source_git_sha,
            output_directory=output_directory,
            bikeshed_pass=bikeshed_pass,
        )
        inform("Saving index-snap")
        save_document(
            doc_snap,
            os.path.join(output_directory, "index-snap"),
            variant="snap",
            in_split=False,
            bikeshed_pass=bikeshed_pass,
        )

    elif build_type == "review":
        inform("Generating REVIEW exclusively...")
        big_toc_review = process_document(
            document=doc_html,
            variant="review",
            source_git_sha=source_git_sha,
            output_directory=output_directory,
            bikeshed_pass=bikeshed_pass,
        )
        inform("Saving index-review")
        save_document(
            doc_html,
            os.path.join(output_directory, "index-review"),
            variant="review",
            in_split=False,
            bikeshed_pass=bikeshed_pass,
        )
    else:
        print(f"Unknown build type: {build_type}")
        sys.exit(1)

    return 0
