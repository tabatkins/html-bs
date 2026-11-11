from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys
import shutil
from pathlib import Path
from urllib import parse as urlparse
from collections import Counter

import lxml.html

# Ensure local wattsipy and bs-convert modules can be imported
currDir = Path(__file__).resolve().parent
repoRootDir = currDir.parent
if str(repoRootDir / "wattsipy") not in sys.path:
    sys.path.insert(0, str(repoRootDir / "wattsipy"))
if str(currDir) not in sys.path:
    sys.path.insert(0, str(currDir))

import bikeshed as bs
from bikeshed import t

import convert
from wattsipy.cli import main as wattsipy_main


def run(
    wattsiSourcePath: str | Path | None = None,
    skipWattsi: bool = False,
) -> None:
    currPath = Path(__file__).resolve().parent
    repoRoot = currPath.parent
    tempDirPath = prepareTempDir(currPath, ".temp-bs")
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    if wattsiSourcePath is None:
        if (currPath / "html.wattsi").exists():
            wattsiSourcePath = currPath / "html.wattsi"
        elif (repoRoot / "bs-convert" / "html.wattsi").exists():
            wattsiSourcePath = repoRoot / "bs-convert" / "html.wattsi"
        else:
            raise FileNotFoundError("Could not locate html.wattsi source file.")
    wattsiSourcePath = Path(wattsiSourcePath).resolve()

    wattsiOutputDir = tempDirPath / "wattsi-out"
    wattsiOutputDir.mkdir(parents=True, exist_ok=True)
    wattsiProcessedPath = wattsiOutputDir / "index-html"

    if not skipWattsi:
        print(f"Running wattsipy on {wattsiSourcePath}...")
        wattsiArgs = [
            "--single-page-only",
            "--bikeshed",
            "--quiet",
            str(wattsiSourcePath),
            "HEAD",
            str(wattsiOutputDir),
            "default",
        ]
        ret = wattsipy_main(wattsiArgs)
        if ret != 0 or not wattsiProcessedPath.exists():
            raise RuntimeError(f"wattsipy failed with exit code {ret}")
    else:
        if wattsiSourcePath.name == "index-html" or wattsiSourcePath.suffix in (".html", ".htm"):
            wattsiProcessedPath = wattsiSourcePath
        print(f"Skipping wattsipy; using {wattsiProcessedPath}")

    print("Running convert.py transformations on Wattsi output...")
    with open(wattsiProcessedPath, "r", encoding="utf-8") as fh:
        wattsiHtml = fh.read()

    docElement = lxml.html.fromstring(wattsiHtml)
    convert.convertDoc(docElement)

    bsSource = lxml.html.tostring(docElement, encoding="unicode")
    inputPath = tempDirPath / "bikeshed-input.html"
    with open(inputPath, "w", encoding="utf-8") as fh:
        fh.write(convert.BIKESHED_META + "\n" + bsSource)

    outputPath = tempDirPath / "bikeshed-pass1.html"
    linkErrorLogPath = tempDirPath / f"link-errors-{timestamp}.json"

    print("Running Bikeshed...")
    with bs.messages.messagesSilent() as _:
        doc = bs.Spec(str(inputPath))
        if not doc.valid:
            bs.messages.die("Spec is in an invalid state; exitting.")
            return
        doc.assembleDocument()
        prepareLinkErrorDetection(doc)
        doc.processDocument()
        verifyLinks(doc, logPath=linkErrorLogPath)
        doc.finish(outputFilename=str(outputPath))

    print(f"Bikeshed output in {outputPath.relative_to(currPath)}")
    print(f"Xref errors log in {linkErrorLogPath.relative_to(currPath)}")


def prepareTempDir(parentFolder=None, folderName="temp"):
    """
    Creates a folder named `folderName` in the current working directory.
    If it already exists, its contents are completely wiped clean.
    """
    if parentFolder is None:
        parentFolder = Path.cwd()

    temp_path = parentFolder / folderName

    if temp_path.exists():
        for item in temp_path.iterdir():
            if item.is_file() or item.is_symlink():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
    else:
        temp_path.mkdir(parents=True, exist_ok=True)

    return temp_path


