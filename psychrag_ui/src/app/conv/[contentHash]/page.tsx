"use client";

import { useParams } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function ConvertedFilePage() {
  const params = useParams();
  const contentHash = params.contentHash as string;

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
          <CardTitle>Converted Document</CardTitle>
          <CardDescription>
            Content Hash: <code className="text-xs bg-muted px-1.5 py-0.5 rounded">{contentHash}</code>
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-muted-foreground py-8 text-center">
            Document review interface will be implemented here.
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

