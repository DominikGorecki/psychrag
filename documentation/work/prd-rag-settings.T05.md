# T05: RAG Settings UI tab with preset management

## Context

- **PRD**: [prd-rag-settings.md](prd-rag-settings.md)
- **PRD Sections**: Technical Specification → Frontend Implementation (lines 387-558)
- **User value**: Provides an intuitive web interface for managing RAG configuration presets, allowing users to tune retrieval/consolidation/augmentation parameters without editing JSON or SQL.

## Outcome

When this ticket is done:
- Settings page has a new "RAG Settings" tab
- Users can view, create, edit, duplicate, and delete RAG config presets via UI
- Preset selector dropdown allows switching between presets
- Three collapsible sections organize parameters: Retrieval, Consolidation, Augmentation
- All 20+ parameters have appropriate inputs (number fields, sliders, toggles) with validation
- Default preset indicator shows which preset is active
- Save/Reset buttons provide clear state management
- Error messages guide users when validation fails or operations fail

## Scope

### In scope:
- Create TypeScript types in `psychrag_ui/src/types/rag-config.ts`
- Create component `psychrag_ui/src/components/settings/rag-config-tab.tsx`
- Update `psychrag_ui/src/app/settings/page.tsx` to add RAG Settings tab
- Implement preset management UI:
  - Preset selector dropdown
  - Create, rename, duplicate, delete presets
  - Set preset as default
- Implement parameter editing UI:
  - Three accordion sections (Retrieval, Consolidation, Augmentation)
  - Number inputs with min/max validation
  - Sliders for float parameters (mmr_lambda, entity_boost, coverage_threshold)
  - Toggle switches for boolean parameters
  - Tooltips with parameter descriptions
- State management for form data and API calls
- Error handling and user feedback

### Out of scope:
- Per-query config override UI (future enhancement)
- Config import/export (future enhancement)
- Config versioning/history UI (future enhancement)
- Parameter recommendations/presets wizard (future enhancement)
- A/B testing UI (future enhancement)

## Implementation plan

### Frontend - TypeScript Types

**File**: `psychrag_ui/src/types/rag-config.ts`

1. **Create comprehensive type definitions**:

