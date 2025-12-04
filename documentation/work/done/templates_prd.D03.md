COMPLETE

# T03: Settings UI - Templates tab with list and editor

## Context

- **PRD**: [templates_prd.md](templates_prd.md)
- **PRD Section**: Lines 3-15 (complete UI flow for template management)
- **User Value**: Provides a user-friendly interface in the Settings page for viewing, editing, and managing prompt template versions, enabling non-technical users to customize prompts without touching code.

## Outcome

Users can navigate to Settings > Templates tab and:
1. See a list of all template functions with their active version
2. Click a function to open the template editor page
3. View the active template in a text input area
4. Select different versions from a dropdown (including "Add New")
5. Edit the active template content directly (saves on blur/submit)
6. Create new versions via "Add New" option
7. Switch between versions and set a version as active

The UI follows existing Settings page patterns (tabs, cards, forms) and integrates seamlessly with the psychRAG UI design system.

## Scope

**In scope:**
- Add "Templates" tab to Settings page after "Paths" tab
- Create templates list view showing all 4 function tags with active version
- Create template editor page with:
  - Version dropdown selector with "Add New" at top
  - Title input field
  - Template content textarea (large, monospace font)
  - "Set as Active" button (only shown for inactive versions)
  - "Save" button for content changes
  - Auto-save on blur or manual save
- Navigation between list and editor views
- State management for template data
- Error handling and loading states
- Success/failure feedback for save operations
- Responsive layout matching existing Settings page design

**Out of scope:**
- Template syntax highlighting or autocomplete (future enhancement)
- Template preview/testing functionality
- Template diff/comparison views
- Template export/import
- Keyboard shortcuts for editor
- Undo/redo functionality
- Template validation beyond API validation

## Implementation plan

### Frontend

#### 1. Update Settings page with Templates tab

File: `psychrag_ui/src/app/settings/page.tsx`

**Changes:**

Add "templates" to tab list (line 67):
```typescript
const defaultTab = tabParam && ["init", "models", "database", "paths", "templates"].includes(tabParam)
  ? tabParam
  : "init";
```

Add TabsTrigger in TabsList (after line 341):
```typescript
<TabsTrigger value="templates">Templates</TabsTrigger>
```

Add TabsContent for templates (after Paths tab, around line 774):
```typescript
{/* Templates Tab */}
<TabsContent value="templates" className="mt-4">
  <TemplatesTabContent />
</TabsContent>
```

#### 2. Create TemplatesTabContent component

File: `psychrag_ui/src/components/settings/templates-tab.tsx`

This component shows the list of template functions:

```typescript
"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Loader2Icon, AlertCircle, PenSquare } from "lucide-react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface TemplateSummary {
  version: number;
  title: string;
  is_active: boolean;
  created_at: string;
}

interface FunctionTemplateSummary {
  function_tag: string;
  active_version: number | null;
  versions: TemplateSummary[];
}

interface TemplateListResponse {
  templates: FunctionTemplateSummary[];
}

// Human-readable labels for function tags
const FUNCTION_LABELS: Record<string, string> = {
  query_expansion: "Query Expansion",
  rag_augmentation: "RAG Augmented Prompt",
  vectorization_suggestions: "Vectorization Suggestions",
  heading_hierarchy: "Heading Hierarchy Corrections",
};

export function TemplatesTabContent() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [templates, setTemplates] = useState<FunctionTemplateSummary[]>([]);

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`${API_BASE_URL}/settings/templates/`);
      if (!response.ok) {
        throw new Error(`Failed to fetch templates: ${response.statusText}`);
      }
      const data: TemplateListResponse = await response.json();
      setTemplates(data.templates);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load templates");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2Icon className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <Card className="border-destructive">
        <CardContent className="pt-6">
          <div className="flex items-center gap-2 text-destructive">
            <AlertCircle className="h-4 w-4" />
            <span>{error}</span>
          </div>
          <Button onClick={fetchTemplates} className="mt-4">
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Prompt Templates</CardTitle>
        <CardDescription>
          Manage versioned prompt templates for AI functions. Click a function to edit its templates.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Function</TableHead>
              <TableHead>Active Version</TableHead>
              <TableHead>Total Versions</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {templates.map((template) => (
              <TableRow key={template.function_tag}>
                <TableCell className="font-medium">
                  {FUNCTION_LABELS[template.function_tag] || template.function_tag}
                </TableCell>
                <TableCell>
                  {template.active_version ? (
                    <Badge variant="default">v{template.active_version}</Badge>
                  ) : (
                    <span className="text-muted-foreground text-sm">No active version</span>
                  )}
                </TableCell>
                <TableCell>
                  <span className="text-sm text-muted-foreground">
                    {template.versions.length} version{template.versions.length !== 1 ? 's' : ''}
                  </span>
                </TableCell>
                <TableCell className="text-right">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => router.push(`/settings/templates/${template.function_tag}`)}
                  >
                    <PenSquare className="h-4 w-4 mr-2" />
                    Edit
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
```

