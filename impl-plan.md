Implementation Plan for Wattsi Migration
========================================

The HTML specification (source file located at bs-convert/html.wattsi) is written in Wattsi Markup, a source language similar to HTML that is processed by the WattsiPy project (located in the wattsipy folder) to produce the final specification.

I need to convert this source file to instead be written in Bikeshed Markup, another source language similar to HTMl that is processed by the Bikeshed project (located in the ~/bikeshed folder).

However, I can't just do a straight conversion of the source file, as there are a large number of Pull Requests altering the source that I'll need to modify as well. Instead, I need to write a Python script which will perform the conversion automatically, so it can also be run on the pull request versions to convert them.

This script has been started in the bs-convert/convert.py. It is currently at an extremely basic stage, and needs significant work. It takes in the bs-convert/html.wattsi source file, and outputs a Bikeshed source file to bs-convert/html.bs.

While writing this conversion script, you have access to both the `bikeshed` library and the `wattsipy` library for use; you can employ both of these to aid in the conversion.

For the first stage of this project, the conversion script will convert all definitions and all links to the appropriate Bikeshed syntax, and ensure that all the Bikeshed links successfully resolve to the same URL as they do in the Wattsi version.

Handling Definitions
--------------------

If a `<dfn>` is in an IDL block, and Bikeshed would recreate that `<dfn>` with the same ID, drop it from the source and rely on Bikeshed's auto-generation. If it would have a different ID, leave it there.

If a `<dfn>` is outside of an IDL block, make sure it has the appropriate Bikeshed definition attributes: a boolean attribute giving the definition's type (like `<dfn interface>Foo</dfn>`, for a WebIDL interface), and if needed, a `for` attribute listing what definition it's scoped to.

Handling Links
--------------

Any elements that are Wattsi autolinks must be modified into Bikeshed autolinks.
Bikeshed autolinks are always `<a>` elements, with appropriate linking attributes
	(a boolean attribute for the link type, a `for` attribute if needed, an `lt` attribute if needed, etc).
The converted file's Bikeshed autolinks must link to the exact same elements that the Wattsi autolinks did in the source file.