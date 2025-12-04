# T005 - Fix double scrollbar in markdown viewers - COMPLETE

## Context

- Link back to the PRD: [corpus_prd.md](corpus_prd.md)
- Specific sections: Section 5 (scrollbar fix for corpus viewer and inspect_original_md)
- This ticket addresses a UX issue where markdown viewer pages have nested scrolling areas, creating an "annoying double scrollbar" between the browser viewport and the markdown content frame. The fix ensures content scrolls naturally in the browser window rather than in a nested container.

## Outcome

Both the corpus work viewer (`/corpus/{id}`) and the inspect original markdown page (`/conv/{id}/inspect_original_md`) display content that:
1. Scrolls naturally in the browser viewport (no nested scrollbar)
2. Shows content directly below the sticky header
3. Provides a cleaner, more natural scrolling experience
4. Maintains the same functionality (viewing/editing markdown)

## Scope

### In scope:
- Fix layout in `/corpus/[id]/page.tsx` (corpus work viewer)
- Fix layout in `/conv/[id]/inspect_original_md/page.tsx` (inspect original markdown)
- Update MarkdownEditor component usage or container styling
- Ensure header remains sticky/fixed if desired
- Test scrolling behavior across browsers

### Out of scope:
- Changes to MarkdownEditor component internals (unless necessary)
- Other pages that use MarkdownEditor (only these two pages)
- Any functional changes beyond scrolling behavior
- Mobile-specific scrolling optimizations (unless critical)

## Implementation plan

### Frontend

#### 1. Understand the current problem

**Current structure (inspect_original_md):**
```tsx
<div className="flex flex-col h-screen">
  {/* Header - fixed height */}
  <div className="border-b bg-card p-4 flex items-center justify-between">
    {/* ... header content ... */}
  </div>

  {/* Content - takes remaining height */}
  <div className="flex-1 p-6 overflow-hidden flex flex-col">
    <MarkdownEditor
      content={content}
      onChange={setContent}
      viewMode="both"
    />
  </div>
</div>
```

**Problem:**
- Container has `h-screen` (100vh)
- Content area has `flex-1 overflow-hidden`
- This creates a fixed-height container
- MarkdownEditor inside has its own scroll area
- Result: Two scrollbars (outer browser, inner editor)

**Root cause:**
- The `overflow-hidden` on the content div forces MarkdownEditor to handle scrolling
- MarkdownEditor likely has `overflow-auto` or `overflow-scroll` internally
- Better approach: Let browser handle scrolling naturally

#### 2. Proposed solution architecture

**New structure:**
```tsx
<div className="min-h-screen flex flex-col">
  {/* Sticky Header */}
  <div className="sticky top-0 z-10 border-b bg-card p-4 flex items-center justify-between">
    {/* ... header content ... */}
  </div>

  {/* Content - natural height, browser scroll */}
  <div className="flex-1 p-6">
    <MarkdownEditor
      content={content}
      onChange={setContent}
      viewMode="both"
    />
  </div>
</div>
```

**Key changes:**
1. `h-screen` → `min-h-screen` (allows content to exceed viewport)
2. Add `sticky top-0 z-10` to header (keeps it visible while scrolling)
3. Remove `overflow-hidden` from content container
4. Remove `flex flex-col` from content container (not needed)
5. Let browser handle scrolling naturally

#### 3. Fix inspect_original_md page

File: `psychrag_ui/src/app/conv/[id]/inspect_original_md/page.tsx`

**Current code (lines 109-156):**
```tsx
return (
  <div className="flex flex-col h-screen">
    {/* Header */}
    <div className="border-b bg-card p-4 flex items-center justify-between">
      {/* ... */}
    </div>

    {/* Content */}
    <div className="flex-1 p-6 overflow-hidden flex flex-col">
      <MarkdownEditor
        content={content}
        onChange={setContent}
        viewMode="both"
      />
    </div>
  </div>
);
```