#### 3. Create template editor page

File: `psychrag_ui/src/app/settings/templates/[function_tag]/page.tsx`

This is a new dynamic route for editing templates:

```typescript
"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Loader2Icon, AlertCircle, CheckCircle2, ArrowLeft, Plus } from "lucide-react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface PromptTemplate {
  id: number;
  function_tag: string;
  version: number;
  title: string;
  template_content: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

const FUNCTION_LABELS: Record<string, string> = {
  query_expansion: "Query Expansion",
  rag_augmentation: "RAG Augmented Prompt",
  vectorization_suggestions: "Vectorization Suggestions",
  heading_hierarchy: "Heading Hierarchy Corrections",
};

export default function TemplateEditorPage() {
  const router = useRouter();
  const params = useParams();
  const functionTag = params.function_tag as string;

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const [templates, setTemplates] = useState<PromptTemplate[]>([]);
  const [selectedVersion, setSelectedVersion] = useState<number | "new" | null>(null);
  const [currentTemplate, setCurrentTemplate] = useState<PromptTemplate | null>(null);

  // Form state
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [isDirty, setIsDirty] = useState(false);

  useEffect(() => {
    fetchTemplates();
  }, [functionTag]);

  useEffect(() => {
    if (selectedVersion === "new") {
      // Reset form for new template
      setCurrentTemplate(null);
      setTitle("");
      setContent("");
      setIsDirty(false);
    } else if (selectedVersion !== null && templates.length > 0) {
      // Load selected version
      const template = templates.find((t) => t.version === selectedVersion);
      if (template) {
        setCurrentTemplate(template);
        setTitle(template.title);
        setContent(template.template_content);
        setIsDirty(false);
      }
    }
  }, [selectedVersion, templates]);

  const fetchTemplates = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`${API_BASE_URL}/settings/templates/${functionTag}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch templates: ${response.statusText}`);
      }
      const data: PromptTemplate[] = await response.json();
      setTemplates(data);

      // Auto-select active version or highest version
      const activeTemplate = data.find((t) => t.is_active);
      if (activeTemplate) {
        setSelectedVersion(activeTemplate.version);
      } else if (data.length > 0) {
        setSelectedVersion(data[0].version); // Already sorted by version DESC
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load templates");
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!isDirty) return;

    try {
      setSaving(true);
      setError(null);

      if (selectedVersion === "new") {
        // Create new version
        const response = await fetch(`${API_BASE_URL}/settings/templates/${functionTag}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ title, template_content: content }),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || `Failed to create template: ${response.statusText}`);
        }

        // Refresh templates and select the new version
        await fetchTemplates();
        setSaveSuccess(true);
        setTimeout(() => setSaveSuccess(false), 2000);
      } else if (currentTemplate) {
        // Update existing version
        const response = await fetch(
          `${API_BASE_URL}/settings/templates/${functionTag}/${currentTemplate.version}`,
          {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ title, template_content: content }),
          }
        );

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || `Failed to update template: ${response.statusText}`);
        }

        // Refresh templates
        await fetchTemplates();
        setIsDirty(false);
        setSaveSuccess(true);
        setTimeout(() => setSaveSuccess(false), 2000);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save template");
    } finally {
      setSaving(false);
    }
  };

  const handleActivate = async () => {
    if (!currentTemplate) return;

    try {
      setSaving(true);
      setError(null);

      const response = await fetch(
        `${API_BASE_URL}/settings/templates/${functionTag}/${currentTemplate.version}/activate`,
        { method: "PUT" }
      );

      if (!response.ok) {
        throw new Error(`Failed to activate: ${response.statusText}`);
      }

      // Refresh templates to update active status
      await fetchTemplates();
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to activate template");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={() => router.push("/settings?tab=templates")}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
        </div>
        <div className="flex items-center justify-center h-64">
          <Loader2Icon className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={() => router.push("/settings?tab=templates")}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
          <div>
            <h2 className="text-3xl font-bold tracking-tight">
              {FUNCTION_LABELS[functionTag] || functionTag}
            </h2>
            <p className="text-muted-foreground">Edit prompt template versions</p>
          </div>
        </div>
      </div>

      {/* Error alert */}
      {error && (
        <div className="bg-destructive/10 border border-destructive/20 text-destructive px-4 py-3 rounded-md text-sm flex items-center gap-2">
          <AlertCircle className="h-4 w-4" />
          {error}
        </div>
      )}

      {/* Success alert */}
      {saveSuccess && (
        <div className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 px-4 py-3 rounded-md text-sm flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4" />
          Template saved successfully
        </div>
      )}

      {/* Editor Card */}
      <Card>
        <CardHeader>
          <CardTitle>Template Editor</CardTitle>
          <CardDescription>
            Select a version to edit or create a new one
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Version selector */}
          <div className="space-y-2">
            <Label>Version</Label>
            <Select
              value={selectedVersion?.toString() || ""}
              onValueChange={(value) => setSelectedVersion(value === "new" ? "new" : parseInt(value))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select version" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="new">
                  <div className="flex items-center gap-2">
                    <Plus className="h-4 w-4" />
                    Add New Version
                  </div>
                </SelectItem>
                {templates.map((template) => (
                  <SelectItem key={template.version} value={template.version.toString()}>
                    <div className="flex items-center gap-2">
                      V{template.version}: {template.title}
                      {template.is_active && (
                        <Badge variant="default" className="ml-2 text-xs">
                          active
                        </Badge>
                      )}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Title input */}
          <div className="space-y-2">
            <Label htmlFor="title">Title</Label>
            <Input
              id="title"
              value={title}
              onChange={(e) => {
                setTitle(e.target.value);
                setIsDirty(true);
              }}
              placeholder="Template title"
            />
          </div>

          {/* Template content */}
          <div className="space-y-2">
            <Label htmlFor="content">Template Content</Label>
            <Textarea
              id="content"
              value={content}
              onChange={(e) => {
                setContent(e.target.value);
                setIsDirty(true);
              }}
              placeholder="Enter prompt template with {variables}"
              className="font-mono text-sm min-h-[400px]"
            />
            <p className="text-xs text-muted-foreground">
              Use {"{"}variable{"}"} syntax for LangChain PromptTemplate variables
            </p>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-3 pt-2">
            <Button onClick={handleSave} disabled={saving || !isDirty}>
              {saving ? (
                <>
                  <Loader2Icon className="h-4 w-4 animate-spin mr-2" />
                  Saving...
                </>
              ) : (
                "Save Changes"
              )}
            </Button>

            {currentTemplate && !currentTemplate.is_active && selectedVersion !== "new" && (
              <Button variant="outline" onClick={handleActivate} disabled={saving}>
                Set as Active
              </Button>
            )}

            {currentTemplate?.is_active && (
              <Badge variant="default" className="ml-2">
                Active Version
              </Badge>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
```

#### 4. Update navbar (optional)

The Templates functionality is under Settings, so no navbar changes are needed. Users navigate: Settings → Templates tab → Edit button → Editor page.

#### 5. State management and data fetching

- Use React hooks (`useState`, `useEffect`) for local state
- Fetch data on component mount and after mutations
- No global state management needed (each page is self-contained)

#### 6. UX flows

**Happy path - Edit existing template:**
1. User navigates to Settings → Templates tab
2. Sees list of 4 functions with active versions
3. Clicks "Edit" on "Query Expansion"
4. Editor loads with active version (v1) selected in dropdown
5. User modifies template content in textarea
6. Content is marked as dirty (isDirty=true)
7. User clicks "Save Changes"
8. API call updates the template
9. Success message appears
10. Template list refreshes

**Happy path - Create new version:**
1. User is on editor page for "Query Expansion"
2. Clicks version dropdown, selects "Add New Version"
3. Form clears (title and content empty)
4. User enters new title and content
5. User clicks "Save Changes"
6. API creates v2 (not active)
7. Success message appears
8. Dropdown refreshes, shows v2

**Happy path - Activate version:**
1. User selects v2 from dropdown (currently not active)
2. "Set as Active" button appears
3. User clicks "Set as Active"
4. API activates v2, deactivates v1
5. Success message appears
6. Badge updates to show "Active Version"

**Error handling:**
- API errors show in red alert banner
- Validation errors from API (invalid template format) shown clearly
- Loading states show spinners
- Failed saves don't lose user's changes (form state preserved)

### Other / cross-cutting

**Responsive design:**
- Use existing Tailwind classes for responsive layout
- Editor textarea should be readable on mobile (may require horizontal scroll for long lines)

**Accessibility:**
- Proper label/input associations
- Keyboard navigation support (via shadcn components)
- ARIA labels on icon buttons

**Performance:**
- Template content can be large (1000+ lines) - textarea should handle this
- Consider debouncing auto-save if implemented (not in scope)

## Unit tests

**Target**: Component tests using React Testing Library

File: `psychrag_ui/src/components/settings/__tests__/templates-tab.test.tsx`

**Test cases:**

1. **TemplatesTabContent component:**
   - `test_renders_loading_state()`: Shows spinner while fetching
   - `test_renders_templates_list()`: Shows table with all function tags
   - `test_displays_active_version_badge()`: Active version shown with badge
   - `test_handles_fetch_error()`: Shows error message and retry button
   - `test_navigates_to_editor()`: Clicking "Edit" navigates to editor page

2. **TemplateEditorPage component:**
   - `test_loads_active_version_by_default()`: Auto-selects active version on load
   - `test_version_selector_shows_all_versions()`: Dropdown includes all versions + "Add New"
   - `test_add_new_clears_form()`: Selecting "Add New" clears title and content
   - `test_save_updates_existing_template()`: Clicking save updates template via API
   - `test_save_creates_new_version()`: Save on "Add New" creates new version
   - `test_activate_button_only_for_inactive()`: "Set as Active" only shown for inactive versions
   - `test_dirty_flag_tracks_changes()`: isDirty=true when form modified
   - `test_shows_success_message_on_save()`: Success alert appears after save

**Example test:**
```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { TemplatesTabContent } from '../templates-tab';

// Mock fetch
global.fetch = jest.fn();

describe('TemplatesTabContent', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders templates list', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        templates: [
          {
            function_tag: 'query_expansion',
            active_version: 1,
            versions: [{ version: 1, title: 'Test V1', is_active: true, created_at: '2025-11-28' }],
          },
        ],
      }),
    });

    render(<TemplatesTabContent />);

    await waitFor(() => {
      expect(screen.getByText('Query Expansion')).toBeInTheDocument();
      expect(screen.getByText('v1')).toBeInTheDocument();
    });
  });
});
```

**Note**: Full component testing requires mocking Next.js router and API calls. Follow existing test patterns in the project.

## Manual test plan

After implementing this ticket, test the full UI flow:

### 1. Navigate to Templates tab

1. Open `http://localhost:3000/settings`
2. Click "Templates" tab
3. **Verify:** Table shows 4 function tags with labels:
   - Query Expansion
   - RAG Augmented Prompt
   - Vectorization Suggestions
   - Heading Hierarchy Corrections
