from __future__ import annotations

import sys
from pathlib import Path

# Ensure local wattsipy can be imported
currPath = Path(__file__).resolve().parent
repoRoot = currPath.parent
if str(repoRoot / "wattsipy") not in sys.path:
	sys.path.insert(0, str(repoRoot / "wattsipy"))

from wattsipy.parser import parse_html
from wattsipy.processor import process_document
from wattsipy.serializer import save_bikeshed, BIKESHED_META


def convertDoc(doc) -> None:
	process_document(
		document=doc,
		variant="html",
		source_git_sha="HEAD",
		output_directory="",
		bikeshed=True,
	)


def run(inputPath: str | Path | None = None, outputPath: str | Path | None = None) -> None:
	currPath = Path(__file__).resolve().parent
	if inputPath is None:
		inputPath = currPath / "html.wattsi"
	if outputPath is None:
		outputPath = currPath / "html.bs"
	inputPath = Path(inputPath)
	outputPath = Path(outputPath)

	with open(inputPath, "rb") as fh:
		wattsiSource = fh.read()
	doc = parse_html(wattsiSource)

	convertDoc(doc)

	save_bikeshed(doc, str(outputPath), body_only=True, metadata=BIKESHED_META)


if __name__ == "__main__":
	run()
