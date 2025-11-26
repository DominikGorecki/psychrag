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

export default function InspectTitleChangesPage() {
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

  const fetchFileContent = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(
        `${API_BASE_URL}/sanitization/work/${workId}/title-changes/content`
      );

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error("Title changes file not found. Generate it first.");
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
        `${API_BASE_URL}/sanitization/work/${workId}/title-changes/content`,
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

  const handleContentChange = (newContent: string) => {
    setContent(newContent);
    setModified(newContent !== originalContent);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2Icon className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center space-y-4">
          <AlertCircle className="h-12 w-12 text-destructive mx-auto" />
          <p className="text-destructive">{error}</p>
          <div className="flex gap-3 justify-center">
            <Button onClick={fetchFileContent}>Retry</Button>
            <Button variant="outline" onClick={() => router.push(`/sanitization/${workId}`)}>
              Back
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen">
      {/* Header with controls */}
      <div className="border-b bg-card p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          {/* Back button */}
          <Button
            onClick={() => router.push(`/sanitization/${workId}`)}
            variant="ghost"
            size="sm"
            className="gap-1"
          >
            <ChevronLeft className="h-4 w-4" />
            Back
          </Button>

          <div className="border-l h-8" />

          <div>
            <h1 className="text-2xl font-bold">Title Changes</h1>
            <p className="text-sm text-muted-foreground">
              Work ID: <code className="text-xs bg-muted px-1.5 py-0.5 rounded">{workId}</code>
            </p>
          </div>
        </div>

        {/* Action buttons in header */}
        <div className="flex items-center gap-2">
          <Button
            onClick={() => setHelpDialogOpen(true)}
            variant="outline"
            size="sm"
            className="w-9 h-9 p-0"
          >
            <HelpCircle className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Main content area - editable textarea */}
      <div className="flex-1 flex overflow-hidden" style={{ maxHeight: "calc(100vh - 180px)" }}>
        <div className="w-full flex flex-col p-4">
          <Textarea
            value={content}
            onChange={(e) => handleContentChange(e.target.value)}
            className="flex-1 font-mono text-sm resize-none"
            placeholder="123 : NO_CHANGE : Chapter Title&#10;456 : H1 : New Chapter Title&#10;789 : REMOVE :&#10;..."
          />
        </div>
      </div>

      {/* Bottom action bar */}
      <div className="border-t bg-card p-4 flex items-center justify-between">
        <div className="text-sm text-muted-foreground">
          {modified && <span>Unsaved changes</span>}
        </div>

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
          Save
        </Button>
      </div>

      {/* Error display */}
      {saveError && (
        <div className="fixed bottom-4 left-1/2 -translate-x-1/2 bg-destructive text-destructive-foreground px-4 py-2 rounded-md shadow-lg flex items-center gap-2 z-50">
          <AlertCircle className="h-4 w-4" />
          {saveError}
        </div>
      )}

      {/* Help Dialog */}
      <Dialog open={helpDialogOpen} onOpenChange={setHelpDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Help</DialogTitle>
            <DialogDescription>
              About Title Changes
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <p className="text-sm text-muted-foreground mb-3">
              This file contains AI-suggested changes to heading levels and titles.
            </p>
            <p className="text-sm text-muted-foreground mb-3">
              <strong>Format:</strong> Each line shows <code>line_number : ACTION : title_text</code>
            </p>
            <p className="text-sm text-muted-foreground mb-3">
              <strong>Actions:</strong>
            </p>
            <ul className="text-sm text-muted-foreground list-disc list-inside space-y-1 ml-2">
              <li><code>NO_CHANGE</code> - Keep current level, may update text</li>
              <li><code>H1, H2, H3, H4</code> - Change to specified heading level</li>
              <li><code>REMOVE</code> - Remove this heading completely</li>
            </ul>
            <p className="text-sm text-muted-foreground mt-3">
              You can edit this file to adjust the AI suggestions before applying them.
            </p>
          </div>
          <DialogFooter>
            <Button onClick={() => setHelpDialogOpen(false)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