4. **Verify:** Each row shows active version badge (v1) and version count (1 version)

### 2. Open template editor

1. Click "Edit" button on "Query Expansion"
2. **Verify:** Navigates to `/settings/templates/query_expansion`
3. **Verify:** Version dropdown shows:
   - "Add New Version" at top
   - "V1: Query Expansion - Multi-Query Expansion (MQE) and HyDE [active]"
4. **Verify:** Title field shows "Query Expansion - Multi-Query Expansion (MQE) and HyDE"
5. **Verify:** Template content shows full prompt with `{query}` and `{n}` variables
6. **Verify:** "Active Version" badge is visible
7. **Verify:** "Set as Active" button is NOT visible (already active)

### 3. Edit active template

1. Modify content in textarea (e.g., change a sentence)
2. **Verify:** "Save Changes" button becomes enabled (not disabled)
3. Click "Save Changes"
4. **Verify:** Loading spinner appears on button
5. **Verify:** Success message appears: "Template saved successfully"
6. **Verify:** Changes persist after page refresh

### 4. Create new version

1. Open version dropdown, select "Add New Version"
2. **Verify:** Title and content fields clear
3. Enter new title: "Query Expansion V2 - Improved"
4. Enter new content (can copy and modify existing)
5. Click "Save Changes"
6. **Verify:** Success message appears
7. **Verify:** Dropdown now shows "V2: Query Expansion V2 - Improved"
8. **Verify:** V2 is selected, but does NOT have "active" badge
9. **Verify:** "Set as Active" button IS visible

