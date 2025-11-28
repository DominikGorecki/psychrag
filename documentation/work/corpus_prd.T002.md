# T002 - Move Init/Status page into Settings and update navigation - COMPLETE

## Context

- Link back to the PRD: [corpus_prd.md](corpus_prd.md)
- Specific sections: Section 2 (navigation and Settings integration)
- This ticket reorganizes the application navigation by integrating the Init/Status page into Settings as a tab and updating the navigation sidebar to accommodate the new Corpus page at the top.

## Outcome

Users experience improved navigation with:
1. Init/Status functionality accessible as the first tab in Settings
2. The `/init` route redirects to `/settings` (with Init/Status tab selected)
3. Corpus link appears at the top of the navigation sidebar
4. No loss of Init/Status functionality

## Scope

### In scope:
- Move Init page component into Settings as a new tab
- Update Settings page to use tabs: Init/Status, Models, Database, Paths
- Add redirect from `/init` to `/settings`
- Update navigation sidebar component to include Corpus at the top and Settings at the bottom (fixed-bottom on page in the navbar)
- Preserve all existing Init/Status functionality

### Out of scope:
- Backend changes (no API modifications needed)
- Corpus page implementation (handled in T003, T004)
- Any changes to Settings form logic beyond tab integration

## Implementation plan

### Frontend

#### 1. Update Settings page with tabs

File: `psychrag_ui/src/app/settings/page.tsx`

**Changes:**
- The existing Settings page already uses Tabs component
- Current tabs: "models", "database", "paths"
- Add new first tab: "init" (label: "Init/Status")
- Update TabsList to include the new tab:

```tsx
<TabsList>
  <TabsTrigger value="init">Init/Status</TabsTrigger>
  <TabsTrigger value="models">Models</TabsTrigger>
  <TabsTrigger value="database">Database</TabsTrigger>
  <TabsTrigger value="paths">Paths</TabsTrigger>
</TabsList>
```

- Set defaultValue to "init" so it opens by default
- Add TabsContent for "init" value

#### 2. Extract and integrate Init page content

File: `psychrag_ui/src/app/init/page.tsx` → integrate into Settings

**Approach:**
- Copy the entire component logic from InitPage
- Create a new component function or inline the content in the TabsContent
- Maintain all state management (loading, error, health checks, etc.)
- Keep all API calls and handlers unchanged
- Preserve the card-based layout

**Integration structure:**
```tsx
<TabsContent value="init" className="mt-4">
  {/* InitStatus component or inline logic */}
  <Card>
    <CardHeader>
      <CardTitle>Database Health</CardTitle>
      {/* ... existing init page content ... */}
    </CardHeader>
  </Card>
  <Card>
    <CardHeader>
      <CardTitle>Actions</CardTitle>
      {/* ... existing init page actions ... */}
    </CardHeader>
  </Card>
</TabsContent>
```

**Considerations:**

- The Init page already uses its own loading and error states
- These should remain scoped to the Init/Status tab
- Don't interfere with Settings page's own state management
- The page header ("Initialization", "System status and setup operations") becomes the tab content

#### 3. Create redirect for /init route

File: `psychrag_ui/src/app/init/page.tsx`

Replace the entire page with a redirect:

```tsx
"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function InitRedirectPage() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to settings page with init tab selected
    router.replace("/settings?tab=init");
  }, [router]);

  return null; // Or a brief loading indicator
}
```

**Alternative approach (using Next.js redirects):**
If the project uses next.config.js redirects or middleware, configure it there instead:

#### 4. Update Settings to handle tab parameter

File: `psychrag_ui/src/app/settings/page.tsx`

Add URL search params handling to support deep linking:

```tsx
"use client";

import { useSearchParams } from "next/navigation";

export default function SettingsPage() {
  const searchParams = useSearchParams();
  const tabParam = searchParams.get("tab");
  const defaultTab = tabParam && ["init", "models", "database", "paths"].includes(tabParam)
    ? tabParam
    : "init";

  // ... rest of component

  return (
    <Tabs defaultValue={defaultTab} className="w-full">
      {/* ... */}
    </Tabs>
  );
}
```

#### 5. Update navigation sidebar

File: Find navigation component (likely `psychrag_ui/src/components/nav.tsx` or `psychrag_ui/src/app/layout.tsx`)

**Required changes:**
- Add "Corpus" link at the very top of the navigation list
- Update "Init" link to point to "/settings?tab=init" (or remove if redundant)
- Ensure proper ordering: Corpus, Settings, Sanitization, RAG, etc.

**Example structure:**
```tsx
const navItems = [
  { name: "Corpus", href: "/corpus", icon: DatabaseIcon },
  { name: "Settings", href: "/settings", icon: SettingsIcon },
  // ... other nav items
];
```

**Considerations:**
- Choose an appropriate icon for Corpus (e.g., Database, Library, BookOpen)
- Ensure active state highlighting works for the new route
- Test that navigation state persists correctly

#### 6. Handle state and side effects

**Settings page state management:**
- Init/Status tab has its own loading/error states
- These should not block rendering of other tabs
- Consider lazy loading the health check only when Init/Status tab is active

**Example:**
```tsx
const [activeTab, setActiveTab] = useState(defaultTab);

// In TabsContent for "init"
useEffect(() => {
  if (activeTab === "init" && hasRequiredDbSettings) {
    fetchHealthChecks();
  }
}, [activeTab, hasRequiredDbSettings]);
```

## Unit tests

Create/update `/psychrag_ui/tests/unit/test_settings_page.tsx`:

### Test framework
- Use React Testing Library with Jest
- Mock Next.js router and navigation hooks
- Mock fetch for API calls