def prepareLinkErrorDetection(doc: t.SpecT) -> None:
    # Elements with data-x are wattsi definitions;
    # elements with data-wattsi-x or data-x-lt are wattsi links.
    # Find all elements with data-wattsi-x or data-x-lt.
    # If they're not links, find the link child and move the data-wattsi-x to it,
    # and move the wattsi-set href to data-wattsi-href for comparison.
    # If they don't have a link child, set data-wattsi-unlinked
    for el in bs.h.findAll("[data-wattsi-x], [data-x-lt]", doc):
        xLt = el.get("data-wattsi-x") or el.get("data-x-lt")
        assert xLt is not None

        # Tracking vector links technically use data-x, but end up with empty linktext
        # Just skip them, they're noise
        if xLt == "tracking vector":
            continue

        aEl: t.ElementT | None
        if el.tag == "a":
            aEl = el
            aEl.set("data-wattsi-x", xLt)
        elif (aEl := bs.h.find("a", el)) is not None:
            aEl.set("data-wattsi-x", xLt)
            if "data-wattsi-x" in el.attrib:
                del el.attrib["data-wattsi-x"]
            if "data-x-lt" in el.attrib:
                del el.attrib["data-x-lt"]
        else:
            # No link anywhere, so Bikeshed won't autolink this at all.
            # Flag it for error logging.
            el.set("data-wattsi-unlinked", "")
            continue

        # If anything ends up with empty linking text, Bikeshed gets pretty unhappy.
        # Flag it for error logging.
        content = bs.h.textContent(aEl)
        if not content:
            el.set("data-wattsi-emptylinktext", "")
            continue

        # Otherwise, shift their href out so Bikeshed will try to autolink them again,
        # and I can compare to Wattsi's results.
        href = aEl.get("href")
        if href:
            aEl.set("data-wattsi-href", href)
            del aEl.attrib["href"]

        aEl.set("outerhtml", bs.h.outerHTML(aEl))


def normalizeUrl(url: str, base: str = "https://html.spec.whatwg.org/") -> str:
    # Turn all local links into absolute URLs to the single-page spec.
    if url.startswith("#"):
        return base + url
    joined = urlparse.urljoin(base, url)
    if joined.startswith("https://html.spec.whatwg.org/multipage/"):
        parsed = urlparse.urlparse(joined)
        return "https://html.spec.whatwg.org/#" + parsed.fragment
    return joined


def getLine(el):
    return bs.h.approximateLineNumber(el)


def getSuggestion(targetEl: t.ElementT) -> str:
    dfnFor = targetEl.get("data-dfn-for")
    lt = bs.h.textContent(targetEl).strip()
    parts = []
    if dfnFor:
        parts.append(f'for="{dfnFor}"')
    parts.append(f'lt="{lt}"')
    return " ".join(parts)


