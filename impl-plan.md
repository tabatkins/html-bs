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
2. Perform the minimal amount of Wattsi conversions to find definitions, links, and how they interact. Ensure every definition has a unique `data-x` value to identify it, and annotate every autolink with a `data-link-x` attribute with a value matching the `data-x` of its corresponding definition, so you can later verify which link goes where.
3. Modify the document to instead support Bikeshed definition and autolinking conventions: every definition ends up with the same ID and correct Bikeshed definition attributes; every autolink becomes an `<a>` using the Bikeshed autolinking attributes.
4. Serialize the document tree to a new Bikeshed source file that will, when processed by Bikeshed, make every autolink successfully link to the same definition that it did as a Wattsi autolink.
5. Verify that the new Bikeshed source produces the same set of links and definitions that the original Wattsi source did.

## Necessary Wattsipy Modifications

* Remove or disable parts of Wattsipy that are already handled by Bikeshed, such as ToC generation, index generation, etc.
* Keep anything related to linking, of course, as that's the big thing we'll need to rely on to make the conversion script work.
* We only want to focus on generating the singlepage version for now. Do not generate additional formats, such as multipage, dev, or snapshot. Where there are attributes and other indicators in the document intended to help *guide* the generation of those other formats, such as `w-nodev`/etc, leave those alone, as I will need them later.
* Wattsipy currently aggressively normalizes whitespace/etc. Remove that functionality; instead, *preserve* whitespace and linebreaks as much as reasonably possible. Ideally, the diff between the original source and the converted Bikeshed source should only show meaningful edits, not a ton of whitespace edits marking every line. This is not a strict requirement if it conflicts with other goals, however.

## Output Document Structure

* The output of the conversion script should be a Bikeshed source file, starting with a `<pre class=metadata>` block, possibly followed by `<pre class=anchors>`/etc as necessary, then the contents of the document.
* The contents should be restricted to just the contents of the `<body>` element. The `<head>` and surrounding data will be handled by Bikeshed's boilerplate system. (I do not yet have HTML boilerplates; they will be added later.)

## Definition & Autolink Markup Conventions

* Attribute syntax:
	* Leave the `data-x` and `data-link-x` attributes on the definitions and autolinks, so they can be double-checked to link the same way in Bikeshed.
	* Use the shorthand Bikeshed definition/autolinking attributes (`<dfn interface>` rather than `<dfn data-dfn-type=interface>`, for example).
	* Some definitions already have Bikeshed linking attributes; trust that they are correct and leave those as they are.
	* Some definitions will already use Bikeshed's shorthand definition attributes (e.g., `<dfn element>`, `<dfn attribute for="HTMLAnchorElement">`, `export`, `noexport`). Leave those as-is and assume they're correct. Add attributes to those definitions that don't already have them.
	* Bikeshed exports non-dfn types by default and unexports dfn types by default. When necessary, add `export` or `noexport` to match what Wattsi currently exports, if that would differ under Bikeshed.
* How far to go inferring type / for vs. using Wattsi's data-x topic as data-lt:
	* The most part of the conversion is keeping the IDs identical between Wattsi and Bikeshed, so existing links continue to work, and then getting the type (and for) values correct, so the definitions play correctly in the wider linking ecosystem beyond this specification.
	* When at all possible, omit `lt` altogether and rely on the text content. Use `lt` to put the term into the canonical form (for example, `Multiple <dfn lt=retry>retries</dfn>`). If *absolutely necessary*, reuse the existing `data-x` value as `lt` to ensure the linking works correctly, but flag these for manual review.
* For currently untyped `<dfn>`s outside IDL blocks (like `attr-*-*`, `dom-*-*`, `event-*`, `concept-*`), infer dfn-type and dfn-for from naming patterns/context and from WebIDL blocks. If it's unclear, leave it as `dfn` type with `lt` set to the Wattsi topic value, and flag it for manual review.


## WebIDL Blocks (`<pre><code class="idl">`)

