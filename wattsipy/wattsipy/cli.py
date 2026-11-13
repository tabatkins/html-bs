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

    with open(source_file, "rb") as f:
        source_data = f.read()

    doc_html = parse_html(source_data)

    os.makedirs(output_directory, exist_ok=True)

    inform("Generating Bikeshed variant...")
    process_document(
        document=doc_html,
        variant="html",
        source_git_sha=source_git_sha,
        output_directory=output_directory,
        bikeshed=True,
    )
    bs_path = os.path.join(output_directory, "html.bs")
    inform(f"Saving {bs_path}")
    save_document(
        doc_html,
        bs_path,
        bikeshed=True,
    )
    return 0
