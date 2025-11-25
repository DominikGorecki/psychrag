"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function VectorizationPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Vectorization</h2>
        <p className="text-muted-foreground">Generate embeddings for chunks.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Process Chunks</CardTitle>
          <CardDescription>Convert text chunks into vector embeddings.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-4">
             <div className="grid gap-1">
                <p className="text-sm font-medium">Pending Chunks</p>
                <p className="text-2xl font-bold">0</p>
             </div>
             <Button>Vectorize All</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