* In html.wattsi, IDL blocks are written as `<pre><code class="idl">`. Convert these to `<pre class=idl>`, so Bikeshed will pick them up as IDL blocks.
* In html.wattsi, IDL blocks often have manual `<dfn>` tags inside. Leave them as-is; they might not be necessary, but Bikeshed will merge them with the parser-created `<dfn>` elements automatically, including reusing the manually-specified ID.
* IDL blocks sometimes also have `<span>` (autolink) tags inside. Leave these in at first, so you can track what definition they link to, and verify that Bikeshed also generates a link for that term (which will be wrapped around the `<span>` after Bikeshed parsing), and that it links to the same `<dfn>` as Wattsi. Then, if it's correct, the conversion script should remove it from the source.

## Special Wattsi Definition & Linking Cases

* External / Deferring Definitions (`<dfn data-x-href="...">`, ~1,696 instances):
	* Wattsi defines external terms via local `<dfn data-x="..." data-x-href="https://...">` elements; references to that topic link to the external data-x-href URL (with data-x-internal).
	* Convert these "definitions" to just a Bikeshed autolink to the external term. Keep the data-x-href attribute around initially, so you can verify that the Bikeshed autolink links to the same term, as do all the autolinks that originally pointed to this "definition".
	* You can examine the Bikeshed linking database via the `bikeshed refs` command or by invoking the Bikeshed module's ref functions directly, to see how to correctly link to the external term. If you can't figure out how to correctly link to it, instead generate an entry in a `<pre class=anchors>` block creating a manual anchor for the term, using the correct Bikeshed metadata for the term, to at least ensure that all the autolinks still go to the correct definition. I can manually review these later.

* `<dfn>` inside Headings (`<h2>`–`<h6>`):
	* When a definition is inside a heading (e.g., `<h4>The <dfn element><code>a</code></dfn> element</h4>`) Wattsi puts the ID (`id="the-a-element"`) on the `<h4>` heading instead of the `<dfn>`, and links to #the-a-element.
	* In every instance of this, the `<dfn>` is alone, so instead, *remove* the `<dfn>` element and instead put the Bikeshed definition attributes on the heading tag, which is allowed. So the above example should be `<h4 id=the-a-element element lt=a>The <code>a</code> element</h4>`. (Recall that headings serving as definition sources *must* use `lt` to identify themselves.) This ensures that autolinks will still go to the same place in both Wattsi and Bikeshed.
* Secondary Definitions (subdfn, ~657 instances):
      • Elements with subdfn should be converted into normal `<a>` autolinks, with their ID preserved if specified. Remove the `subdfn` attribute, but replace it with `bs-subdfn=[id of the primary definition]`, so I can ensure they still get correctly transformed into definitions when building the dev version later.
 Bibliography (<ref>FOO</ref> and <dl id="ref-list">, ~720 instances):
 	* Convert these to Bikeshed's `[[FOO]]` syntax. Query Bikeshed to ensure that they link to the same document. If the document they link to doesn't exist in Bikeshed's linking database, add an appropriate entry to a `<pre class=biblio>` block at the start of the document.


## Document Variants & Non-Link Wattsi Features

* Preserve the attributes that control variant generation types, such as w-nodev, w-dev, w-nohtml, w-nospa, w-noreview, and w-nosplit.
* The handling of subdfn is specified above.
* Reduce the source to just the contents of the `<body>` element. Remove the `<header>` element. Remove toc and smalltoc comments. All of these will be handled by Bikeshed boilerplate, later.
* If there is a Bikeshed equivalent, convert Watti-specific comments/elements to Bikeshed. (<!-- NON-NORMATIVE SECTION -->, <!--INSERT TRACKING-->, <span class="pubdate">, <a href="/commit-snapshots/[SHA]">, <wpt>) If not, leave them untouched.


## Minimal-Diff Serialization Requirement

* Currently, the Wattsi parser strips HTML comments, deletes whitespace, omits optional tags, etc.
* Instead, modify wattsipy's processor/serializer so DOM serialization preserves comments, whitespace text nodes, explicit closing tags, and attribute quotes. (It's okay that html5lib still normalizes multi-line tag attributes.)


## File Locations & Verification Criteria

* Place the conversion script and output file in the bs-convert folder.
* To verify that Bikeshed will link things the same as Wattsi did, build the output document with Bikeshed, and then verify that every element with `data-link-x` is a successful Bikeshed autolink, and that the Bikeshed autolinker set `href` to the ID of the matching `data-x` definition.