```typescript
/**
 * TypeScript types for RAG configuration management.
 * Matches backend Pydantic schemas.
 */

export interface RagConfig {
  id: number;
  preset_name: string;
  is_default: boolean;
  description: string | null;
  config: RagConfigParams;
  created_at: string;
  updated_at: string;
}

export interface RagConfigParams {
  retrieval: RetrievalParams;
  consolidation: ConsolidationParams;
  augmentation: AugmentationParams;
}

export interface RetrievalParams {
  dense_limit: number;
  lexical_limit: number;
  rrf_k: number;
  top_k_rrf: number;
  top_n_final: number;
  entity_boost: number;
  min_word_count: number;
  min_char_count: number;
  min_content_length: number;
  enrich_lines_above: number;
  enrich_lines_below: number;
  mmr_lambda: number;
  reranker_batch_size: number;
  reranker_max_length: number;
}

export interface ConsolidationParams {
  coverage_threshold: number;
  line_gap: number;
  min_content_length: number;
  enrich_from_md: boolean;
}

export interface AugmentationParams {
  top_n_contexts: number;
}

// Request types
export interface RagConfigCreateRequest {
  preset_name: string;
  description?: string;
  is_default: boolean;
  config: RagConfigParams;
}

export interface RagConfigUpdateRequest {
  description?: string;
  config?: RagConfigParams;
}

// Validation constraints (matches backend)
export const PARAM_CONSTRAINTS = {
  retrieval: {
    dense_limit: { min: 1, max: 100, default: 19, description: "Max results per dense vector query" },
    lexical_limit: { min: 1, max: 50, default: 5, description: "Max results per lexical (BM25) query" },
    rrf_k: { min: 1, max: 100, default: 50, description: "RRF constant for rank fusion" },
    top_k_rrf: { min: 1, max: 200, default: 75, description: "Top candidates after RRF fusion" },
    top_n_final: { min: 1, max: 50, default: 17, description: "Final number of results after MMR" },
    entity_boost: { min: 0.0, max: 0.5, default: 0.05, step: 0.01, description: "Score boost per entity match" },
    min_word_count: { min: 0, max: 1000, default: 150, description: "Minimum words in chunk (0 to disable)" },
    min_char_count: { min: 0, max: 5000, default: 250, description: "Minimum characters in chunk (0 to disable)" },
    min_content_length: { min: 0, max: 5000, default: 750, description: "Min content length before enrichment" },
    enrich_lines_above: { min: 0, max: 50, default: 0, description: "Lines to add above chunk when enriching" },
    enrich_lines_below: { min: 0, max: 50, default: 13, description: "Lines to add below chunk when enriching" },
    mmr_lambda: { min: 0.0, max: 1.0, default: 0.7, step: 0.01, description: "MMR balance: relevance (1.0) vs diversity (0.0)" },
    reranker_batch_size: { min: 1, max: 32, default: 8, description: "Batch size for BGE reranker inference" },
    reranker_max_length: { min: 128, max: 1024, default: 512, description: "Max token length for reranker" },
  },
  consolidation: {
    coverage_threshold: { min: 0.0, max: 1.0, default: 0.5, step: 0.01, description: "% of parent coverage to replace with parent" },
    line_gap: { min: 0, max: 50, default: 7, description: "Max lines between chunks to merge them" },
    min_content_length: { min: 0, max: 5000, default: 350, description: "Min characters for final output inclusion" },
    enrich_from_md: { default: true, description: "Read content from markdown during consolidation" },
  },
  augmentation: {
    top_n_contexts: { min: 1, max: 20, default: 5, description: "Number of top contexts to include in prompt" },
  },
} as const;

// Helper to get default config
export function getDefaultConfig(): RagConfigParams {
  return {
    retrieval: {
      dense_limit: PARAM_CONSTRAINTS.retrieval.dense_limit.default,
      lexical_limit: PARAM_CONSTRAINTS.retrieval.lexical_limit.default,
      rrf_k: PARAM_CONSTRAINTS.retrieval.rrf_k.default,
      top_k_rrf: PARAM_CONSTRAINTS.retrieval.top_k_rrf.default,
      top_n_final: PARAM_CONSTRAINTS.retrieval.top_n_final.default,
      entity_boost: PARAM_CONSTRAINTS.retrieval.entity_boost.default,
      min_word_count: PARAM_CONSTRAINTS.retrieval.min_word_count.default,
      min_char_count: PARAM_CONSTRAINTS.retrieval.min_char_count.default,
      min_content_length: PARAM_CONSTRAINTS.retrieval.min_content_length.default,
      enrich_lines_above: PARAM_CONSTRAINTS.retrieval.enrich_lines_above.default,
      enrich_lines_below: PARAM_CONSTRAINTS.retrieval.enrich_lines_below.default,
      mmr_lambda: PARAM_CONSTRAINTS.retrieval.mmr_lambda.default,
      reranker_batch_size: PARAM_CONSTRAINTS.retrieval.reranker_batch_size.default,
      reranker_max_length: PARAM_CONSTRAINTS.retrieval.reranker_max_length.default,
    },
    consolidation: {
      coverage_threshold: PARAM_CONSTRAINTS.consolidation.coverage_threshold.default,
      line_gap: PARAM_CONSTRAINTS.consolidation.line_gap.default,
      min_content_length: PARAM_CONSTRAINTS.consolidation.min_content_length.default,
      enrich_from_md: PARAM_CONSTRAINTS.consolidation.enrich_from_md.default,
    },
    augmentation: {
      top_n_contexts: PARAM_CONSTRAINTS.augmentation.top_n_contexts.default,
    },
  };
}
```

### Frontend - RAG Config Tab Component

