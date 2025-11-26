"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import {
  AlertCircle,
  CheckCircle2,
  Loader2Icon,
  MessageSquare,
  Clock,
  Zap,
  Search,
  Layers,
  PlayCircle,
  Plus,
} from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Alert, AlertDescription } from "@/components/ui/alert";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface QueryListItem {
  id: number;
  original_query: string;
  created_at: string;
  status: string;
  intent: string | null;
  entities_count: number;
}

interface QueryListResponse {
  queries: QueryListItem[];
  total: number;
}

export default function RAGPage() {
  const router = useRouter();
  const [queries, setQueries] = useState<QueryListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newQuery, setNewQuery] = useState("");
  const [stats, setStats] = useState({ total: 0, ready: 0, pending: 0 });

  // Operation states
  const [operatingId, setOperatingId] = useState<number | null>(null);
  const [operationError, setOperationError] = useState<string | null>(null);
  const [operationSuccess, setOperationSuccess] = useState<string | null>(null);

  useEffect(() => {
    fetchQueries();
  }, []);

  const fetchQueries = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${API_BASE_URL}/rag/queries`);

      if (!response.ok) {
        throw new Error(`Failed to load queries: ${response.statusText}`);
      }

      const data: QueryListResponse = await response.json();
      setQueries(data.queries);

      // Calculate stats
      const ready = data.queries.filter(q => q.status === "ready").length;
      setStats({
        total: data.total,
        ready,
        pending: data.total - ready
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load queries");
    } finally {
      setLoading(false);
    }
  };

  const handleNewQuery = () => {
    if (!newQuery.trim()) return;
    router.push(`/rag/new?q=${encodeURIComponent(newQuery.trim())}`);
  };

  const handleEmbed = async (queryId: number) => {
    setOperatingId(queryId);
    setOperationError(null);
    setOperationSuccess(null);

    try {
      const response = await fetch(`${API_BASE_URL}/rag/queries/${queryId}/embed`, {
        method: "POST",
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to embed query");
      }

      setOperationSuccess("Embeddings generated successfully");
      await fetchQueries();
    } catch (err) {
      setOperationError(err instanceof Error ? err.message : "Failed to embed query");
    } finally {
      setOperatingId(null);
    }
  };

  const handleRetrieve = async (queryId: number) => {
    setOperatingId(queryId);
    setOperationError(null);
    setOperationSuccess(null);

    try {
      const response = await fetch(`${API_BASE_URL}/rag/queries/${queryId}/retrieve`, {
        method: "POST",
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to retrieve");
      }

      const data = await response.json();
      setOperationSuccess(`Retrieved ${data.final_count} chunks`);
      await fetchQueries();
    } catch (err) {
      setOperationError(err instanceof Error ? err.message : "Failed to retrieve");
    } finally {
      setOperatingId(null);
    }
  };

  const handleConsolidate = async (queryId: number) => {
    setOperatingId(queryId);
    setOperationError(null);
    setOperationSuccess(null);

    try {
      const response = await fetch(`${API_BASE_URL}/rag/queries/${queryId}/consolidate`, {
        method: "POST",
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to consolidate");
      }

      const data = await response.json();
      setOperationSuccess(data.message);
      await fetchQueries();
    } catch (err) {
      setOperationError(err instanceof Error ? err.message : "Failed to consolidate");
    } finally {
      setOperatingId(null);
    }
  };

  const handleGenerate = (queryId: number) => {
    router.push(`/rag/${queryId}`);
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "needs_embeddings":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-amber-100 text-amber-800">
            <Zap className="h-3 w-3" />
            Needs Embeddings
          </span>
        );
      case "needs_retrieval":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
            <Search className="h-3 w-3" />
            Needs Retrieval
          </span>
        );
      case "needs_consolidation":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
            <Layers className="h-3 w-3" />
            Needs Consolidation
          </span>
        );
      case "ready":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
            <CheckCircle2 className="h-3 w-3" />
            Ready
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
            <Clock className="h-3 w-3" />
            {status}
          </span>
        );
    }
  };

  const getActionButton = (query: QueryListItem) => {
    const isOperating = operatingId === query.id;

    switch (query.status) {
      case "needs_embeddings":
        return (
          <Button
            size="sm"
            variant="outline"
            onClick={() => handleEmbed(query.id)}
            disabled={isOperating}
            className="gap-1"
          >
            {isOperating ? (
              <Loader2Icon className="h-3 w-3 animate-spin" />
            ) : (
              <Zap className="h-3 w-3" />
            )}
            Embed
          </Button>
        );
      case "needs_retrieval":
        return (
          <Button
            size="sm"
            variant="outline"
            onClick={() => handleRetrieve(query.id)}
            disabled={isOperating}
            className="gap-1"
          >
            {isOperating ? (
              <Loader2Icon className="h-3 w-3 animate-spin" />
            ) : (
              <Search className="h-3 w-3" />
            )}
            Retrieve
          </Button>
        );
      case "needs_consolidation":
        return (
          <Button
            size="sm"
            variant="outline"
            onClick={() => handleConsolidate(query.id)}
            disabled={isOperating}
            className="gap-1"
          >
            {isOperating ? (
              <Loader2Icon className="h-3 w-3 animate-spin" />
            ) : (
              <Layers className="h-3 w-3" />
            )}
            Consolidate
          </Button>
        );
      case "ready":
        return (
          <Button
            size="sm"
            onClick={() => handleGenerate(query.id)}
            disabled={isOperating}
            className="gap-1"
          >
            <PlayCircle className="h-3 w-3" />
            Generate
          </Button>
        );
      default:
        return null;
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    });
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">RAG Queries</h2>
          <p className="text-muted-foreground">Manage queries through the RAG pipeline.</p>
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
          <h2 className="text-3xl font-bold tracking-tight">RAG Queries</h2>
          <p className="text-muted-foreground">Manage queries through the RAG pipeline.</p>
        </div>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3 text-destructive">
              <AlertCircle className="h-5 w-5" />
              <p>{error}</p>
            </div>
            <Button onClick={fetchQueries} variant="outline" className="mt-4">
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
        <h2 className="text-3xl font-bold tracking-tight">RAG Queries</h2>
        <p className="text-muted-foreground">Manage queries through the RAG pipeline.</p>
      </div>

      {/* Success/Error Messages */}
      {operationSuccess && (
        <Alert>
          <CheckCircle2 className="h-4 w-4" />
          <AlertDescription>{operationSuccess}</AlertDescription>
        </Alert>
      )}

      {operationError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{operationError}</AlertDescription>
        </Alert>
      )}

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Queries</CardTitle>
            <MessageSquare className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Ready</CardTitle>
            <CheckCircle2 className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{stats.ready}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending</CardTitle>
            <Clock className="h-4 w-4 text-amber-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-amber-600">{stats.pending}</div>
          </CardContent>
        </Card>
      </div>

      {/* New Query Input */}
      <Card>
        <CardHeader>
          <CardTitle>New Query</CardTitle>
          <CardDescription>
            Enter a new query to expand and process through the RAG pipeline.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-3">
            <Textarea
              value={newQuery}
              onChange={(e) => setNewQuery(e.target.value)}
              placeholder="Enter your query here... (e.g., What is working memory?)"
              className="flex-1 min-h-[80px] resize-none"
            />
            <Button
              onClick={handleNewQuery}
              disabled={!newQuery.trim()}
              className="gap-2 self-end"
            >
              <Plus className="h-4 w-4" />
              New
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Queries Table */}
      <Card>
        <CardHeader>
          <CardTitle>Queries</CardTitle>
          <CardDescription>
            All queries and their current pipeline status.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {queries.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <MessageSquare className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No queries found.</p>
              <p className="text-sm mt-2">Create a new query above to get started.</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[50%]">Query</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {queries.map((query) => (
                  <TableRow key={query.id}>
                    <TableCell
                      className="font-medium max-w-md"
                      style={{ wordBreak: "break-word", whiteSpace: "normal" }}
                    >
                      {query.original_query}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground whitespace-nowrap">
                      {formatDate(query.created_at)}
                    </TableCell>
                    <TableCell>
                      {getStatusBadge(query.status)}
                    </TableCell>
                    <TableCell className="text-right">
                      {getActionButton(query)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
