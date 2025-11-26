"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertCircle, CheckCircle2, Eye, Loader2Icon, PlayCircle } from "lucide-react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface InspectionItem {
  name: string;
  available: boolean;
  files_checked: string[];
}

interface InspectionResponse {
  items: InspectionItem[];
}

// Map inspection names to human-readable labels
const INSPECTION_LABELS: Record<string, string> = {
  inspect_style_hier: "Style vs Hier Comparison",
  inspect_toc_titles: "Table of Contents Titles",
  inspect_titles: "Document Titles",
  inspect_title_changes: "Title Changes Review",
  inspect_original_md: "Original Markdown",
};

// Map inspection names to descriptions
const INSPECTION_DESCRIPTIONS: Record<string, string> = {
  inspect_style_hier: "Compare style.md and hier.md versions side by side",
  inspect_toc_titles: "Review and edit table of contents titles",
  inspect_titles: "Review extracted document titles",
  inspect_title_changes: "Review changes made to titles",
  inspect_original_md: "View the original converted markdown file",
};

export default function ConvertedFilePage() {
  const params = useParams();
  const router = useRouter();
  const fileId = params.id as string;

  const [inspectionItems, setInspectionItems] = useState<InspectionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchInspectionOptions();
  }, [fileId]);

  const fetchInspectionOptions = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${API_BASE_URL}/conv/inspection/${fileId}`);
      
      if (!response.ok) {
        if (response.status === 404) {
          throw new Error("File not found. It may have been deleted or moved.");
        }
        throw new Error(`Failed to load inspection options: ${response.statusText}`);
      }

      const data: InspectionResponse = await response.json();
      setInspectionItems(data.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load inspection options");
    } finally {
      setLoading(false);
    }
  };

  const handleInspect = (inspectionName: string) => {
    router.push(`/conv/${fileId}/${inspectionName}`);
  };

  const handleGenerate = (inspectionName: string) => {
    // Stub: This will be implemented later
    console.log(`Generate ${inspectionName} for file ${fileId}`);
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Review Conversion</h2>
          <p className="text-muted-foreground">
            Review and finalize the converted document before adding to database.
          </p>
        </div>
        <div className="flex items-center justify-center h-64">
          <Loader2Icon className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Review Conversion</h2>
          <p className="text-muted-foreground">
            Review and finalize the converted document before adding to database.
          </p>
        </div>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3 text-destructive">
              <AlertCircle className="h-5 w-5" />
              <p>{error}</p>
            </div>
            <Button onClick={fetchInspectionOptions} className="mt-4">
              Retry
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Review Conversion</h2>
        <p className="text-muted-foreground">
          Review and finalize the converted document before adding to database.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Inspection Options</CardTitle>
          <CardDescription>
            File ID: <code className="text-xs bg-muted px-1.5 py-0.5 rounded">{fileId}</code>
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {inspectionItems.length === 0 ? (
              <div className="text-sm text-muted-foreground py-8 text-center">
                No inspection options available for this file.
              </div>
            ) : (
              inspectionItems.map((item) => (
                <div
                  key={item.name}
                  className="flex items-start gap-4 p-4 rounded-lg border bg-card hover:bg-accent/50 transition-colors"
                >
                  <div className="flex-shrink-0 mt-1">
                    {item.available ? (
                      <CheckCircle2 className="h-5 w-5 text-green-500" />
                    ) : (
                      <AlertCircle className="h-5 w-5 text-amber-500" />
                    )}
                  </div>

                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-semibold mb-1">
                      {INSPECTION_LABELS[item.name] || item.name}
                    </h3>
                    <p className="text-xs text-muted-foreground mb-2">
                      {INSPECTION_DESCRIPTIONS[item.name] || "No description available"}
                    </p>
                    <div className="flex flex-wrap gap-1">
                      {item.files_checked.map((file) => (
                        <code
                          key={file}
                          className="text-[10px] px-1.5 py-0.5 rounded bg-muted text-muted-foreground"
                        >
                          {file}
                        </code>
                      ))}
                    </div>
                  </div>

                  <div className="flex-shrink-0">
                    {item.available ? (
                      <Button
                        size="sm"
                        onClick={() => handleInspect(item.name)}
                        className="gap-2"
                      >
                        <Eye className="h-4 w-4" />
                        Inspect
                      </Button>
                    ) : (
                      <Button
                        size="sm"
                        variant="outline"
                        disabled
                        onClick={() => handleGenerate(item.name)}
                        className="gap-2"
                      >
                        <PlayCircle className="h-4 w-4" />
                        Generate
                      </Button>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Next Steps</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3 text-sm">
            <p className="text-muted-foreground">
              Once you've reviewed all necessary inspection items:
            </p>
            <ol className="list-decimal list-inside space-y-2 text-muted-foreground">
              <li>Verify the conversion quality using the inspection tools above</li>
              <li>Make any necessary manual corrections to the files</li>
              <li>Click "Add to Database" to finalize the conversion</li>
            </ol>
            <Button className="mt-4" variant="default" disabled>
              Add to Database
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
