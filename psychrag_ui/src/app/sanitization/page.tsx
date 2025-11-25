"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function SanitizationPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Sanitization</h2>
        <p className="text-muted-foreground">Clean and structure markdown content.</p>
      </div>

      <div className="grid gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Heading Management</CardTitle>
            <CardDescription>Analyze and fix document structure.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-4">
              <Button>Extract TOC</Button>
              <Button variant="outline">Analyze Headings</Button>
              <Button variant="outline">Suggest Changes</Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Preview</CardTitle>
            <CardDescription>Document content preview.</CardDescription>
          </CardHeader>
          <CardContent className="min-h-[300px] border rounded-md bg-muted/10 p-4">
            <p className="text-muted-foreground text-sm">Select a document to view content.</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

