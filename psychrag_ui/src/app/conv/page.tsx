"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { FileIcon, FileTextIcon, ChevronRightIcon } from "lucide-react";

// Mock data - will be replaced with module calls
const mockInputFiles = [
  { name: "cognitive_psychology", extension: "pdf" },
  { name: "memory_handbook", extension: "pdf" },
  { name: "neuroscience_intro", extension: "pdf" },
  { name: "behavioral_analysis", extension: "pdf" },
  { name: "clinical_methods", extension: "pdf" },
];

// Mock data for converted files (grouped by stem)
// In reality, these would have .style.md, .hier.md, .toc_titles.md, .pdf, etc.
const mockConvertedFiles = [
  { name: "learning_theory", contentHash: "abc123def456", hasStyle: true, hasHier: true, hasToc: true },
  { name: "perception_basics", contentHash: "xyz789ghi012", hasStyle: true, hasHier: false, hasToc: true },
  { name: "developmental_psych", contentHash: "jkl345mno678", hasStyle: true, hasHier: true, hasToc: false },
];

export default function ConversionPage() {
  const router = useRouter();
  const [selectedInputFile, setSelectedInputFile] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleInputFileClick = (fileName: string) => {
    setSelectedInputFile(fileName);
    setIsModalOpen(true);
  };

  const handleConvertedFileClick = (contentHash: string) => {
    router.push(`/conv/${contentHash}`);
  };

  const handleStartConversion = () => {
    // TODO: Implement conversion start
    console.log(`Starting conversion for: ${selectedInputFile}`);
    setIsModalOpen(false);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Conversion</h2>
        <p className="text-muted-foreground">Convert documents to markdown format.</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Left Panel - Input Files */}
        <Card>
          <CardHeader>
            <CardTitle>Input Files</CardTitle>
            <CardDescription>Select a file to convert to markdown.</CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[400px] pr-4">
              {mockInputFiles.length === 0 ? (
                <div className="text-sm text-muted-foreground py-8 text-center">
                  No files in input folder.
                </div>
              ) : (
                <div className="space-y-1">
                  {mockInputFiles.map((file) => (
                    <button
                      key={file.name}
                      onClick={() => handleInputFileClick(file.name)}
                      className="w-full flex items-center gap-3 p-3 rounded-md hover:bg-accent transition-colors text-left group"
                    >
                      <div className="flex-shrink-0 p-2 rounded bg-red-500/10 text-red-500">
                        <FileIcon className="h-4 w-4" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">{file.name}</p>
                        <p className="text-xs text-muted-foreground uppercase">.{file.extension}</p>
                      </div>
                      <ChevronRightIcon className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                    </button>
                  ))}
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Right Panel - Converted Files (Not in DB) */}
        <Card>
          <CardHeader>
            <CardTitle>Pending Review</CardTitle>
            <CardDescription>Converted files awaiting database entry.</CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[400px] pr-4">
              {mockConvertedFiles.length === 0 ? (
                <div className="text-sm text-muted-foreground py-8 text-center">
                  No converted files pending review.
                </div>
              ) : (
                <div className="space-y-1">
                  {mockConvertedFiles.map((file) => (
                    <button
                      key={file.contentHash}
                      onClick={() => handleConvertedFileClick(file.contentHash)}
                      className="w-full flex items-center gap-3 p-3 rounded-md hover:bg-accent transition-colors text-left group"
                    >
                      <div className="flex-shrink-0 p-2 rounded bg-emerald-500/10 text-emerald-500">
                        <FileTextIcon className="h-4 w-4" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">{file.name}</p>
                        <div className="flex gap-1 mt-1">
                          {file.hasStyle && (
                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-500">
                              style
                            </span>
                          )}
                          {file.hasHier && (
                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-purple-500/10 text-purple-500">
                              hier
                            </span>
                          )}
                          {file.hasToc && (
                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-500">
                              toc
                            </span>
                          )}
                        </div>
                      </div>
                      <ChevronRightIcon className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                    </button>
                  ))}
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>
      </div>

      {/* Confirmation Modal for Input Files */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Start Conversion</DialogTitle>
            <DialogDescription>
              Convert <span className="font-medium text-foreground">{selectedInputFile}.pdf</span> to markdown format?
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <p className="text-sm text-muted-foreground">
              This will process the PDF and generate markdown files for review. 
              The conversion may take several minutes depending on the file size.
            </p>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleStartConversion}>
              Start Conversion
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
