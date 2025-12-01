# T003 - Corpus listing page with works and statistics - COMPLETE

## Context

- Link back to the PRD: [corpus_prd.md](corpus_prd.md)
- Specific sections: Section 4 (corpus page with overview and works table)
- This ticket implements the main corpus listing page that displays statistics about vectorization readiness and a table of all works that have completed chunking. This gives users visibility into which works are ready for RAG operations and what their vectorization status is.

## Outcome

Users can view a comprehensive corpus page at `/corpus` that shows:
1. Overview statistics: total corpus works and chunk counts broken down by vector status
2. A sortable table of all corpus works with title, authors, and file path
3. Clickable rows that navigate to individual work detail pages
4. Loading, error, and empty states

## Scope

### In scope:
- Create `/corpus` route and page component
- Fetch and display corpus statistics from backend API
- Fetch and display works table from backend API
- Implement clickable table rows with navigation
- Add loading states, error handling, and empty state
- Style page consistently with existing pages (Sanitization pattern)
- Display all four chunk vector statuses with counts

### Out of scope:
- Individual work detail page (handled in T004)
- Backend API implementation (handled in T001)
- Navigation changes (handled in T002)
- Any edit/delete operations (corpus is read-only)
- Pagination (initial implementation shows all works)

## Implementation plan

### Frontend

#### 1. Create corpus page component

File: `psychrag_ui/src/app/corpus/page.tsx`

**Component structure based on Sanitization page pattern:**

```tsx
"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertCircle, Loader2Icon, FileText, Database } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ChunkVectorStats {
  no_vec: number;
  to_vec: number;
  vec: number;
  vec_err: number;
}

interface CorpusStats {
  total_works: number;
  chunk_stats: ChunkVectorStats;
}

interface CorpusWork {
  id: number;
  title: string;
  authors: string | null;
  sanitized_path: string;
}

interface CorpusWorksResponse {
  works: CorpusWork[];
  total: number;
}

export default function CorpusPage() {
  const router = useRouter();
  const [stats, setStats] = useState<CorpusStats | null>(null);
  const [works, setWorks] = useState<CorpusWork[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Component implementation...
}
```

#### 2. Implement data fetching

**Fetch both stats and works in parallel:**

```tsx
useEffect(() => {
  fetchData();
}, []);

const fetchData = async () => {
  try {
    setLoading(true);
    setError(null);

    // Fetch stats and works in parallel
    const [statsResponse, worksResponse] = await Promise.all([
      fetch(`${API_BASE_URL}/corpus/stats`),
      fetch(`${API_BASE_URL}/corpus/works`),
    ]);

    if (!statsResponse.ok) {
      throw new Error(`Failed to load statistics: ${statsResponse.statusText}`);
    }

    if (!worksResponse.ok) {
      throw new Error(`Failed to load works: ${worksResponse.statusText}`);
    }

    const statsData: CorpusStats = await statsResponse.json();
    const worksData: CorpusWorksResponse = await worksResponse.json();

    setStats(statsData);
    setWorks(worksData.works);
  } catch (err) {
    setError(err instanceof Error ? err.message : "Failed to load corpus data");
  } finally {
    setLoading(false);
  }
};
```

#### 3. Implement loading state

```tsx
if (loading) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Corpus</h2>
        <p className="text-muted-foreground">Works ready for vectorization and RAG.</p>
      </div>
      <div className="flex items-center justify-center h-64">
        <Loader2Icon className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    </div>
  );
}
```

#### 4. Implement error state

```tsx
if (error) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Corpus</h2>
        <p className="text-muted-foreground">Works ready for vectorization and RAG.</p>
      </div>
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-3 text-destructive">
            <AlertCircle className="h-5 w-5" />
            <p>{error}</p>
          </div>
          <Button onClick={fetchData} className="mt-4">
            Retry
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
```

#### 5. Implement overview statistics card

```tsx
<Card>
  <CardHeader>
    <CardTitle>Embeddings Overview</CardTitle>
    <CardDescription>Corpus statistics and embedding vectorization status</CardDescription>
  </CardHeader>
  <CardContent>
    <div className="grid grid-cols-5 gap-4">
      <div className="space-y-1">
        <p className="text-sm text-muted-foreground">Total Works</p>
        <p className="text-2xl font-bold">{stats?.total_works || 0}</p>
      </div>
      <div className="space-y-1">
        <p className="text-sm text-muted-foreground">Not Queued</p>
        <p className="text-2xl font-bold text-muted-foreground">
          {stats?.chunk_stats.no_vec || 0}
        </p>
      </div>
      <div className="space-y-1">
        <p className="text-sm text-muted-foreground">To Vectorize</p>
        <p className="text-2xl font-bold text-amber-500">
          {stats?.chunk_stats.to_vec || 0}
        </p>
      </div>
      <div className="space-y-1">
        <p className="text-sm text-muted-foreground">Vectorized</p>
        <p className="text-2xl font-bold text-green-500">
          {stats?.chunk_stats.vec || 0}
        </p>
      </div>
      <div className="space-y-1">
        <p className="text-sm text-muted-foreground">Errors</p>
        <p className="text-2xl font-bold text-red-500">
          {stats?.chunk_stats.vec_err || 0}
        </p>
      </div>
    </div>
  </CardContent>
</Card>
```