**Updated code:**
```tsx
return (
  <div className="min-h-screen flex flex-col">
    {/* Sticky Header */}
    <div className="sticky top-0 z-10 border-b bg-card p-4 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <Button
          onClick={() => router.back()}
          variant="ghost"
          size="sm"
          className="gap-1"
        >
          <ChevronLeft className="h-4 w-4" />
          Back
        </Button>
        <div className="border-l h-8" />
        <div>
          <h1 className="text-xl font-bold">Inspect Original Markdown</h1>
          <p className="text-sm text-muted-foreground max-w-2xl truncate">
            {filename}
          </p>
        </div>
      </div>

      {/* Save Button */}
      <Button
        onClick={handleSave}
        className="gap-1"
        disabled={saving}
      >
        {saving ? (
          <Loader2Icon className="h-4 w-4 animate-spin" />
        ) : (
          <Save className="h-4 w-4" />
        )}
        {saving ? "Saving..." : "Save"}
      </Button>
    </div>

    {/* Content - natural scroll */}
    <div className="p-6">
      <MarkdownEditor
        content={content}
        onChange={setContent}
        viewMode="both"
      />
    </div>
  </div>
);
```

**Changes summary:**
- Container: `h-screen` → `min-h-screen`
- Header: Added `sticky top-0 z-10`
- Content div: Removed `flex-1 overflow-hidden flex flex-col`, kept only `p-6`

#### 4. Fix corpus work viewer page

File: `psychrag_ui/src/app/corpus/[id]/page.tsx`

**Apply the same pattern:**
```tsx
return (
  <div className="min-h-screen flex flex-col">
    {/* Sticky Header */}
    <div className="sticky top-0 z-10 border-b bg-card p-4 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <Button
          onClick={() => router.push("/corpus")}
          variant="ghost"
          size="sm"
          className="gap-1"
        >
          <ChevronLeft className="h-4 w-4" />
          Back
        </Button>

        <div className="border-l h-8" />

        <div>
          <h1 className="text-xl font-bold">Corpus Work</h1>
          <p className="text-sm text-muted-foreground max-w-2xl truncate">
            {workTitle}
          </p>
        </div>
      </div>

      <div className="text-sm text-muted-foreground">
        {filename}
      </div>
    </div>

    {/* Content - natural scroll */}
    <div className="p-6">
      <MarkdownEditor
        content={content}
        onChange={() => {}} // Read-only
        viewMode="both"
      />
    </div>
  </div>
);
```

**Same pattern as inspect_original_md:**
- Sticky header
- Natural content flow
- Browser handles scrolling

#### 5. Check MarkdownEditor component behavior

**Verify MarkdownEditor doesn't force internal scrolling:**

The MarkdownEditor component may have its own height constraints or overflow settings. Check:

```tsx
// In markdown-editor.tsx (if accessible)
// Look for patterns like:
<div className="h-full overflow-auto"> {/* BAD */}
  {/* editor content */}
</div>

// Should be:
<div className="w-full"> {/* GOOD */}
  {/* editor content */}
</div>
```

**If MarkdownEditor has fixed height:**
- Check component props for height-related options
- May need to pass `height="auto"` or similar
- May need to override styles with custom class

**Example override (if needed):**
```tsx
<div className="[&_.markdown-editor]:h-auto [&_.markdown-editor]:overflow-visible">
  <MarkdownEditor
    content={content}
    onChange={setContent}
    viewMode="both"
  />
</div>
```

#### 6. Handle edge cases

**Very short content:**
- Page should still be at least full viewport height (min-h-screen ensures this)
- Header should stay at top
- Content area fills remaining space

**Very long content:**
- Browser scrollbar appears naturally
- Header stays visible at top (sticky)
- User can scroll through entire content
- No nested scrollbar

**Sticky header considerations:**
- Add `bg-card` to prevent content showing through
- Add `z-10` to ensure it's above content
- Consider adding subtle shadow when scrolled:

```tsx
<div className="sticky top-0 z-10 border-b bg-card p-4 shadow-sm">
  {/* header content */}
</div>
```

#### 7. Cross-browser testing

**Test in:**
- Chrome (Windows/Mac)
- Firefox (Windows/Mac)
- Safari (Mac)
- Edge (Windows)

**Verify:**
- Single scrollbar on right side of viewport
- No scrollbar within content area
- Smooth scrolling behavior
- Header stays visible when scrolling
- No layout shift or jumpiness

#### 8. Accessibility considerations

**Keyboard navigation:**
- Scrolling with arrow keys should work naturally
- Page Down/Up should scroll browser, not nested container
- Home/End should go to top/bottom of page

**Screen readers:**
- Natural scroll doesn't affect screen reader behavior
- Sticky header is announced properly
- Content is accessible in reading order

#### 9. Mobile considerations

**On mobile:**
- Sticky header behavior may differ
- iOS Safari has special scrolling behavior
- Android browsers may handle sticky differently

