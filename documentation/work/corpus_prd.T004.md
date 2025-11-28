# T004 - Corpus work viewer with read-only sanitized markdown

## Context

- Link back to the PRD: [corpus_prd.md](corpus_prd.md)
- Specific sections: Section 5 (Work Examine page)
- This ticket implements the individual work viewer page that displays sanitized markdown content in read-only mode. This allows users to review the processed content that will be used for RAG operations.

## Outcome

Users can view any corpus work's sanitized markdown at `/corpus/{id}` where:
1. The full sanitized markdown content is displayed using the MarkdownEditor component
2. The editor is in read-only mode (no editing allowed)
3. The page shows work metadata (title, filename) in the header
4. Users can navigate back to the corpus listing page

## Scope

### In scope:
- Create `/corpus/[id]` dynamic route and page component
- Fetch work details and sanitized content from backend API
- Display markdown using MarkdownEditor component in read-only mode
- Show work metadata in page header
- Add loading, error, and navigation states
- Style consistently with inspect_original_md page pattern

### Out of scope:
- Edit/save functionality (this is read-only)
- Double scrollbar fix (handled in T005)
- Backend API implementation (handled in T001)
- Corpus listing page (handled in T003)
- Any operations that modify the work or content

## Implementation plan

### Frontend

#### 1. Create dynamic route structure

Create directory: `psychrag_ui/src/app/corpus/[id]/`
Create file: `psychrag_ui/src/app/corpus/[id]/page.tsx`

**File structure:**
```
psychrag_ui/src/app/
├── corpus/
│   ├── page.tsx              # T003: Listing page
│   └── [id]/
│       └── page.tsx          # T004: This file (work viewer)
```

#### 2. Create page component

File: `psychrag_ui/src/app/corpus/[id]/page.tsx`

**Component structure based on inspect_original_md pattern:**

```tsx
"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import {
  AlertCircle,
  ChevronLeft,
  Loader2Icon,
} from "lucide-react";
import { MarkdownEditor } from "@/components/markdown-editor";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface WorkContentResponse {
  content: string;
  filename: string;
  work_id: number;
  work_title: string;
}

export default function CorpusWorkViewerPage() {
  const params = useParams();
  const router = useRouter();
  const workId = params.id as string;

  const [content, setContent] = useState<string>("");
  const [filename, setFilename] = useState<string>("");
  const [workTitle, setWorkTitle] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Component implementation...
}
```

**Key differences from inspect_original_md:**
1. No `onChange` handler for MarkdownEditor (read-only)
2. No Save button in header
3. Fetches from `/corpus/work/{id}/content` instead of conversion endpoint
4. Back button goes to `/corpus` instead of browser back

#### 3. Implement data fetching

```tsx
useEffect(() => {
  fetchContent();
}, [workId]);

const fetchContent = async () => {
  try {
    setLoading(true);
    setError(null);

    const response = await fetch(`${API_BASE_URL}/corpus/work/${workId}/content`);

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error("Work not found or sanitized content not available.");
      }
      throw new Error(`Failed to load content: ${response.statusText}`);
    }

    const data: WorkContentResponse = await response.json();
    setContent(data.content);
    setFilename(data.filename);
    setWorkTitle(data.work_title);

  } catch (err) {
    setError(err instanceof Error ? err.message : "Failed to load content");
  } finally {
    setLoading(false);
  }
};
```

**Error handling considerations:**
- 404: Work doesn't exist or isn't a corpus work
- 500: File read error on server
- Network errors: Timeout or connection issues

#### 4. Implement loading state

```tsx
if (loading) {
  return (
    <div className="flex items-center justify-center h-screen">
      <Loader2Icon className="h-8 w-8 animate-spin text-muted-foreground" />
    </div>
  );
}
```

**Full-screen loading:** Matches inspect_original_md pattern for consistency.

#### 5. Implement error state