### 5. Activate new version

1. With V2 selected, click "Set as Active"
2. **Verify:** Success message appears
3. **Verify:** "Active Version" badge appears
4. **Verify:** "Set as Active" button disappears
5. Switch dropdown to V1
6. **Verify:** V1 no longer shows "active" badge
7. Go back to Templates tab (click "Back")
8. **Verify:** Query Expansion row shows "v2" as active version

### 6. Test error handling

1. In editor, set template content to invalid format: `"bad template {unclosed"`
2. Click "Save Changes"
3. **Verify:** Error alert appears with message about invalid PromptTemplate format
4. **Verify:** Form content is NOT lost (user can fix the error)

### 7. Test navigation

1. Click "Back" button in editor
2. **Verify:** Returns to Settings page, Templates tab
3. Verify URL is `/settings?tab=templates`

### 8. Test all 4 functions

Repeat steps 2-5 for each of the other 3 function tags to ensure all templates are accessible and editable.

### 9. Responsive design check

1. Resize browser to mobile width (375px)
2. **Verify:** Templates table is readable (may scroll horizontally)
3. **Verify:** Editor page is usable (textarea may wrap or scroll)

## Dependencies and sequencing

**Depends on:**
- T02 (Backend API endpoints) - MUST be completed first

**Blocks:**
- Nothing - this is the final user-facing deliverable for templates

