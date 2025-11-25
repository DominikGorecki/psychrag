"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export default function ChunkingPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Chunking</h2>
        <p className="text-muted-foreground">Split documents into semantic chunks.</p>
      </div>

      <Tabs defaultValue="headings" className="w-full">
        <TabsList>
          <TabsTrigger value="headings">By Heading</TabsTrigger>
          <TabsTrigger value="content">By Content</TabsTrigger>
          <TabsTrigger value="bib">Bibliography</TabsTrigger>
        </TabsList>

        <TabsContent value="headings" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Heading-based Chunking</CardTitle>
              <CardDescription>Split based on document hierarchy.</CardDescription>
            </CardHeader>
            <CardContent>
              <Button>Analyze Structure</Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="content" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Content-based Chunking</CardTitle>
              <CardDescription>Split by token size and overlap.</CardDescription>
            </CardHeader>
            <CardContent>
              <Button>Process</Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="bib" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Bibliography Extraction</CardTitle>
              <CardDescription>Extract and structure references.</CardDescription>
            </CardHeader>
            <CardContent>
              <Button>Extract References</Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

