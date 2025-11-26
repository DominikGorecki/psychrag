"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  AlertCircle,
  ChevronLeft,
  HelpCircle,
  Loader2Icon,
  Save,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function InspectVecSuggestionsPage() {
  const params = useParams();
  const router = useRouter();
  const workId = params.id as string;

  // Content states
  const [content, setContent] = useState("");
  const [originalContent, setOriginalContent] = useState("");
  const [modified, setModified] = useState(false);

  // Loading states
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Error states
  const [error, setError] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);

  // Dialog states
  const [helpDialogOpen, setHelpDialogOpen] = useState(false);

  // Fetch file content on mount
  useEffect(() => {
    fetchFileContent();
  }, [workId]);

  // Track content modifications
  useEffect(() => {
    setModified(content !== originalContent);
  }, [content, originalContent]);

  const fetchFileContent = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(
        `${API_BASE_URL}/chunk/work/${workId}/vec-suggestions/content`
      );

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error("Vector suggestions file not found. Generate it first.");
        }
        throw new Error(`Failed to load file: ${response.statusText}`);
      }

      const data = await response.json();
      setContent(data.content);
      setOriginalContent(data.content);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load file");
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setSaveError(null);

    try {
      const response = await fetch(
        `${API_BASE_URL}/chunk/work/${workId}/vec-suggestions/content`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ content }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to save file");
      }

      // Update original content to match saved content
      setOriginalContent(content);
      setModified(false);
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Failed to save file");
    } finally {
      setSaving(false);
    }
  };

  const handleBack = () => {
    if (modified) {
      const confirmLeave = confirm(
        "You have unsaved changes. Are you sure you want to leave?"
      );
      if (!confirmLeave) return;
    }
    router.push(`/chunk/${workId}`);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[calc(100vh-200px)]">
        <Loader2Icon className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={handleBack}>
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <div>
            <h2 className="text-3xl font-bold tracking-tight">Error</h2>
          </div>
        </div>
        <div className="rounded-lg border border-destructive bg-destructive/10 p-4">
          <div className="flex items-center gap-3 text-destructive">
            <AlertCircle className="h-5 w-5" />
            <p>{error}</p>
          </div>
          <Button onClick={fetchFileContent} variant="outline" className="mt-4">
            Retry
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={handleBack}>
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <div>
            <h2 className="text-3xl font-bold tracking-tight">
              Vector Embedding Suggestions
            </h2>
            <p className="text-muted-foreground">
              View and edit vectorization decisions for each heading
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setHelpDialogOpen(true)}
          >
            <HelpCircle className="h-4 w-4 mr-2" />
            Help
          </Button>
          <Button
            onClick={handleSave}
            disabled={!modified || saving}
            size="sm"
            className="gap-2"
          >
            {saving ? (
              <Loader2Icon className="h-4 w-4 animate-spin" />
            ) : (
              <Save className="h-4 w-4" />
            )}
            {saving ? "Saving..." : "Save Changes"}
          </Button>
        </div>
      </div>

      {/* Save Error Alert */}
      {saveError && (
        <div className="rounded-lg border border-destructive bg-destructive/10 p-4">
          <div className="flex items-center gap-3 text-destructive">
            <AlertCircle className="h-5 w-5" />
            <div>
              <p className="font-medium">Failed to save</p>
              <p className="text-sm">{saveError}</p>
            </div>
          </div>
        </div>
      )}

      {/* Modified Indicator */}
      {modified && (
        <div className="rounded-lg border border-yellow-500 bg-yellow-50 p-3">
          <p className="text-sm text-yellow-800">
            You have unsaved changes. Click "Save Changes" to update the file.
          </p>
        </div>
      )}

      {/* Content Editor */}
      <div className="rounded-lg border">
        <Textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          className="min-h-[calc(100vh-350px)] font-mono text-sm resize-none border-0 focus-visible:ring-0"
          placeholder="Vector suggestions..."
        />
      </div>

      {/* Help Dialog */}
      <Dialog open={helpDialogOpen} onOpenChange={setHelpDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Vector Embedding Suggestions Help</DialogTitle>
            <DialogDescription>
              This file contains AI-generated decisions about which headings should be vectorized.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 text-sm">
            <div>
              <h4 className="font-semibold mb-2">What is this file?</h4>
              <p className="text-muted-foreground">
                This file lists each heading from your sanitized document with a decision
                of whether to vectorize it (VECTORIZE) or skip it (SKIP). These decisions
                are used when creating chunks in the database.
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-2">File Format</h4>
              <p className="text-muted-foreground mb-2">
                The file contains a code block with one decision per line:
              </p>
              <ul className="list-disc pl-5 space-y-1 text-muted-foreground">
                <li>
                  Format: <code>line_number: DECISION</code>
                </li>
                <li>
                  <strong>VECTORIZE</strong> - This heading and its content will be chunked and vectorized
                </li>
                <li>
                  <strong>SKIP</strong> - This heading will not be included in vector search
                </li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-2">Editing Guidelines</h4>
              <ul className="list-disc pl-5 space-y-1 text-muted-foreground">
                <li>Line numbers must match the sanitized titles file</li>
                <li>Only use VECTORIZE or SKIP (case-sensitive)</li>
                <li>Skip administrative sections like Table of Contents, Appendices</li>
                <li>Vectorize main content sections with meaningful information</li>
                <li>Changes affect which headings become searchable chunks</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-2">Example Format</h4>
              <pre className="bg-muted p-3 rounded text-xs overflow-x-auto">
{`./document.sanitized.titles.md

# VECTORIZATION SUGGESTIONS
\`\`\`
10: SKIP
25: VECTORIZE
50: VECTORIZE
75: VECTORIZE
100: VECTORIZE
125: SKIP
\`\`\``}
              </pre>
            </div>
            <div>
              <h4 className="font-semibold mb-2">Impact on Chunking</h4>
              <p className="text-muted-foreground">
                When you run "Apply Heading Chunks", only headings marked as VECTORIZE
                will be created as chunks in the database. These chunks will then be
                available for vector search and retrieval.
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button onClick={() => setHelpDialogOpen(false)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

