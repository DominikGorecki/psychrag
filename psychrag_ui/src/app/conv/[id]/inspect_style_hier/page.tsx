"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { MarkdownStickyViewer } from "@/components/markdown-sticky-viewer";
import {
  AlertCircle,
  CheckCircle2,
  Loader2Icon,
  Save,
  Sparkles,
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

interface FileMetrics {
  total_headings: number;
  h1_h2_count: number;
  max_depth: number;
  avg_depth: number;
  coverage_score: number;
  hierarchy_score: number;
  chunkability_score: number;
  target_size_sections: number;
  small_sections: number;
  large_sections: number;
  level_jump_count: number;
  penalty_total: number;
  final_score: number;
}

interface Suggestion {
  style_metrics: FileMetrics;
  hier_metrics: FileMetrics;
  winner: "style" | "hier";
  score_difference: number;
}

export default function InspectStyleHierPage() {
  const params = useParams();
  const fileId = params.id as string;

  // Content states
  const [styleContent, setStyleContent] = useState("");
  const [hierContent, setHierContent] = useState("");
  
  // Modified states
  const [styleModified, setStyleModified] = useState(false);
  const [hierModified, setHierModified] = useState(false);
  
  // Original content for comparison
  const [originalStyleContent, setOriginalStyleContent] = useState("");
  const [originalHierContent, setOriginalHierContent] = useState("");

  // Loading states
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<"style" | "hier" | null>(null);
  const [selecting, setSelecting] = useState<"style" | "hier" | null>(null);
  const [loadingSuggestion, setLoadingSuggestion] = useState(false);

  // Error states
  const [error, setError] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);

  // Suggestion state
  const [suggestion, setSuggestion] = useState<Suggestion | null>(null);

  // Selection dialog state
  const [selectionDialog, setSelectionDialog] = useState<{
    open: boolean;
    fileType: "style" | "hier" | null;
  }>({ open: false, fileType: null });

  // Fetch file contents and suggestion on mount
  useEffect(() => {
    fetchFiles();
    fetchSuggestion();
  }, [fileId]);

  const fetchFiles = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch both files in parallel
      const [styleRes, hierRes] = await Promise.all([
        fetch(`${API_BASE_URL}/conv/file-content/${fileId}/style`),
        fetch(`${API_BASE_URL}/conv/file-content/${fileId}/hier`),
      ]);

      if (!styleRes.ok || !hierRes.ok) {
        throw new Error("Failed to load files");
      }

      const styleData = await styleRes.json();
      const hierData = await hierRes.json();

      setStyleContent(styleData.content);
      setHierContent(hierData.content);
      setOriginalStyleContent(styleData.content);
      setOriginalHierContent(hierData.content);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load files");
    } finally {
      setLoading(false);
    }
  };

  const fetchSuggestion = async () => {
    try {
      setLoadingSuggestion(true);
      const response = await fetch(`${API_BASE_URL}/conv/suggestion/${fileId}`);
      
      if (!response.ok) {
        throw new Error("Failed to load suggestion");
      }

      const data = await response.json();
      setSuggestion(data);
    } catch (err) {
      console.error("Error loading suggestion:", err);
      // Don't show error to user, suggestion is optional
    } finally {
      setLoadingSuggestion(false);
    }
  };

  const handleSave = async (fileType: "style" | "hier") => {
    setSaving(fileType);
    setSaveError(null);

    try {
      const content = fileType === "style" ? styleContent : hierContent;
      const response = await fetch(
        `${API_BASE_URL}/conv/file-content/${fileId}/${fileType}`,
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

      // Update original content and reset modified flag
      if (fileType === "style") {
        setOriginalStyleContent(content);
        setStyleModified(false);
      } else {
        setOriginalHierContent(content);
        setHierModified(false);
      }
    } catch (err) {
      setSaveError(
        err instanceof Error ? err.message : "Failed to save file"
      );
    } finally {
      setSaving(null);
    }
  };

  const handleSelectClick = (fileType: "style" | "hier") => {
    setSelectionDialog({ open: true, fileType });
  };

  const handleSelectConfirm = async () => {
    const fileType = selectionDialog.fileType;
    if (!fileType) return;

    setSelecting(fileType);
    setSaveError(null);

    try {
      const response = await fetch(
        `${API_BASE_URL}/conv/select-file/${fileId}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ file_type: fileType }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to select file");
      }

      // Success - close dialog
      setSelectionDialog({ open: false, fileType: null });
      
      // Show success message (you could add a toast notification here)
      alert(`Successfully selected ${fileType}.md as the main file!`);
    } catch (err) {
      setSaveError(
        err instanceof Error ? err.message : "Failed to select file"
      );
    } finally {
      setSelecting(null);
    }
  };

  const handleStyleContentChange = (newContent: string) => {
    setStyleContent(newContent);
    setStyleModified(newContent !== originalStyleContent);
  };

  const handleHierContentChange = (newContent: string) => {
    setHierContent(newContent);
    setHierModified(newContent !== originalHierContent);
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
          <Button onClick={fetchFiles}>Retry</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <div className="border-b bg-card p-4">
        <h1 className="text-2xl font-bold">Style vs Hier Comparison</h1>
        <p className="text-sm text-muted-foreground">
          File ID: <code className="text-xs bg-muted px-1.5 py-0.5 rounded">{fileId}</code>
        </p>
      </div>

      {/* Main content area - 50/50 split */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left: Style file */}
        <div className="w-1/2 flex flex-col border-r">
          <MarkdownStickyViewer
            content={styleContent}
            onContentChange={handleStyleContentChange}
            title="style.md"
          />
          
          {/* Style file actions */}
          <div className="p-4 border-t bg-card flex items-center gap-3">
            <Button
              onClick={() => handleSave("style")}
              disabled={!styleModified || saving !== null}
              className="gap-2"
            >
              {saving === "style" ? (
                <Loader2Icon className="h-4 w-4 animate-spin" />
              ) : (
                <Save className="h-4 w-4" />
              )}
              Save
              {styleModified && <span className="text-xs">(modified)</span>}
            </Button>
            
            <Button
              onClick={() => handleSelectClick("style")}
              disabled={selecting !== null}
              variant="outline"
              className="gap-2"
            >
              <CheckCircle2 className="h-4 w-4" />
              Select
            </Button>

            {suggestion && suggestion.winner === "style" && (
              <div className="ml-auto flex items-center gap-2 text-sm text-green-600 dark:text-green-400">
                <Sparkles className="h-4 w-4" />
                <span className="font-medium">Recommended</span>
              </div>
            )}
          </div>
        </div>

        {/* Right: Hier file */}
        <div className="w-1/2 flex flex-col">
          <MarkdownStickyViewer
            content={hierContent}
            onContentChange={handleHierContentChange}
            title="hier.md"
          />
          
          {/* Hier file actions */}
          <div className="p-4 border-t bg-card flex items-center gap-3">
            <Button
              onClick={() => handleSave("hier")}
              disabled={!hierModified || saving !== null}
              className="gap-2"
            >
              {saving === "hier" ? (
                <Loader2Icon className="h-4 w-4 animate-spin" />
              ) : (
                <Save className="h-4 w-4" />
              )}
              Save
              {hierModified && <span className="text-xs">(modified)</span>}
            </Button>
            
            <Button
              onClick={() => handleSelectClick("hier")}
              disabled={selecting !== null}
              variant="outline"
              className="gap-2"
            >
              <CheckCircle2 className="h-4 w-4" />
              Select
            </Button>

            {suggestion && suggestion.winner === "hier" && (
              <div className="ml-auto flex items-center gap-2 text-sm text-green-600 dark:text-green-400">
                <Sparkles className="h-4 w-4" />
                <span className="font-medium">Recommended</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Center suggestion button */}
      <div className="absolute bottom-4 left-1/2 -translate-x-1/2">
        <Button
          onClick={fetchSuggestion}
          disabled={loadingSuggestion}
          variant="secondary"
          size="lg"
          className="shadow-lg gap-2"
        >
          {loadingSuggestion ? (
            <Loader2Icon className="h-5 w-5 animate-spin" />
          ) : (
            <Sparkles className="h-5 w-5" />
          )}
          {loadingSuggestion ? "Analyzing..." : "Suggest Best"}
        </Button>
      </div>

      {/* Error display */}
      {saveError && (
        <div className="fixed bottom-20 left-1/2 -translate-x-1/2 bg-destructive text-destructive-foreground px-4 py-2 rounded-md shadow-lg flex items-center gap-2">
          <AlertCircle className="h-4 w-4" />
          {saveError}
        </div>
      )}

      {/* Selection confirmation dialog */}
      <Dialog
        open={selectionDialog.open}
        onOpenChange={(open) => setSelectionDialog({ open, fileType: null })}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirm File Selection</DialogTitle>
            <DialogDescription>
              Are you sure you want to select <strong>{selectionDialog.fileType}.md</strong> as the main file?
              <br />
              <br />
              This will copy it to <strong>&lt;base&gt;.md</strong> and will be used as the final version.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setSelectionDialog({ open: false, fileType: null })}
              disabled={selecting !== null}
            >
              Cancel
            </Button>
            <Button
              onClick={handleSelectConfirm}
              disabled={selecting !== null}
            >
              {selecting ? (
                <>
                  <Loader2Icon className="mr-2 h-4 w-4 animate-spin" />
                  Selecting...
                </>
              ) : (
                "Confirm Selection"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