```tsx
if (error) {
  return (
    <div className="flex items-center justify-center h-screen">
      <div className="text-center space-y-4">
        <AlertCircle className="h-12 w-12 text-destructive mx-auto" />
        <p className="text-destructive">{error}</p>
        <div className="flex gap-3 justify-center">
          <Button onClick={fetchContent}>Retry</Button>
          <Button variant="outline" onClick={() => router.push("/corpus")}>
            Back to Corpus
          </Button>
        </div>
      </div>
    </div>
  );
}
```

**Error features:**
- Retry button re-attempts fetch
- Back to Corpus button provides escape route
- Clear error message

#### 6. Implement page header

```tsx
<div className="border-b bg-card p-4 flex items-center justify-between">
  <div className="flex items-center gap-3">
    {/* Back button */}
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

  {/* Right side: work metadata or actions */}
  <div className="text-sm text-muted-foreground">
    {filename}
  </div>
</div>
```

**Header features:**
- Back button navigates to `/corpus` (not browser back)
- Work title displayed as subtitle
- Filename shown on right side
- Consistent with inspect_original_md layout

#### 7. Implement markdown viewer

```tsx
return (
  <div className="flex flex-col h-screen">
    {/* Header */}
    {/* ... header implementation ... */}

    {/* Content */}
    <div className="flex-1 p-6 overflow-hidden flex flex-col">
      <MarkdownEditor
        content={content}
        onChange={() => {}} // No-op: read-only
        viewMode="both"
      />
    </div>
  </div>
);
```

**Read-only implementation:**
- Pass empty function to `onChange` (MarkdownEditor requires it)
- Alternative: Check if MarkdownEditor has a `readOnly` prop
- `viewMode="both"` shows editor and preview side-by-side

**Layout notes:**
- `flex flex-col h-screen` ensures full-height layout
- `overflow-hidden` on container, let MarkdownEditor handle scroll
- `p-6` adds padding around editor

#### 8. Check MarkdownEditor component interface

Before implementation, verify the MarkdownEditor component:

```tsx
// Check if component has these props:
interface MarkdownEditorProps {
  content: string;
  onChange: (value: string) => void;
  viewMode?: "edit" | "preview" | "both";
  readOnly?: boolean; // Check if this exists
}
```

**If `readOnly` prop exists:**
```tsx
<MarkdownEditor
  content={content}
  onChange={() => {}}
  viewMode="both"
  readOnly={true}
/>
```

**If no `readOnly` prop:**
- Use `viewMode="preview"` to show only rendered view
- OR pass no-op onChange and rely on component's own behavior
- Verify component doesn't allow editing in practice

#### 9. Navigation and routing

**Back button behavior:**
```tsx
const handleBack = () => {
  router.push("/corpus");
};

// In header:
<Button onClick={handleBack} variant="ghost" size="sm" className="gap-1">
  <ChevronLeft className="h-4 w-4" />
  Back
</Button>
```

**Why not router.back():**
- User might arrive from different sources (direct link, bookmark)
- Explicit navigation to `/corpus` provides consistent UX
- Matches pattern from other viewer pages

#### 10. Responsive design

**Considerations:**
- Header should stack on mobile (title over filename)
- MarkdownEditor should handle its own responsive behavior
- Ensure page doesn't break on narrow screens

```tsx
<div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
  <div className="flex items-center gap-3">
    {/* Back and title */}
  </div>
  <div className="text-sm text-muted-foreground">
    {filename}
  </div>
</div>
```

#### 11. Accessibility

- Semantic heading hierarchy (h1 for page title)
- Loading/error states announced to screen readers
- Keyboard navigation works (back button, etc.)
- MarkdownEditor itself should be accessible
- Consider adding skip link for keyboard users

#### 12. Performance considerations

**Content size:**
- Sanitized markdown files can be large (100KB+)
- Content is fetched once on mount
- No need for streaming or chunking initially
- If performance issues arise, consider:
  - Virtual scrolling in MarkdownEditor
  - Lazy loading of rendered preview
  - Server-side pagination for very large files