### Specific test cases

**Settings page tab integration:**
- Renders all four tabs: Init/Status, Models, Database, Paths
- Init/Status tab is selected by default
- Clicking each tab displays correct content
- Tab content is properly isolated (changing one doesn't affect others)

**Init/Status tab functionality:**
- Displays database health checks when DB settings are present
- Shows "Add DB Settings" button when settings are missing
- "Initialize Database" button appears when connection fails
- "Check Connections" button triggers health check refresh
- All buttons have correct loading states

**URL parameter handling:**
- Opening `/settings?tab=init` selects Init/Status tab
- Opening `/settings?tab=models` selects Models tab
- Invalid tab parameter defaults to Init/Status
- Missing tab parameter defaults to Init/Status

**Navigation:**
- Corpus link appears in navigation sidebar
- Corpus link routes to `/corpus`
- Settings link routes to `/settings` (defaults to Init/Status tab)
- Active state highlighting works correctly

### Edge cases
- Direct navigation to `/init` redirects to `/settings?tab=init`
- Switching tabs doesn't lose form state in other tabs
- API errors in Init/Status tab don't break other tabs
- Browser back/forward navigation works with tabs

## Manual test plan (acceptance criteria)

### Test Case 1: Init/Status tab in Settings
**Preconditions:** Application is running, database settings are configured
**Steps:**
1. Navigate to `/settings`
2. Verify four tabs are visible: Init/Status, Models, Database, Paths
3. Verify Init/Status tab is selected by default
4. Observe the database health checks display
5. Switch to Models tab
6. Switch back to Init/Status tab
7. Verify health checks are still visible

**Expected result:** Init/Status tab displays all original Init page functionality, switching tabs works smoothly

### Test Case 2: Direct navigation to /init redirects
**Preconditions:** Application is running
**Steps:**
1. Navigate directly to `/init` in the browser address bar
2. Observe the browser URL
3. Verify the page displayed

**Expected result:** Browser redirects to `/settings`, Init/Status tab is selected

### Test Case 3: Deep linking to specific tab
**Preconditions:** Application is running
**Steps:**
1. Navigate to `/settings?tab=models`
2. Verify Models tab is selected
3. Navigate to `/settings?tab=init`
4. Verify Init/Status tab is selected
5. Navigate to `/settings?tab=invalid`
6. Verify Init/Status tab is selected (fallback)

**Expected result:** URL tab parameter correctly selects the tab, invalid values default to Init/Status

### Test Case 4: Navigation sidebar updated
**Preconditions:** Application is running
**Steps:**
1. Load the application
2. Look at the navigation sidebar
3. Verify "Corpus" link appears at the top
4. Verify "Settings" link is present
5. Click "Corpus" link
6. Verify it navigates to `/corpus` (even if page doesn't exist yet)

**Expected result:** Corpus link is at the top of navigation, clicking it navigates to correct route

### Test Case 5: Init/Status functionality preserved
**Preconditions:** Database not initialized
**Steps:**
1. Navigate to `/settings`
2. Go to Init/Status tab
3. Click "Initialize Database" button
4. Observe loading state
5. Verify success/error handling works as before

**Expected result:** All Init page functionality works identically within Settings tab

### Test Case 6: Settings tabs independent
**Preconditions:** Application is running
**Steps:**
1. Navigate to `/settings`
2. Go to Models tab
3. Change provider to "OpenAI" (don't save)
4. Switch to Init/Status tab
5. Return to Models tab
6. Verify OpenAI selection is still there

**Expected result:** Tab state is preserved when switching between tabs

### Test Case 7: Tab navigation with browser history
**Preconditions:** Application is running
**Steps:**
1. Navigate to `/settings` (Init/Status tab)
2. Click Models tab
3. Click Database tab
4. Click browser back button
5. Verify Models tab is selected
6. Click browser back button again
7. Verify Init/Status tab is selected

**Expected result:** Browser back/forward navigation respects tab changes (if implemented with URL updates)

## Dependencies and sequencing

**Must be completed before:**
- T003 (Corpus listing page) - navigation link should exist before the page

**Can be done in parallel with:**
- T001 (Backend API) - no dependencies between them

**No dependencies on:**
- T004, T005

## Clarifications and assumptions

### Blocking questions:
None - all requirements clarified during planning.

### Assumptions:

1. **Tab state management:** Assuming we want tabs to be bookmarkable (URL-based state) rather than purely client-side state. This allows users to share links to specific tabs.

2. **Init page removal:** Assuming the `/init` route should be a hard redirect and the original InitPage component can be removed or gutted after integration is complete.

3. **Navigation component location:** Assuming navigation sidebar exists in a shared layout or component. If navigation is defined elsewhere (e.g., in each page), the implementation will need adjustment.

4. **Icon choice:** Assuming any lucide-react icon is acceptable for Corpus. Will use `Database` icon unless specified otherwise.

5. **Settings page state isolation:** Assuming each tab's state (forms, loading, errors) should be independent. Switching tabs doesn't reset other tabs' state.

6. **Tab lazy loading:** Assuming we want to fetch Init/Status health checks only when that tab is active, not on initial Settings page load. This improves performance when users go directly to other tabs.

### Non-blocking clarifications:

- **Mobile navigation:** Assuming mobile navigation (if it exists) should also be updated with Corpus link at the top.

- **Breadcrumbs:** If the app uses breadcrumbs, they may need updating to show "Settings > Init/Status" when on that tab.

---

**Before implementing, review the Clarifications and assumptions section. If the navigation component structure differs from assumptions, adjust the implementation accordingly. Coordinate with T003 implementer on icon choice for consistency.**
