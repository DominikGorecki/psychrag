"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2Icon, CheckCircle2, XCircle, AlertCircle } from "lucide-react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Types matching API schemas
interface DatabaseConfig {
  admin_user: string;
  host: string;
  port: number;
  db_name: string;
  app_user: string;
}

interface DbHealthCheckResult {
  name: string;
  passed: boolean;
  message: string;
  details: string | null;
}

interface DbHealthCheckResponse {
  results: DbHealthCheckResult[];
  all_passed: boolean;
  connection_ok: boolean;
}

export default function InitPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [dbSettings, setDbSettings] = useState<DatabaseConfig | null>(null);
  const [dbSettingsError, setDbSettingsError] = useState<string | null>(null);
  const [healthResults, setHealthResults] = useState<DbHealthCheckResponse | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [healthLoading, setHealthLoading] = useState(false);

  // Check if required DB settings are present
  const hasRequiredDbSettings = dbSettings && 
    dbSettings.db_name && 
    dbSettings.app_user && 
    dbSettings.admin_user;

  // Fetch database settings on mount
  useEffect(() => {
    fetchDbSettings();
  }, []);

  // Fetch health checks when settings are available
  useEffect(() => {
    if (hasRequiredDbSettings) {
      fetchHealthChecks();
    }
  }, [hasRequiredDbSettings]);

  const fetchDbSettings = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/settings/database`);
      if (!response.ok) {
        throw new Error(`Failed to fetch settings: ${response.statusText}`);
      }
      const data: DatabaseConfig = await response.json();
      setDbSettings(data);
      setDbSettingsError(null);
    } catch (err) {
      setDbSettingsError(err instanceof Error ? err.message : "Failed to load settings");
    } finally {
      setLoading(false);
    }
  };

  const fetchHealthChecks = async () => {
    try {
      setHealthLoading(true);
      setHealthError(null);
      const response = await fetch(`${API_BASE_URL}/init/db-health`);
      if (!response.ok) {
        throw new Error(`Failed to fetch health: ${response.statusText}`);
      }
      const data: DbHealthCheckResponse = await response.json();
      setHealthResults(data);
    } catch (err) {
      setHealthError(err instanceof Error ? err.message : "Failed to check health");
    } finally {
      setHealthLoading(false);
    }
  };

  const handleInitialize = async () => {
    // TODO: Call init database endpoint
    console.log("Initialize database");
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2Icon className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Initialization</h2>
        <p className="text-muted-foreground">System status and setup operations.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {/* Database Health Card */}
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>Database Health</CardTitle>
            <CardDescription>
              {dbSettings ? (
                <span>
                  {dbSettings.db_name} @ {dbSettings.host}:{dbSettings.port}
                </span>
              ) : (
                "Connection status and schema checks"
              )}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {/* Show error if settings failed to load */}
            {dbSettingsError && (
              <div className="flex items-center gap-2 text-destructive mb-4">
                <AlertCircle className="h-4 w-4" />
                <span className="text-sm">{dbSettingsError}</span>
              </div>
            )}

            {/* Show warning if required settings are missing */}
            {!hasRequiredDbSettings && !dbSettingsError && (
              <div className="flex items-center justify-between py-4 border-b">
                <div className="flex items-center gap-3">
                  <AlertCircle className="h-5 w-5 text-amber-500" />
                  <span className="text-sm">Database settings incomplete</span>
                </div>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => router.push("/settings")}
                >
                  Add DB Settings
                </Button>
              </div>
            )}

            {/* Health check results */}
            {hasRequiredDbSettings && (
              <>
                {healthLoading && (
                  <div className="flex items-center gap-2 py-4">
                    <Loader2Icon className="h-4 w-4 animate-spin" />
                    <span className="text-sm text-muted-foreground">Running health checks...</span>
                  </div>
                )}

                {healthError && (
                  <div className="flex items-center gap-2 text-destructive py-4">
                    <XCircle className="h-4 w-4" />
                    <span className="text-sm">{healthError}</span>
                    <Button variant="ghost" size="sm" onClick={fetchHealthChecks}>
                      Retry
                    </Button>
                  </div>
                )}

                {healthResults && (
                  <div className="space-y-1">
                    {healthResults.results.map((result, index) => (
                      <div 
                        key={index} 
                        className="flex items-center gap-3 py-1.5 text-sm"
                      >
                        {result.passed ? (
                          <CheckCircle2 className="h-4 w-4 text-emerald-500 flex-shrink-0" />
                        ) : (
                          <XCircle className="h-4 w-4 text-destructive flex-shrink-0" />
                        )}
                        <span className={result.passed ? "text-foreground" : "text-destructive"}>
                          {result.name}
                        </span>
                        <span className="text-muted-foreground text-xs truncate">
                          — {result.message}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>

        {/* Actions Card */}
        <Card>
          <CardHeader>
            <CardTitle>Actions</CardTitle>
            <CardDescription>Setup and maintenance tasks</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {/* Show "Add DB Settings" if settings are missing */}
            {!hasRequiredDbSettings && (
              <Button 
                className="w-full" 
                variant="default"
                onClick={() => router.push("/settings")}
              >
                Add DB Settings
              </Button>
            )}

            {/* Show "Initialize" only if connection fails */}
            {hasRequiredDbSettings && healthResults && !healthResults.connection_ok && (
              <Button 
                className="w-full" 
                variant="default"
                onClick={handleInitialize}
              >
                Initialize Database
              </Button>
            )}

            {/* Show "Check Connections" button */}
            {hasRequiredDbSettings && (
              <Button 
                className="w-full" 
                variant="outline"
                onClick={fetchHealthChecks}
                disabled={healthLoading}
              >
                {healthLoading ? (
                  <>
                    <Loader2Icon className="h-4 w-4 animate-spin mr-2" />
                    Checking...
                  </>
                ) : (
                  "Check Connections"
                )}
              </Button>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
