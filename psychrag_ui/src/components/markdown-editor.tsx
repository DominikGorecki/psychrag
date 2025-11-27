"use client";

import { useState, useEffect } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { MarkdownRenderer } from "@/components/markdown-renderer";
import Editor from "@monaco-editor/react";

interface MarkdownEditorProps {
  content: string;
  onChange?: (value: string) => void;
  readOnly?: boolean;
  viewMode?: "both" | "markdown-only";
  className?: string;
}

export function MarkdownEditor({
  content,
  onChange,
  readOnly = false,
  viewMode = "both",
  className = "",
}: MarkdownEditorProps) {
  const [activeTab, setActiveTab] = useState<string>(
    viewMode === "markdown-only" ? "markdown" : "rendered"
  );
  // Force light theme (white background) as requested
  const monacoTheme = "light";

  useEffect(() => {
    if (viewMode === "markdown-only") {
      setActiveTab("markdown");
    }
  }, [viewMode]);

  const handleEditorChange = (value: string | undefined) => {
    if (onChange && value !== undefined) {
      onChange(value);
    }
  };

  return (
    <div className={`flex flex-col h-full ${className}`}>
      <Tabs 
        value={activeTab} 
        onValueChange={setActiveTab} 
        className="flex-1 flex flex-col overflow-hidden"
      >
        {viewMode === "both" && (
          <div className="flex items-center justify-between mb-4">
            <TabsList className="w-[200px]">
              <TabsTrigger value="rendered">Rendered</TabsTrigger>
              <TabsTrigger value="markdown">Markdown</TabsTrigger>
            </TabsList>
          </div>
        )}

        <TabsContent value="rendered" className="flex-1 overflow-hidden mt-0">
          <Card className="h-full overflow-hidden">
            <CardContent className="h-full p-0">
              <ScrollArea className="h-full p-6">
                <MarkdownRenderer content={content} />
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="markdown" className="flex-1 overflow-hidden mt-0">
          <Card className="h-full overflow-hidden border-0 rounded-none">
            <CardContent className="h-full p-0">
              <Editor
                height="100%"
                defaultLanguage="markdown"
                value={content}
                theme={monacoTheme}
                onChange={handleEditorChange}
                options={{
                  readOnly: readOnly,
                  lineNumbers: "on",
                  minimap: { enabled: false },
                  wordWrap: "on",
                  scrollBeyondLastLine: false,
                  automaticLayout: true,
                  padding: { top: 16, bottom: 16 },
                  fontSize: 14,
                  fontFamily: "monospace",
                }}
              />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