**Styling notes:**
- Use muted gray for "no_vec" (neutral)
- Use amber/yellow for "to_vec" (pending action)
- Use green for "vec" (success)
- Use red for "vec_err" (errors)
- Grid layout ensures even spacing

#### 6. Implement works table

```tsx
<Card>
  <CardHeader>
    <CardTitle>Works</CardTitle>
    <CardDescription>
      Click on a work to view its sanitized content
    </CardDescription>
  </CardHeader>
  <CardContent>
    {works.length === 0 ? (
      <div className="text-center py-12">
        <Database className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
        <p className="text-muted-foreground">No corpus works found.</p>
        <p className="text-sm text-muted-foreground mt-2">
          Works must complete chunking before appearing here.
        </p>
      </div>
    ) : (
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[60px]">ID</TableHead>
              <TableHead>Title</TableHead>
              <TableHead>Authors</TableHead>
              <TableHead>Sanitized Path</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {works.map((work) => (
              <TableRow
                key={work.id}
                className="cursor-pointer hover:bg-muted/50"
                onClick={() => handleWorkClick(work.id)}
              >
                <TableCell className="font-medium">{work.id}</TableCell>
                <TableCell className="max-w-md truncate">
                  {work.title}
                </TableCell>
                <TableCell className="max-w-xs truncate text-muted-foreground">
                  {work.authors || "-"}
                </TableCell>
                <TableCell className="text-xs text-muted-foreground font-mono truncate max-w-sm">
                  {work.sanitized_path}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    )}
  </CardContent>
</Card>
```

**Table features:**
- Entire row is clickable (better UX than just title)
- Hover state provides visual feedback
- Truncation prevents layout breaking from long titles/paths
- Font-mono for file paths (easier to read)
- Null authors display as "-"

#### 7. Implement navigation handler

```tsx
const handleWorkClick = (workId: number) => {
  router.push(`/corpus/${workId}`);
};
```

#### 8. Page layout and header

```tsx
return (
  <div className="space-y-6">
    <div className="flex items-center justify-between">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Corpus</h2>
        <p className="text-muted-foreground">
          Works ready for vectorization and RAG.
        </p>
      </div>
    </div>

    {/* Stats Card */}
    {/* ... stats card implementation ... */}

    {/* Works Table */}
    {/* ... works table implementation ... */}
  </div>
);
```

**Layout notes:**
- Consistent with Sanitization page layout
- No action buttons needed (read-only page)
- Space-y-6 provides consistent vertical spacing
- Header with title and description

#### 9. Responsive design

**Considerations:**
- Grid in overview card should stack on mobile
- Table should be horizontally scrollable on small screens
- Use Tailwind responsive prefixes (md:, lg:)

```tsx
<div className="grid grid-cols-2 md:grid-cols-5 gap-4">
  {/* Overview stats */}
</div>
```

#### 10. Accessibility

- Semantic HTML (proper heading hierarchy)
- Table has proper headers
- Loading/error states are announced to screen readers
- Interactive elements (table rows) are keyboard accessible
- Focus states visible on table rows

## Unit tests

Create `tests/unit/test_corpus_page.tsx`:

### Test framework
- React Testing Library with Jest
- Mock Next.js router
- Mock fetch API

### Specific test cases

**Page rendering:**
- Renders page title "Corpus"
- Renders page description
- Shows loading spinner initially
- Hides loading spinner after data loads

**Data fetching:**
- Fetches from `/corpus/stats` on mount
- Fetches from `/corpus/works` on mount
- Both requests happen in parallel
- Handles successful responses correctly
- Retries on error when Retry button clicked

**Statistics display:**
- Displays total_works count correctly
- Displays all four chunk stats: no_vec, to_vec, vec, vec_err
- Uses correct colors for each status
- Shows 0 when stats are empty

**Works table:**
- Displays all works from API response
- Shows work ID, title, authors, sanitized_path
- Displays "-" for null authors
- Shows empty state when no works
- Empty state shows appropriate message

**Navigation:**
- Clicking a table row calls router.push with correct work ID
- Navigation path is `/corpus/{work_id}`

**Error handling:**
- Displays error message when fetch fails
- Shows Retry button in error state
- Retry button triggers re-fetch

### Edge cases
- Zero works in corpus
- Works with very long titles (test truncation)
- Works with null/empty authors
- API timeout (mock delayed response)
- Network error (mock fetch rejection)

## Manual test plan (acceptance criteria)

### Test Case 1: Page loads with data
**Preconditions:** Database has 3 corpus works with various chunk statuses
**Steps:**
1. Navigate to `/corpus`
2. Wait for page to load
3. Observe overview card
4. Check works table

**Expected result:**
- Overview shows total_works = 3
- All four chunk status counts are displayed with correct colors
- Works table shows 3 rows with ID, title, authors, path
- Page layout matches Sanitization page style

### Test Case 2: Empty corpus
**Preconditions:** Database has no works with completed chunking
**Steps:**
1. Navigate to `/corpus`
2. Wait for page to load
3. Observe overview card
4. Check works table area