## Unit tests

Create `tests/unit/test_corpus_work_viewer.tsx`:

### Test framework
- React Testing Library with Jest
- Mock Next.js router and params
- Mock fetch API
- Mock MarkdownEditor component

### Specific test cases

**Page rendering:**
- Renders loading state initially
- Fetches content from correct API endpoint
- Displays work title in header
- Displays filename in header
- Renders MarkdownEditor with content

**Data fetching:**
- Fetches from `/corpus/work/{workId}/content` on mount
- Parses work ID from route params correctly
- Handles successful response
- Handles 404 response
- Handles 500 response
- Handles network errors

**MarkdownEditor integration:**
- Passes content prop to MarkdownEditor
- Sets viewMode to "both" or appropriate mode
- Passes read-only props correctly
- onChange is no-op (doesn't modify content)

**Navigation:**
- Back button navigates to `/corpus`
- Back button in error state navigates to `/corpus`
- Retry button in error state re-fetches content

**Error handling:**
- Displays error message when fetch fails
- Shows Retry and Back buttons in error state
- Error message is user-friendly

### Edge cases
- Invalid work ID (non-numeric)
- Work exists but is not a corpus work (should 404)
- Very large content (100KB+ markdown)
- Content with special characters (Unicode, emojis)
- Empty content (edge case, should still render)

## Manual test plan (acceptance criteria)

### Test Case 1: View corpus work content
**Preconditions:** Database has corpus work with ID 5
**Steps:**
1. Navigate to `/corpus`
2. Click on work with ID 5
3. Observe page load
4. Check header
5. Check markdown content display

**Expected result:**
- Browser navigates to `/corpus/5`
- Loading spinner shows briefly
- Page header shows work title and filename
- Markdown content displays in editor (both edit and preview panes)
- Content is read-only (cannot edit)

### Test Case 2: Read-only enforcement
**Preconditions:** Viewing a corpus work
**Steps:**
1. Navigate to `/corpus/5`
2. Wait for content to load
3. Try to click in the markdown editor pane
4. Try to type in the editor
5. Look for Save button

**Expected result:**
- Editor does not respond to typing OR shows preview-only mode
- No Save button in header (unlike inspect_original_md)
- Content cannot be modified
- User understands this is read-only

### Test Case 3: Back navigation
**Preconditions:** Viewing a corpus work
**Steps:**
1. Navigate to `/corpus/5`
2. Wait for content to load
3. Click "Back" button in header

**Expected result:**
- Browser navigates to `/corpus`
- Corpus listing page displays
- User can navigate to different work

### Test Case 4: Direct navigation via URL
**Preconditions:** Database has corpus work with ID 5
**Steps:**
1. Enter `/corpus/5` directly in browser address bar
2. Observe page load

**Expected result:**
- Page loads correctly
- Content displays
- No errors from missing navigation state

### Test Case 5: Invalid work ID
**Preconditions:** Database has no work with ID 9999
**Steps:**
1. Navigate to `/corpus/9999`
2. Observe response

**Expected result:**
- Error state displays
- Error message: "Work not found or sanitized content not available."
- Retry and "Back to Corpus" buttons available
- Clicking Back navigates to `/corpus`

### Test Case 6: Non-corpus work
**Preconditions:** Database has work ID 3 with incomplete chunking
**Steps:**
1. Navigate to `/corpus/3`
2. Observe response

**Expected result:**
- Error state displays (likely 404 or 400 from backend)
- Error message indicates work not available
- User can navigate back to corpus listing

### Test Case 7: Large content file
**Preconditions:** Corpus work with 100KB+ sanitized markdown
**Steps:**
1. Navigate to the large corpus work
2. Observe loading time
3. Scroll through content
4. Check responsiveness

**Expected result:**
- Page loads within reasonable time (< 5 seconds)
- Scrolling is smooth
- MarkdownEditor handles large content gracefully
- No browser freezing or lag

### Test Case 8: Content with special formatting
**Preconditions:** Corpus work with complex markdown (tables, code blocks, images)
**Steps:**
1. Navigate to work with complex markdown
2. Observe rendered preview pane
3. Check editor pane

**Expected result:**
- Tables render correctly
- Code blocks have syntax highlighting
- Images display (if paths are correct)
- Complex formatting doesn't break layout

### Test Case 9: Network error handling
**Preconditions:** Backend API is unreachable or returns 500
**Steps:**
1. Navigate to `/corpus/5`
2. Observe error state
3. Click "Retry" button
4. If API is back online, observe success

**Expected result:**
- Error message displays with details
- Retry button triggers new fetch attempt
- If retry succeeds, content displays
- If retry fails, error persists

### Test Case 10: Mobile responsive view
**Preconditions:** Viewing corpus work on mobile device or narrow browser
**Steps:**
1. Navigate to `/corpus/5` on mobile
2. Observe header layout
3. Check MarkdownEditor layout

**Expected result:**
- Header elements stack vertically on mobile
- Back button is accessible
- MarkdownEditor adapts to narrow screen (may show single pane)
- No horizontal scrolling (unless needed for content)

## Dependencies and sequencing

**Must be completed after:**
- T001 (Backend API) - requires `/corpus/work/{id}/content` endpoint
- T003 (Corpus listing page) - users navigate from listing to this page

**Must be completed before:**
- T005 (Scrollbar fix) - this ticket provides the page to fix

**Independent of:**
- T002 (Navigation) - can work without nav changes

**Integration considerations:**
- Relies on MarkdownEditor component being available
- Uses same component as inspect_original_md page
- Should verify MarkdownEditor can handle read-only mode

## Clarifications and assumptions

### Blocking questions:
None - all requirements clarified during planning.

### Assumptions:

1. **MarkdownEditor read-only mode:** Assuming MarkdownEditor component either has a `readOnly` prop or can be made read-only by passing a no-op `onChange`. If neither works, we may need to:
   - Fork/modify the component
   - Use `viewMode="preview"` exclusively
   - Add custom CSS to disable pointer events

2. **ViewMode preference:** Assuming `viewMode="both"` is preferred (shows editor and preview). Could also use:
   - `"preview"` - shows only rendered markdown (simpler, truly read-only)
   - `"edit"` - shows only source (useful for copying)
   The PRD doesn't specify, so "both" matches inspect_original_md pattern.

3. **Back navigation target:** Assuming Back button should always go to `/corpus` listing, not `router.back()`. This provides consistent navigation regardless of how user arrived.

4. **File path display:** Assuming filename in header is sufficient. Could also show full path with tooltip, or add a "Copy Path" button for power users.

5. **Content caching:** Assuming content is fetched fresh each time user navigates to the page. No client-side caching initially. If users frequently revisit works, could add React Query or SWR for caching.

6. **Error retry behavior:** Assuming single Retry button that re-fetches content. Could also add automatic retry with exponential backoff, but simple manual retry is clearer UX.

7. **Work metadata:** Backend returns work_title and filename with content. Assuming this is sufficient for header. Could also fetch full work details (authors, year, etc.) and display in a sidebar or card.

### Non-blocking clarifications:

- **Page title:** Currently "Corpus Work" - could be more specific like "View Sanitized Content" or just use work title.

- **Breadcrumbs:** Could add breadcrumbs: "Corpus > {work_title}" for better navigation context.

- **Action buttons:** Future enhancement could add "Download", "Copy to Clipboard", or "View Statistics" buttons.

- **Metadata panel:** Could add collapsible sidebar showing work metadata (authors, year, publisher, chunk counts, etc.).

---

**Before implementing, review the Clarifications and assumptions section. Test the MarkdownEditor component's read-only capabilities first. If it doesn't support read-only mode adequately, consult with the team on best approach (preview-only mode, custom styling, or component modification).**
