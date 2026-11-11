# WattsiPy

WattsiPy is a Python port of [Wattsi](https://github.com/whatwg/wattsi), the build tool for generating the [HTML Standard](https://html.spec.whatwg.org/multipage/) from its source.

## Features

- Number the sections and headings
- Create comprehensive and small Tables of Contents (TOC)
- Cross-reference `<span>` and `<code>` to `<dfn>`
- Create cross-reference indices (`xrefs.json`)
- Spec splitting into multipage versions (`multipage-html`, `multipage-dev`) with fragment links (`fragment-links.json`)
- Dev edition search index generation (`search-index.json`)
- Add output for `<wpt>` elements
- Strip unused references and validate missing references

## Usage

```bash
wattsipy [--quiet] [--single-page-only] <source-file> <source-git-sha> <output-directory> <default-or-review> [<highlight-server-url>]
```

Or via python:

```bash
python3 -m wattsipy ...
```