**Expected result:**
- Overview shows total_works = 0
- All chunk stats show 0
- Works table shows empty state with icon and message
- Message says "No corpus works found" and "Works must complete chunking before appearing here"

### Test Case 3: Click work to navigate
**Preconditions:** Database has corpus works
**Steps:**
1. Navigate to `/corpus`
2. Wait for works table to load
3. Click on first work row (anywhere in the row)
4. Observe browser URL

**Expected result:**
- Browser navigates to `/corpus/{work_id}` where work_id is the ID of clicked work
- Entire row is clickable (not just title)
- Row has hover effect before clicking

### Test Case 4: Loading state
**Preconditions:** Slow network or use browser dev tools to throttle
**Steps:**
1. Navigate to `/corpus`
2. Immediately observe the page

**Expected result:**
- Page header is visible
- Loading spinner displays in center
- No error or data shown yet

### Test Case 5: Error handling
**Preconditions:** Backend API is down or returning errors
**Steps:**
1. Navigate to `/corpus`
2. Wait for request to fail
3. Observe error state
4. Click "Retry" button

**Expected result:**
- Error message displays in red with error icon
- Retry button is visible
- Clicking Retry re-attempts the fetch
- If successful, data appears; if failed, error persists

### Test Case 6: Data accuracy
**Preconditions:** Known database state (e.g., 5 works, specific chunk counts)
**Steps:**
1. Manually verify database has:
   - 5 corpus works
   - 100 chunks with no_vec
   - 50 chunks with to_vec
   - 200 chunks with vec
   - 10 chunks with vec_err
2. Navigate to `/corpus`
3. Compare displayed stats with database

**Expected result:**
- Total works: 5
- Not Queued (no_vec): 100
- To Vectorize (to_vec): 50
- Vectorized (vec): 200
- Errors (vec_err): 10
- All work rows display correct titles, authors, paths

### Test Case 7: Long text truncation
**Preconditions:** Database has work with very long title (100+ chars)
**Steps:**
1. Navigate to `/corpus`
2. Observe works table
3. Look at the row with long title

**Expected result:**
- Long title is truncated with ellipsis (...)
- Title doesn't break table layout
- Full title visible on hover (browser default tooltip)

### Test Case 8: Responsive layout
**Preconditions:** None
**Steps:**
1. Navigate to `/corpus` on desktop
2. Resize browser to tablet width
3. Resize to mobile width
4. Observe overview card grid

**Expected result:**
- Desktop: 5 columns (all stats visible)
- Tablet/mobile: 2 columns (stats stack)
- Table is scrollable horizontally on narrow screens
- Layout doesn't break at any width

## Dependencies and sequencing

**Must be completed after:**
- T001 (Backend API) - requires `/corpus/stats` and `/corpus/works` endpoints
- T002 (Navigation) - navigation link should exist (though page can work without it)

**Must be completed before:**
- T004 (Work viewer) - users need to navigate from this page to work detail

**Independent of:**
- T005 (Scrollbar fix) - that's a refinement to T004

## Clarifications and assumptions

### Blocking questions:
None - all requirements clarified during planning.

### Assumptions:

1. **Color scheme for vector statuses:** Assuming the following color mapping is appropriate:
   - no_vec: muted gray (neutral, not urgent)
   - to_vec: amber/yellow (pending, attention needed)
   - vec: green (success)
   - vec_err: red (errors)

2. **Table sorting:** Initial implementation shows works sorted by ID descending (from backend). No client-side sorting controls initially. Can be added in future enhancement.

3. **Path display:** Displaying full `sanitized_path` in table. This may be very long. Truncation with ellipsis and monospace font helps readability. Alternative: show only filename (e.g., `work.sanitized.md`) with full path in tooltip.

4. **Empty state icon:** Using `Database` icon from lucide-react for empty state. Alternative icons: `FileText`, `Inbox`, `Archive`.

5. **Overview grid columns:** Desktop shows 5 columns (one per stat). On mobile, stacks to 2 columns. Could also show 1 column on very small screens if preferred.

6. **No pagination:** Assuming initial implementation loads all corpus works without pagination. If corpus grows to 100+ works, this ticket may need revision or a follow-up ticket for pagination.

7. **No refresh interval:** Page doesn't auto-refresh stats. User must manually refresh browser or revisit page. Could add a "Refresh" button in future enhancement.

8. **Stats accuracy timing:** Stats and works are fetched in parallel, so there's a tiny race condition window. Assuming this is acceptable for read-only data.

### Non-blocking clarifications:

- **Overview card title:** Using "Overview" to match Sanitization page. Could also be "Statistics" or "Vectorization Status".

- **Page description:** Using "Works ready for vectorization and RAG." Could also say "Processed works available for retrieval-augmented generation."

- **Table column order:** Currently: ID, Title, Authors, Path. Could reorder if preferred (e.g., Title first, then ID).

---

**Before implementing, review the Clarifications and assumptions section. If any color choices or text labels don't match the design system, update accordingly. Test with various data volumes to ensure performance is acceptable.**
