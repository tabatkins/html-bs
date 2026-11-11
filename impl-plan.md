Implementation Plan for Wattsi Migration
========================================

The HTML specification (source file located at bs-convert/html.wattsi) is written in Wattsi Markup, a source language similar to HTML that is processed by the WattsiPy project (located in the wattsipy folder) to produce the final specification.

I need to convert this source file to instead be written in Bikeshed Markup, another source language similar to HTMl that is processed by the Bikeshed project (located in the ~/bikeshed folder).

However, I can't just do a straight conversion of the source file, as there are a large number of Pull Requests altering the source that I'll need to modify as well. Instead, I need to write a Python script which will perform the conversion automatically, so it can also be run on the pull request versions to convert them.

Tools
-----

* You have access to the `wattsipy` command and Python library, installed in editable mode from the wattsipy folder here. You can edit the library as needed to achieve your goals. Use this to understand how Wattsi Markup works and how the source file is turned into HTML. You can also use the library directly in the conversion script.
* You have access to the `bikeshed` command and Python library, installed in editable mode from the bikeshed fodler here. You can also edit this library as needed, but should only do so to help extract functionality into a more externally-usable form, for the purpose of helping with the conversion script. For example, it might be helpful to make the code for parsing WebIDL blocks more accessible, so the conversion script can use that information to mark up definitions and links better.

Goal and Rough Plan
-------------------

The goal is a conversion script that will perform a minimal conversion of the input file to make it a valid Bikeshed document, ideally not adjusting linebreaks/indentation/etc so the eventual diff is minimal and only contains necessary changes. The resulting Bikeshed document should use idiomatic Bikeshed patterns, but using only the HTML syntax. (Bikeshed allows and usually encourages using a Markdown-adjacent syntax, but the HTML source is currently using an HTML-adjacent syntax instead, and should retain that.)

The rough plan is:

1. Load the source document in wattsipy.
2. Perform the minimal amount of Wattsi conversions to find definitions, links, and how they interact. Annotate every dfn to clearly indicate its presence, and every autolink to clearly indicate what definition it links to.
3. Modify the document to instead support Bikeshed definition and autolinking conventions: every definition ends up with the same ID and correct Bikeshed definition attributes (`data-dfn-type`, `data-dfn-for` if appropriate, and if necessary, `data-lt`); every autolink becomes an `<a>` using the Bikeshed autolinking attributes (`data-link-type`, `data-link-for` if appropriate, and if necessary, `data-lt`).
4. Serialize the document tree to a new Bikeshed source file that will, when processed by Bikeshed, make every autolink successfully link to the same definition that it did as a Wattsi autolink.
5. Verify that the new Bikeshed source produces the same set of links and definitions that the original Wattsi source did.