**Test on:**
- iOS Safari (iPhone)
- Chrome Mobile (Android)
- Responsive mode in desktop browser

**Potential mobile adjustments:**
```tsx
<div className="sticky top-0 md:sticky md:top-0 z-10">
  {/* May need different sticky behavior on mobile */}
</div>
```

#### 10. Performance considerations

**Sticky positioning:**
- Modern CSS `position: sticky` is performant
- No JavaScript needed for sticky header
- Browser handles efficiently

**Long documents:**
- Browser's native scroll is optimized
- MarkdownEditor may need virtual scrolling for very large files
- If performance issues arise, investigate MarkdownEditor internals

## Unit tests

### Visual regression tests

Since this is primarily a layout/UX fix, visual regression tests are ideal:

**Using testing library:**
```tsx
describe("Scrolling behavior", () => {
  it("renders without nested scroll containers", () => {
    render(<InspectOriginalMdPage />);

    // Check main container doesn't have overflow-hidden
    const container = screen.getByTestId("page-container");
    expect(container).not.toHaveClass("overflow-hidden");

    // Check content area doesn't have overflow constraints
    const contentArea = screen.getByTestId("content-area");
    expect(contentArea).not.toHaveClass("h-screen");
    expect(contentArea).not.toHaveClass("overflow-auto");
  });

  it("header has sticky positioning", () => {
    render(<InspectOriginalMdPage />);

    const header = screen.getByRole("banner");
    expect(header).toHaveClass("sticky");
    expect(header).toHaveClass("top-0");
  });
});
```

**Manual testing focus:**
- Automated tests can't fully validate scroll behavior
- Prioritize manual testing checklist
- Use visual regression tools (Percy, Chromatic) if available

## Dependencies and sequencing

**Must be completed after:**
- T004 (Corpus work viewer) - need the page to exist before fixing it

**Can be done after:**
- T003 (Corpus listing) - independent work

**Could be done in parallel with:**
- T004 if coordinated (fix can be built into initial implementation)

**No dependencies on:**
- T001 (Backend)
- T002 (Navigation)

**Recommendation:**
- Implement T004 without the scroll fix first (follow existing pattern)
- Then apply T005 to both pages in one go
- This ensures consistent fix across both pages

## Clarifications and assumptions

### Blocking questions:
None - all requirements clarified during planning.

### Assumptions:

1. **Sticky header desired:** Assuming the header should remain visible while scrolling. Alternative would be to let it scroll away, but sticky is better UX for access to Back/Save buttons.

2. **MarkdownEditor height:** Assuming MarkdownEditor component can adapt to container height naturally. If it requires explicit height prop, may need to investigate component internals or pass `height="auto"`.

3. **Browser support:** Assuming modern browsers only (Chrome 56+, Firefox 59+, Safari 13+, Edge 16+). These all support `position: sticky`.

4. **No custom scrollbars:** Assuming we're using native browser scrollbars, not custom styled ones. If custom scrollbars are required, implementation will differ.

5. **Single column layout:** Assuming pages have single-column content. If side-by-side layout (editor + preview) has its own scrolling, may need more investigation.

6. **Z-index management:** Assuming z-10 is sufficient for sticky header. If other page elements have high z-index, may need adjustment.

7. **Content padding:** Keeping p-6 padding around content. This provides breathing room and prevents content from touching viewport edges.

### Non-blocking clarifications:

- **Shadow on scroll:** Could add subtle shadow to header when page is scrolled (enhances visual separation). Not required, but nice enhancement:

```tsx
const [scrolled, setScrolled] = useState(false);

useEffect(() => {
  const handleScroll = () => setScrolled(window.scrollY > 0);
  window.addEventListener("scroll", handleScroll);
  return () => window.removeEventListener("scroll", handleScroll);
}, []);

<div className={`sticky top-0 z-10 border-b bg-card p-4 ${scrolled ? "shadow-md" : ""}`}>
```

- **Smooth scrolling:** Could enable smooth scrolling behavior:
```css
html {
  scroll-behavior: smooth;
}
```

- **Scroll to top button:** For very long documents, could add a "scroll to top" FAB (floating action button).

---

**Before implementing, review the Clarifications and assumptions section. Test the fix in both pages to ensure consistency. If MarkdownEditor has height constraints that conflict with this approach, investigate component props or consider custom styling overrides.**