def verifyLinks(doc: t.SpecT, logPath=Path) -> None:
    # Go over every wattsi autolink and check if Bikeshed linked them the same way.

    # Categorize all dfns by their data-x
    dfnFromDataX = {}
    allDataX = set()
    for el in bs.h.findAll("[data-x]", doc):
        val = el.get("data-x")
        if val:
            dfnFromDataX[val] = el
            allDataX.add(val)
    allDataWattsiX = set()
    for el in bs.h.findAll("[data-wattsi-x]", doc):
        val = el.get("data-wattsi-x", "")
        allDataWattsiX.add(val)

    elFromId = bs.h.collectIds(doc.document)
    usedDataX = set()
    errors = []

    wattsiLinks = list(bs.h.findAll("[data-wattsi-href]", doc))
    print(f"{len(wattsiLinks)=}")
    successfulLinks = 0
    for el in wattsiLinks:
        # Links copied into the ToC will get turned into spans by Bikeshed
        if bs.h.hasAncestor(el, lambda x: x.get("id") == "toc"):
            continue

        line = getLine(el)

        wattsiHref = el.get("data-wattsi-href")
        assert wattsiHref is not None
        xLt = el.get("data-wattsi-x")
        assert xLt is not None
        wattsiDfn = dfnFromDataX.get(xLt)
        if wattsiDfn is None:
            errors.append({
                "line": line,
                "type": "broken-wattsi-link",
                "msg": f"(x={xLt}) No dfn with a matching data-x exists in the document",
            })
            continue

        normalizedOrig = normalizeUrl(wattsiHref)

        # Bikeshed failed the autolink
        if bs.h.hasClass(doc, el, "link-error"):
            errTitle = el.get("title") or ""
            errors.append({
                "line": line,
                "type": "bikeshed-link-error",
                "msg": f"(x={xLt}) A Wattsi link triggered a link error in Bikeshed",
                "wattsi-href": wattsiHref,
                "link-error": errTitle,
            })
            continue

        # Bikeshed didn't even *try* to autolink for some reason
        if not el.get("href") and not bs.h.hasClass(doc, el, "link-error"):
            line = getLine(el)
            errors.append({
                "line": line,
                "type": "unprocessed",
                "msg": f"(x={xLt}) Wattsi link wasn't even attempted by Bikeshed.",
                "wattsi-href": wattsiHref,
                "wattsi-outer-html": printWattsiEl(el),
                "bikeshed-outer-html": printEl(el),
            })
            continue

        resolvedHref = el.get("href")
        assert resolvedHref is not None
        # Bikeshed linked to a local dfn...
        if resolvedHref.startswith("#"):
            # Find the element it linked to...
            targetId = resolvedHref[1:]
            bikeshedDfn = elFromId.get(targetId)
            # And the element
            if bikeshedDfn is not None:
                targetDataX = bikeshedDfn.get("data-x")
                if targetDataX == xLt:
                    # Success! Bikeshed and Wattsi agreed!
                    usedDataX.add(xLt)
                    successfulLinks += 1
                    continue
                elif targetDataX:
                    # Bikeshed linked to a different Wattsi dfn
                    errors.append({
                        "line": line,
                        "type": "different-wattsi-dfn",
                        "msg": f"(x={xLt}) Bikeshed instead linked to {resolvedHref} (x={targetDataX})",
                        "link-el": printEl(el),
                        "bikeshed-dfn": printEl(bikeshedDfn),
                        "bikeshed-line": getLine(bikeshedDfn),
                        "wattsi-dfn": printEl(wattsiDfn),
                        "wattsi-line": getLine(wattsiDfn),
                    })
                    continue
                else:
                    # Bikeshed linked to something Wattsi doesn't see as a dfn at all
                    errors.append({
                        "line": line,
                        "type": "not-wattsi-dfn",
                        "msg": f"(x={xLt}) Bikeshed instead linked to {resolvedHref} (no data-x at all)",
                        "link-el": printEl(el),
                        "bikeshed-dfn": printEl(bikeshedDfn),
                        "bikeshed-line": getLine(bikeshedDfn),
                        "wattsi-dfn": printEl(wattsiDfn),
                        "wattsi-line": getLine(wattsiDfn),
                    })
                    continue
            else:
                # Bikeshed screwed up, the linked ID doesn't show up in the doc
                # Shouldn't be possible without a screwed up anchors block,
                # just checking in case...
                errors.append({
                    "line": line,
                    "type": "broken-link",
                    "msg": f"Resolved target #{targetId} not found in document for link '{xLt}'",
                })
                continue

        normalizedResolved = normalizeUrl(resolvedHref)
        # Bikeshed linked to a non-local dfn, different from Wattsi
        if normalizedOrig != normalizedResolved:
            errors.append({
                "line": line,
                "type": "external-mismatch",
                "msg": f"(x={xLt}) Bikeshed linked to different external than Wattsi.",
                "wattsi-href": wattsiHref,
                "bikeshed-href": resolvedHref,
                "link-el": printEl(el),
            })
            continue
        else:
            # Success! Bikeshed and Wattsi agreed on external link!
            usedDataX.add(xLt)
            successfulLinks += 1
            continue

    # Log elements with data-wattsi-x that weren't <a>s
    for el in bs.h.findAll("[data-wattsi-unlinked]", doc):
        line = getLine(el)
        xLt = el.get("data-wattsi-x") or el.get("data-x-lt")
        errors.append({
            "line": line,
            "type": "unlinked-source",
            "msg": f"(x={xLt}) Element isn't an <a> or has an <a> child/descendant",
            "link-el": printEl(el),
        })

    for el in bs.h.findAll("[data-wattsi-emptylinktext]", doc):
        line = getLine(el)
        errors.append({
            "line": line,
            "type": "empty-link-text",
            "msg": "Element has no link text at all.",
        })

    # Log unused data-x
    unusedDataX = (allDataX & allDataWattsiX) - usedDataX
    for x in sorted(unusedDataX):
        el = dfnFromDataX[x]
        line = getLine(el)
        errors.append({
            "line": line,
            "type": "unused-dfn",
            "msg": f"(x={x}) Wattsi dfn was never linked to",
        })

    try:
        errors.sort(key=lambda x: (x["type"], x.get("line") or 0, x.get("msg") or ""))
    except Exception:
        pass

    # Collect some stats
    typeCounter = Counter(x["type"] for x in errors)
    typeCounter["successful-links"] = successfulLinks
    errors.insert(0, dict(typeCounter))

    # Write to log file
    with open(logPath, "w", encoding="utf-8") as fh:
        json.dump(errors, fh, indent=2, ensure_ascii=False)

    print("Link verification results summary:")
    for k, v in typeCounter.items():
        print(f"  {k}: {v}")


def printEl(el: t.ElementT) -> str:
    naive = bs.h.outerHTML(el)
    # Remove the 'outerhtml' attribute that I use to smuggle in the original Wattsi version of the element
    text = re.sub(r' outerhtml="[^"]*"', "", naive)
    return text


def printWattsiEl(el: t.ElementT) -> str:
    return el.get("outerhtml", "")


def cli(argv=None) -> None:
    argparser = argparse.ArgumentParser(
        description="Checks that Bikeshed and Wattsi process autolinks in the same way, and logs discrepancies."
    )
    argparser.add_argument(
        "infile",
        nargs="?",
        help="Path to the Wattsi source file (or processed Wattsi output HTML)",
    )
    argparser.add_argument(
        "--mdn",
        dest="mdn_path",
        help="Path to mdnspeclinks.json",
    )
    argparser.add_argument(
        "--skip-wattsi",
        action="store_true",
        help="Skip running wattsipy; assume infile is already processed Wattsi HTML",
    )

    options = argparser.parse_args(argv)
    run(options.infile, skipWattsi=options.skip_wattsi)


if __name__ == "__main__":
    cli()