**File**: `psychrag_ui/src/components/settings/rag-config-tab.tsx`

2. **Create main component** (this is a large component, breaking into sections):

```typescript
"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Loader2Icon, AlertCircle, CheckCircle2, Star, Copy, Trash2 } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

import type {
  RagConfig,
  RagConfigParams,
  RagConfigCreateRequest,
  RagConfigUpdateRequest,
  RetrievalParams,
  ConsolidationParams,
  AugmentationParams,
} from "@/types/rag-config";
import { PARAM_CONSTRAINTS, getDefaultConfig } from "@/types/rag-config";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function RagConfigTab() {
  // State management
  const [presets, setPresets] = useState<RagConfig[]>([]);
  const [selectedPresetName, setSelectedPresetName] = useState<string | null>(null);
  const [currentConfig, setCurrentConfig] = useState<RagConfigParams | null>(null);
  const [originalConfig, setOriginalConfig] = useState<RagConfigParams | null>(null);
  const [description, setDescription] = useState<string>("");
  const [originalDescription, setOriginalDescription] = useState<string>("");

  // UI state
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Dialog state
  const [showNewPresetDialog, setShowNewPresetDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [newPresetName, setNewPresetName] = useState("");
  const [newPresetDescription, setNewPresetDescription] = useState("");

  // Fetch presets on mount
  useEffect(() => {
    fetchPresets();
  }, []);

  // Fetch all presets
  const fetchPresets = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`${API_BASE_URL}/api/rag-config/`);
      if (!response.ok) {
        throw new Error(`Failed to fetch presets: ${response.statusText}`);
      }
      const data: RagConfig[] = await response.json();
      setPresets(data);

      // Select default preset if none selected
      if (!selectedPresetName && data.length > 0) {
        const defaultPreset = data.find((p) => p.is_default) || data[0];
        loadPreset(defaultPreset);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load presets");
    } finally {
      setLoading(false);
    }
  };

  // Load a preset into the form
  const loadPreset = (preset: RagConfig) => {
    setSelectedPresetName(preset.preset_name);
    setCurrentConfig(preset.config);
    setOriginalConfig(JSON.parse(JSON.stringify(preset.config))); // Deep copy
    setDescription(preset.description || "");
    setOriginalDescription(preset.description || "");
    setSaveSuccess(false);
  };

  // Handle preset selection change
  const handlePresetChange = (presetName: string) => {
    const preset = presets.find((p) => p.preset_name === presetName);
    if (preset) {
      loadPreset(preset);
    }
  };

  // Create new preset
  const handleCreatePreset = async () => {
    if (!newPresetName.trim()) {
      setError("Preset name is required");
      return;
    }

    try {
      setSaving(true);
      setError(null);

      const createRequest: RagConfigCreateRequest = {
        preset_name: newPresetName,
        description: newPresetDescription || undefined,
        is_default: false,
        config: currentConfig || getDefaultConfig(),
      };

      const response = await fetch(`${API_BASE_URL}/api/rag-config/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(createRequest),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to create preset: ${response.statusText}`);
      }

      const newPreset: RagConfig = await response.json();

      // Refresh and select new preset
      await fetchPresets();
      loadPreset(newPreset);

      // Reset dialog
      setShowNewPresetDialog(false);
      setNewPresetName("");
      setNewPresetDescription("");
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create preset");
    } finally {
      setSaving(false);
    }
  };

  // Save current preset
  const handleSavePreset = async () => {
    if (!selectedPresetName || !currentConfig) return;

    try {
      setSaving(true);
      setError(null);

      const updateRequest: RagConfigUpdateRequest = {
        description: description || undefined,
        config: currentConfig,
      };

      const response = await fetch(
        `${API_BASE_URL}/api/rag-config/${encodeURIComponent(selectedPresetName)}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(updateRequest),
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to save preset: ${response.statusText}`);
      }

      const updatedPreset: RagConfig = await response.json();

      // Update local state
      setOriginalConfig(JSON.parse(JSON.stringify(currentConfig)));
      setOriginalDescription(description);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 2000);

      // Refresh preset list
      await fetchPresets();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save preset");
    } finally {
      setSaving(false);
    }
  };

  // Set preset as default
  const handleSetDefault = async () => {
    if (!selectedPresetName) return;

    try {
      setSaving(true);
      setError(null);

      const response = await fetch(
        `${API_BASE_URL}/api/rag-config/${encodeURIComponent(selectedPresetName)}/set-default`,
        { method: "PUT" }
      );

      if (!response.ok) {
        throw new Error(`Failed to set default: ${response.statusText}`);
      }

      await fetchPresets();
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to set default");
    } finally {
      setSaving(false);
    }
  };

  // Delete preset
  const handleDeletePreset = async () => {
    if (!selectedPresetName) return;

    try {
      setSaving(true);
      setError(null);

      const response = await fetch(
        `${API_BASE_URL}/api/rag-config/${encodeURIComponent(selectedPresetName)}`,
        { method: "DELETE" }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to delete preset: ${response.statusText}`);
      }

      // Refresh and select default
      await fetchPresets();
      setShowDeleteDialog(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete preset");
    } finally {
      setSaving(false);
    }
  };

  // Reset to original values
  const handleReset = () => {
    if (originalConfig) {
      setCurrentConfig(JSON.parse(JSON.stringify(originalConfig)));
      setDescription(originalDescription);
    }
  };

  // Check if form has unsaved changes
  const hasUnsavedChanges = () => {
    if (!originalConfig || !currentConfig) return false;
    return (
      JSON.stringify(currentConfig) !== JSON.stringify(originalConfig) ||
      description !== originalDescription
    );
  };

  // Update retrieval parameter
  const updateRetrievalParam = <K extends keyof RetrievalParams>(
    key: K,
    value: RetrievalParams[K]
  ) => {
    if (!currentConfig) return;
    setCurrentConfig({
      ...currentConfig,
      retrieval: { ...currentConfig.retrieval, [key]: value },
    });
  };

  // Update consolidation parameter
  const updateConsolidationParam = <K extends keyof ConsolidationParams>(
    key: K,
    value: ConsolidationParams[K]
  ) => {
    if (!currentConfig) return;
    setCurrentConfig({
      ...currentConfig,
      consolidation: { ...currentConfig.consolidation, [key]: value },
    });
  };

  // Update augmentation parameter
  const updateAugmentationParam = <K extends keyof AugmentationParams>(
    key: K,
    value: AugmentationParams[K]
  ) => {
    if (!currentConfig) return;
    setCurrentConfig({
      ...currentConfig,
      augmentation: { ...currentConfig.augmentation, [key]: value },
    });
  };

  // Get current preset
  const currentPreset = presets.find((p) => p.preset_name === selectedPresetName);
  const isDefault = currentPreset?.is_default || false;

  if (loading) {
    return (
      <Card>
        <CardContent className="pt-6 flex items-center justify-center">
          <Loader2Icon className="h-8 w-8 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header Card - Preset Selector */}
      <Card>
        <CardHeader>
          <CardTitle>RAG Configuration Presets</CardTitle>
          <CardDescription>
            Manage retrieval, consolidation, and augmentation parameters. Changes affect how the RAG
            pipeline processes queries.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {saveSuccess && (
            <Alert className="border-emerald-500/20 bg-emerald-500/10">
              <CheckCircle2 className="h-4 w-4 text-emerald-500" />
              <AlertDescription className="text-emerald-500">
                Changes saved successfully
              </AlertDescription>
            </Alert>
          )}

          <div className="flex items-center gap-3">
            <div className="flex-1">
              <Label htmlFor="preset-select">Active Preset</Label>
              <div className="flex items-center gap-2 mt-1.5">
                <Select value={selectedPresetName || ""} onValueChange={handlePresetChange}>
                  <SelectTrigger id="preset-select" className="w-full">
                    <SelectValue placeholder="Select preset..." />
                  </SelectTrigger>
                  <SelectContent>
                    {presets.map((preset) => (
                      <SelectItem key={preset.id} value={preset.preset_name}>
                        <div className="flex items-center gap-2">
                          {preset.preset_name}
                          {preset.is_default && (
                            <Star className="h-3 w-3 fill-yellow-500 text-yellow-500" />
                          )}
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="flex gap-2 pt-6">
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => setShowNewPresetDialog(true)}
                    >
                      <Copy className="h-4 w-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Duplicate current preset</TooltipContent>
                </Tooltip>
              </TooltipProvider>

              {!isDefault && (
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button variant="outline" size="icon" onClick={handleSetDefault}>
                        <Star className="h-4 w-4" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>Set as default preset</TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              )}
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Input
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe this preset's purpose..."
            />
          </div>
        </CardContent>
      </Card>

      {/* Parameters Card */}
      {currentConfig && (
        <Card>
          <CardHeader>
            <CardTitle>Parameters</CardTitle>
            <CardDescription>Configure RAG pipeline behavior</CardDescription>
          </CardHeader>
          <CardContent>
            <Accordion type="multiple" defaultValue={["retrieval"]} className="w-full">
              {/* Retrieval Section */}
              <AccordionItem value="retrieval">
                <AccordionTrigger className="text-lg font-semibold">
                  Retrieval Parameters
                </AccordionTrigger>
                <AccordionContent className="space-y-4 pt-4">
                  {/* Number inputs for retrieval params */}
                  <div className="grid grid-cols-2 gap-4">
                    {Object.entries(PARAM_CONSTRAINTS.retrieval).map(([key, constraint]) => {
                      const typedKey = key as keyof RetrievalParams;
                      const value = currentConfig.retrieval[typedKey];

                      // Float parameters use slider + input
                      if ("step" in constraint && constraint.step) {
                        return (
                          <div key={key} className="space-y-2 col-span-2">
                            <div className="flex justify-between">
                              <Label htmlFor={`retrieval-${key}`}>
                                {key.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
                              </Label>
                              <span className="text-sm text-muted-foreground">
                                {value.toFixed(2)}
                              </span>
                            </div>
                            <Slider
                              id={`retrieval-${key}`}
                              min={constraint.min}
                              max={constraint.max}
                              step={constraint.step}
                              value={[value as number]}
                              onValueChange={([v]) => updateRetrievalParam(typedKey, v as any)}
                            />
                            <p className="text-xs text-muted-foreground">
                              {constraint.description}
                            </p>
                          </div>
                        );
                      }

                      // Integer parameters use number input
                      return (
                        <div key={key} className="space-y-2">
                          <Label htmlFor={`retrieval-${key}`}>
                            {key.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
                          </Label>
                          <Input
                            id={`retrieval-${key}`}
                            type="number"
                            min={constraint.min}
                            max={constraint.max}
                            value={value as number}
                            onChange={(e) =>
                              updateRetrievalParam(typedKey, parseInt(e.target.value) as any)
                            }
                          />
                          <p className="text-xs text-muted-foreground">
                            {constraint.description}
                          </p>
                        </div>
                      );
                    })}
                  </div>
                </AccordionContent>
              </AccordionItem>

              {/* Consolidation Section */}
              <AccordionItem value="consolidation">
                <AccordionTrigger className="text-lg font-semibold">
                  Consolidation Parameters
                </AccordionTrigger>
                <AccordionContent className="space-y-4 pt-4">
                  <div className="grid grid-cols-2 gap-4">
                    {/* coverage_threshold - slider */}
                    <div className="space-y-2 col-span-2">
                      <div className="flex justify-between">
                        <Label>Coverage Threshold</Label>
                        <span className="text-sm text-muted-foreground">
                          {currentConfig.consolidation.coverage_threshold.toFixed(2)}
                        </span>
                      </div>
                      <Slider
                        min={PARAM_CONSTRAINTS.consolidation.coverage_threshold.min}
                        max={PARAM_CONSTRAINTS.consolidation.coverage_threshold.max}
                        step={PARAM_CONSTRAINTS.consolidation.coverage_threshold.step}
                        value={[currentConfig.consolidation.coverage_threshold]}
                        onValueChange={([v]) => updateConsolidationParam("coverage_threshold", v)}
                      />
                      <p className="text-xs text-muted-foreground">
                        {PARAM_CONSTRAINTS.consolidation.coverage_threshold.description}
                      </p>
                    </div>

                    {/* line_gap */}
                    <div className="space-y-2">
                      <Label>Line Gap</Label>
                      <Input
                        type="number"
                        min={PARAM_CONSTRAINTS.consolidation.line_gap.min}
                        max={PARAM_CONSTRAINTS.consolidation.line_gap.max}
                        value={currentConfig.consolidation.line_gap}
                        onChange={(e) =>
                          updateConsolidationParam("line_gap", parseInt(e.target.value))
                        }
                      />
                      <p className="text-xs text-muted-foreground">
                        {PARAM_CONSTRAINTS.consolidation.line_gap.description}
                      </p>
                    </div>

                    {/* min_content_length */}
                    <div className="space-y-2">
                      <Label>Min Content Length</Label>
                      <Input
                        type="number"
                        min={PARAM_CONSTRAINTS.consolidation.min_content_length.min}
                        max={PARAM_CONSTRAINTS.consolidation.min_content_length.max}
                        value={currentConfig.consolidation.min_content_length}
                        onChange={(e) =>
                          updateConsolidationParam("min_content_length", parseInt(e.target.value))
                        }
                      />
                      <p className="text-xs text-muted-foreground">
                        {PARAM_CONSTRAINTS.consolidation.min_content_length.description}
                      </p>
                    </div>

                    {/* enrich_from_md - toggle */}
                    <div className="space-y-2 col-span-2">
                      <div className="flex items-center justify-between">
                        <div className="space-y-0.5">
                          <Label>Enrich From Markdown</Label>
                          <p className="text-xs text-muted-foreground">
                            {PARAM_CONSTRAINTS.consolidation.enrich_from_md.description}
                          </p>
                        </div>
                        <Switch
                          checked={currentConfig.consolidation.enrich_from_md}
                          onCheckedChange={(checked) =>
                            updateConsolidationParam("enrich_from_md", checked)
                          }
                        />
                      </div>
                    </div>
                  </div>
                </AccordionContent>
              </AccordionItem>

              {/* Augmentation Section */}
              <AccordionItem value="augmentation">
                <AccordionTrigger className="text-lg font-semibold">
                  Augmentation Parameters
                </AccordionTrigger>
                <AccordionContent className="space-y-4 pt-4">
                  <div className="space-y-2">
                    <Label>Top N Contexts</Label>
                    <Input
                      type="number"
                      min={PARAM_CONSTRAINTS.augmentation.top_n_contexts.min}
                      max={PARAM_CONSTRAINTS.augmentation.top_n_contexts.max}
                      value={currentConfig.augmentation.top_n_contexts}
                      onChange={(e) =>
                        updateAugmentationParam("top_n_contexts", parseInt(e.target.value))
                      }
                    />
                    <p className="text-xs text-muted-foreground">
                      {PARAM_CONSTRAINTS.augmentation.top_n_contexts.description}
                    </p>
                  </div>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          </CardContent>
        </Card>
      )}

      {/* Action Buttons */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div className="flex gap-2">
              <Button onClick={handleSavePreset} disabled={saving || !hasUnsavedChanges()}>
                {saving ? (
                  <>
                    <Loader2Icon className="h-4 w-4 animate-spin mr-2" />
                    Saving...
                  </>
                ) : (
                  "Save Changes"
                )}
              </Button>
              <Button
                variant="outline"
                onClick={handleReset}
                disabled={!hasUnsavedChanges()}
              >
                Reset
              </Button>
            </div>

            {!isDefault && (
              <Button
                variant="destructive"
                onClick={() => setShowDeleteDialog(true)}
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Delete Preset
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* New Preset Dialog */}
      <AlertDialog open={showNewPresetDialog} onOpenChange={setShowNewPresetDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Create New Preset</AlertDialogTitle>
            <AlertDialogDescription>
              Create a new preset based on the current configuration.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="new-preset-name">Preset Name</Label>
              <Input
                id="new-preset-name"
                value={newPresetName}
                onChange={(e) => setNewPresetName(e.target.value)}
                placeholder="e.g., Fast Retrieval"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="new-preset-description">Description</Label>
              <Input
                id="new-preset-description"
                value={newPresetDescription}
                onChange={(e) => setNewPresetDescription(e.target.value)}
                placeholder="Describe the preset..."
              />
            </div>
          </div>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleCreatePreset}>Create</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Preset</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete "{selectedPresetName}"? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDeletePreset} className="bg-destructive">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
```

### Frontend - Settings Page Update

**File**: `psychrag_ui/src/app/settings/page.tsx`

3. **Add RAG Settings tab**:

```typescript
// Add import at top
import { RagConfigTab } from "@/components/settings/rag-config-tab";

// Update defaultTab to include "rag"
const defaultTab = tabParam && ["init", "models", "database", "paths", "templates", "rag"].includes(tabParam)
  ? tabParam
  : "init";

// Add tab trigger in TabsList (around line 343)
<TabsList>
  <TabsTrigger value="init">Init/Status</TabsTrigger>
  <TabsTrigger value="models">Models</TabsTrigger>
  <TabsTrigger value="database">Database</TabsTrigger>
  <TabsTrigger value="paths">Paths</TabsTrigger>
  <TabsTrigger value="templates">Templates</TabsTrigger>
  <TabsTrigger value="rag">RAG Settings</TabsTrigger>  {/* Add this */}
</TabsList>

// Add tab content after Templates tab (around line 780)
<TabsContent value="rag" className="mt-4">
  <RagConfigTab />
</TabsContent>
```

## Unit tests

**File**: `psychrag_ui/src/components/settings/__tests__/rag-config-tab.test.tsx`

Create tests for the component (using React Testing Library):

```typescript
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { RagConfigTab } from "../rag-config-tab";

// Mock fetch
global.fetch = jest.fn();

describe("RagConfigTab", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders loading state", () => {
    (global.fetch as jest.Mock).mockImplementation(() => new Promise(() => {}));
    render(<RagConfigTab />);
    expect(screen.getByRole("progressbar")).toBeInTheDocument();
  });

  it("fetches and displays presets", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => [
        {
          id: 1,
          preset_name: "Default",
          is_default: true,
          description: "Default config",
          config: { retrieval: {}, consolidation: {}, augmentation: {} },
        },
      ],
    });

    render(<RagConfigTab />);

    await waitFor(() => {
      expect(screen.getByText("Default")).toBeInTheDocument();
    });
  });

  it("handles preset selection", async () => {
    // Test preset switching
  });

  it("validates parameter inputs", async () => {
    // Test min/max validation
  });

  it("handles save operation", async () => {
    // Test save flow
  });

  it("handles delete operation", async () => {
    // Test delete flow
  });
});
```

## Manual test plan

### Prerequisites:
1. Backend API running with T03 endpoints
2. At least one default RAG config preset in database
3. Frontend dev server running: `npm run dev`

### Test scenarios:

**1. View presets**
- Navigate to Settings → RAG Settings tab
- Expected: See preset selector with at least "Default" preset
- Expected: Default preset has star icon indicator

**2. View parameters**
- Select a preset
- Expected: See three accordion sections (Retrieval, Consolidation, Augmentation)
- Expand Retrieval section
- Expected: See ~14 parameter inputs with current values

**3. Edit parameters**
- Change `dense_limit` from 19 to 25
- Expected: Save button becomes enabled
- Expected: Form shows unsaved changes indicator

**4. Save changes**
- Click "Save Changes"
- Expected: Success message appears
- Expected: Changes persist after refresh

**5. Reset changes**
- Change a parameter
- Click "Reset"
- Expected: Parameter reverts to saved value
- Expected: Save button becomes disabled

**6. Create new preset**
- Click "Duplicate" icon button
- Enter name "Fast"
- Enter description "Faster retrieval with fewer candidates"
- Click "Create"
- Expected: New preset appears in dropdown
- Expected: New preset is selected automatically

**7. Set as default**
- Select non-default preset
- Click star icon button
- Expected: Preset becomes default (star appears in dropdown)
- Expected: Old default loses default status

**8. Delete preset**
- Select non-default preset
- Click "Delete Preset"
- Confirm deletion
- Expected: Preset removed from list
- Expected: Default preset auto-selected

**9. Validation errors**
- Try to set `dense_limit` to 999 (exceeds max 100)
- Expected: Input shows validation error or reverts
- Try to create preset with empty name
- Expected: Error message shown

**10. Slider controls**
- Adjust `mmr_lambda` slider
- Expected: Value updates smoothly
- Expected: Value displays next to slider (e.g., "0.75")

**11. Toggle controls**
- Toggle `enrich_from_md` switch
- Expected: Switch changes state
- Expected: Save button enabled

**12. Delete default protection**
- Select default preset
- Expected: Delete button hidden or disabled

## Dependencies and sequencing

### Dependencies:
- **Requires**: T03 (API endpoints must be complete)
- **Optional**: T04 (integration - not required for UI development/testing)

### Sequencing notes:
- Can start development after T03 API is deployed to test environment
- This is the final ticket in the sequence
- Once complete, full end-to-end flow is available: UI → API → Database → RAG pipeline

## Clarifications and assumptions

### Assumptions:
1. **UI framework**: Using existing shadcn/ui components (Button, Input, Select, Slider, Switch, Accordion)
2. **State management**: Using React useState (no global state like Redux needed)
3. **API calls**: Using fetch API directly (no axios or other HTTP client)
4. **Error handling**: Displaying errors in Alert components, not toast notifications
5. **Validation**: Client-side validation matches backend Pydantic constraints
6. **Unsaved changes**: Track changes but don't warn on navigation (user responsibility)
7. **Preset duplication**: "New Preset" button duplicates current config, not cloning existing preset
8. **Float display**: Show 2 decimal places for float parameters (mmr_lambda, entity_boost, etc.)

### Open questions (non-blocking):
1. Should we add a "Discard changes" confirmation dialog when switching presets with unsaved changes?
2. Should we add preset export/import buttons (download/upload JSON)?
3. Should we add a "Restore defaults" button to reset to PRD default values?
4. Should we add parameter tooltips with more detailed explanations?
5. Should we add visual indicators for which parameters differ from default?
6. Should we add preset search/filter if user has many presets?

### Implementer notes:

> **Before implementing**:
> - Review existing settings components (`templates-tab.tsx`) for code style consistency
> - Ensure T03 API is deployed and accessible
> - Test all API endpoints in Swagger UI first
> - Set up shadcn/ui components if not already installed

> **During implementation**:
> - Build component incrementally: preset selector → parameters → actions
> - Test each section individually before moving to next
> - Use TypeScript strictly - don't use `any` types
> - Ensure all inputs are controlled components (value + onChange)
> - Test validation on every parameter input
> - Handle loading, error, and success states for all API calls

> **After implementation**:
> - Test entire flow multiple times
> - Test with slow network (throttle in DevTools)
> - Test error cases: API errors, validation errors
> - Verify all buttons are properly disabled during loading
> - Test keyboard navigation and accessibility
> - Verify responsive design (mobile, tablet, desktop)
> - Test with actual backend API, not just mocks
