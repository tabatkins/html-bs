from __future__ import annotations

from pathlib import Path
import lxml.html

# Put this at the top of the generated Bikeshed source file
BIKESHED_META = """<pre class=metadata>
Group: WHATWG
H1: HTML
Shortname: html
Text Macro: TWITTER htmlstandard
Text Macro: LATESTRD 2025-01
Abstract: HTML is Bikeshed.
Indent: 1
Markup Shorthands: css off, markdown-block off
Complain About: accidental-2119 off, missing-example-ids off
Include MDN Panels: false
Die On: nothing
Remove Multiple Links: no
</pre>
"""


def convertIdlBlocks(doc: lxml.html.HtmlElement) -> None:
	for code in doc.cssselect("pre > code.idl"):
		pre = code.getparent()
		assert pre is not None
		for k, v in code.attrib.items():
			if k == "class":
				if hasattr(code, "classes") and hasattr(pre, "classes"):
					for cls in code.classes:
						pre.classes.add(cls)
				else:
					preClasses = set(pre.get("class", "").split())
					preClasses.update(v.split())
					pre.set("class", " ".join(sorted(preClasses)))
			elif k not in pre.attrib:
				pre.set(k, v)
		code.drop_tag()


def convertDoc(doc: lxml.html.HtmlElement) -> None:
	convertIdlBlocks(doc)


def run(inputPath: str | Path | None = None, outputPath: str | Path | None = None) -> None:
	currPath = Path(__file__).resolve().parent
	if inputPath is None:
		inputPath = currPath / "html.wattsi"
	if outputPath is None:
		outputPath = currPath / "html.bs"
	inputPath = Path(inputPath)
	outputPath = Path(outputPath)

	with open(inputPath, "r", encoding="utf-8") as fh:
		wattsiSource = fh.read()
	doc = lxml.html.fromstring(wattsiSource)

	convertDoc(doc)

	bsSource = lxml.html.tostring(doc, encoding="unicode")
	with open(outputPath, "w", encoding="utf-8") as fh:
		fh.write(BIKESHED_META + bsSource)


if __name__ == "__main__":
	run()
