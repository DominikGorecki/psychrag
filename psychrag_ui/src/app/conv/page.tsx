"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function ConversionPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Conversion</h2>
        <p className="text-muted-foreground">Convert documents to markdown format.</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Upload Document</CardTitle>
            <CardDescription>Support for PDF and EPUB files.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid w-full max-w-sm items-center gap-1.5">
              <Label htmlFor="file">Document</Label>
              <Input id="file" type="file" />
            </div>
            <Button>Start Conversion</Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent Jobs</CardTitle>
            <CardDescription>Status of recent conversions.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-sm text-muted-foreground">No recent jobs found.</div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

