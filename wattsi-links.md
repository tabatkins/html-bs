These are the rules for what makes a valid cross reference, currently:

  1. `<span>`
   * When allowed:
     * Any `<span>` outside of a `<dfn>` (a `<span>` inside a `<dfn>` triggers an error: `<span>` inside
       `<dfn>`).
     * Except spans with class="pubdate", class="pubyear", or class="secno", which are reserved for
       metadata.
     * Must not use lt="" (triggers `<span>` with lt="" found, use data-x="" instead).
   * Cross-reference classification:
     * Explicit (crExplicit): If it has a non-empty data-x attribute, or if it is completely bare
       with no attributes (not Assigned(Element.Attributes)).
     * Implicit (crImplicit): If it has other attributes (e.g., class) but no data-x.
     * Suppressed: If data-x="" (empty), the topic identifier is empty and the span is ignored (used
       internally by Wattsi for MDN/CanIUse widgets to prevent auto-linking).
   * DOM transformation:
     * When resolved to a `<dfn>`, the `<span>` element is replaced in-place by the generated `<a>`
       element (all child nodes and attributes are swapped onto the `<a>`, and the `<span>` is
       destroyed).

  ---

  2. `<code>`
   * When allowed:
     * Any `<code>` element outside of a `<dfn>`.
     * Must not use lt="" (triggers `<code>` with lt="" found, use data-x="" instead).
   * Cross-reference classification:
     * Always treated as explicit (crExplicit), even when omitting data-x (its text content is used
       as the topic).
     * If a `<code>` element is inside `<pre>`, missing `<dfn>` errors are suppressed.
   * DOM transformation:
     * Unlike `<span>`, the `<code>` tag remains; the generated `<a>` element is inserted inside the
       `<code>` element wrapping its contents (`<code><a href="...">...</a></code>`).

  ---

  3. `<i>`
   * When allowed:
     * Only when it explicitly has a data-x attribute (kCrossRefAttribute).
     * Must not be inside a `<dfn>`.
     * Must not have an empty data-x="" (triggers `<i>` with empty data-x="").
   * Cross-reference classification:
     * Explicit (crExplicit).
   * DOM transformation:
     * The `<i>` element remains; the generated `<a>` is inserted inside the `<i>` element (`<i><a href="...">...</a></i>`).

  ---

  4. `<var>`
   * When allowed:
     * Only when it explicitly has a data-x attribute (kCrossRefAttribute).
     * Must not be inside a `<dfn>`.
     * Must not have an empty data-x="" (triggers `<var>` with empty data-x="").
   * Cross-reference classification:
     * Explicit (crExplicit).
   * DOM transformation:
     * The `<var>` element remains; the generated `<a>` is inserted inside the `<var>` element (`<var><a href="...">...</a></var>`).

  ---

  Additional Cross-Reference Rules & Constraints

   * No `<a>` Ancestor: Any cross-reference element nested inside an existing `<a>` is skipped (not
     HasAncestor(..., eA)).
   * Secondary Definitions (subdfn): Any of the allowed crossref elements can carry the subdfn
     attribute to designate that occurrence as a secondary definition site.
   * Other Elements: No other element tags (e.g. `<b>`, `<p>`, `<div>`) can be cross-references. An `<a>`
     element without href is rejected as an error (`<a>` without href found).
  (Note: Bibliographic citations use `<ref>`, which is handled separately from term cross-references
  and links directly to #refs...).