**Can run in parallel with:**
- T04 (Integration with existing functions) - integration is independent

## Clarifications and assumptions

### Assumptions made:

1. **Auto-save vs manual save**: Implementing manual save (user clicks "Save Changes") - auto-save on blur could be added later - **CONFIRM**: Is manual save acceptable for V1?

2. **Discard changes warning**: No "unsaved changes" warning when navigating away - browser may show default prompt if form is dirty - **CLARIFY**: Should we add explicit confirmation modal?

3. **Template syntax help**: No inline documentation for template variable syntax - user must know to use `{variable}` format - **CLARIFY**: Should we add help text, examples, or a "Variables" reference section?

4. **Version ordering**: Dropdown shows versions in descending order (newest first) - **CONFIRM**: Is this the desired order, or should newest be at bottom?

5. **Delete functionality**: No way to delete old versions via UI - versions persist forever - **CONFIRM**: Is this acceptable, or should we add a "Delete" button for non-active versions?

6. **Concurrent editing**: No conflict detection if multiple users edit same template - last save wins - **CLARIFY**: Is this a concern? Should we add optimistic locking or show a warning?

7. **Template variables documentation**: No validation that template contains required variables for its function - relies on runtime errors in T04 - **CLARIFY**: Should we validate variable presence in the UI?

8. **Mobile experience**: Textarea editing on mobile may be challenging for large templates - acceptable for admin interface - **CONFIRM**: Is mobile support required, or is this desktop-only?

9. **Success message duration**: Success alerts auto-dismiss after 2 seconds - **CONFIRM**: Is this duration appropriate?

10. **Dirty state tracking**: Form tracks changes to enable/disable save button - doesn't prevent navigation - **CONFIRM**: Is this sufficient, or should we prevent accidental navigation?

### Blocking questions:

**NONE** - Can proceed with implementation. Address assumptions in UX review.

---

**Before implementing, review the Clarifications and assumptions section with the product owner. If any blocking item is unresolved, get explicit answers or update the ticket accordingly before writing code.**
