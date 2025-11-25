"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";

export default function RAGPage() {
  return (
    <div className="space-y-6 h-[calc(100vh-8rem)] flex flex-col">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">RAG</h2>
        <p className="text-muted-foreground">Retrieval-Augmented Generation playground.</p>
      </div>

      <div className="grid gap-6 grid-cols-1 lg:grid-cols-3 flex-1 overflow-hidden">
        <div className="lg:col-span-2 flex flex-col gap-4">
          <Card className="flex-1 flex flex-col">
            <CardHeader>
              <CardTitle>Chat / Query</CardTitle>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col gap-4">
              <ScrollArea className="flex-1 border rounded-md p-4">
                <div className="text-sm text-muted-foreground text-center mt-10">
                  Enter a query to start searching the psychology database.
                </div>
              </ScrollArea>
              <div className="flex gap-2">
                <Input placeholder="Ask a question..." />
                <Button>Send</Button>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="flex flex-col gap-4">
          <Card className="flex-1">
            <CardHeader>
              <CardTitle>Context</CardTitle>
              <CardDescription>Retrieved chunks will appear here.</CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[400px]">
                <div className="text-sm text-muted-foreground">No context retrieved yet.</div>
              </ScrollArea>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

