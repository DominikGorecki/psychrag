"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertCircle, CheckCircle2, ChevronLeft, Loader2Icon } from "lucide-react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface FormData {
  title: string;
  authors: string;
  year: string;
  publisher: string;
  isbn: string;
  edition: string;
}

interface FormErrors {
  title?: string;
  year?: string;
}

export default function AddWorkPage() {
  const params = useParams();
  const router = useRouter();
  const fileId = params.id as string;

  const [formData, setFormData] = useState<FormData>({
    title: "",
    authors: "",
    year: "",
    publisher: "",
    isbn: "",
    edition: "",
  });

  const [formErrors, setFormErrors] = useState<FormErrors>({});
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const validateForm = (): boolean => {
    const errors: FormErrors = {};

    // Title is required
    if (!formData.title.trim()) {
      errors.title = "Title is required";
    } else if (formData.title.length > 500) {
      errors.title = "Title must be 500 characters or less";
    }

    // Year must be 4 digits if provided
    if (formData.year.trim()) {
      const yearNum = parseInt(formData.year);
      if (isNaN(yearNum) || yearNum < 1000 || yearNum > 9999) {
        errors.year = "Year must be a 4-digit number (1000-9999)";
      }
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate form
    if (!validateForm()) {
      return;
    }

    setSubmitting(true);
    setSubmitError(null);

    try {
      // Prepare request body
      const requestBody: any = {
        title: formData.title.trim(),
      };

      // Add optional fields only if they have values
      if (formData.authors.trim()) {
        requestBody.authors = formData.authors.trim();
      }
      if (formData.year.trim()) {
        requestBody.year = parseInt(formData.year);
      }
      if (formData.publisher.trim()) {
        requestBody.publisher = formData.publisher.trim();
      }
      if (formData.isbn.trim()) {
        requestBody.isbn = formData.isbn.trim();
      }
      if (formData.edition.trim()) {
        requestBody.edition = formData.edition.trim();
      }

      const response = await fetch(
        `${API_BASE_URL}/conv/add-to-database/${fileId}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(requestBody),
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to add work: ${response.statusText}`);
      }

      const data = await response.json();
      
      // Show success message
      setSuccess(true);
      
      // Navigate back to conv page after a short delay
      setTimeout(() => {
        router.push(`/conv/${fileId}`);
      }, 2000);
      
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : "Failed to add work to database");
    } finally {
      setSubmitting(false);
    }
  };

  const handleCancel = () => {
    router.push(`/conv/${fileId}`);
  };

  const handleFieldChange = (field: keyof FormData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    // Clear error for this field when user starts typing
    if (formErrors[field as keyof FormErrors]) {
      setFormErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[field as keyof FormErrors];
        return newErrors;
      });
    }
  };

  if (success) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center space-y-4">
          <CheckCircle2 className="h-16 w-16 text-green-500 mx-auto" />
          <h2 className="text-2xl font-bold">Work Added Successfully!</h2>
          <p className="text-muted-foreground">Redirecting...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container max-w-3xl py-8">
      {/* Header */}
      <div className="mb-6">
        <Button
          onClick={handleCancel}
          variant="ghost"
          size="sm"
          className="gap-1 mb-4"
        >
          <ChevronLeft className="h-4 w-4" />
          Back
        </Button>
        
        <h1 className="text-3xl font-bold tracking-tight">Add to Database</h1>
        <p className="text-muted-foreground mt-2">
          Enter bibliographic information for this work
        </p>
      </div>

      {/* Form Card */}
      <Card>
        <CardHeader>
          <CardTitle>Work Metadata</CardTitle>
          <CardDescription>
            File ID: <code className="text-xs bg-muted px-1.5 py-0.5 rounded">{fileId}</code>
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Title - Required */}
            <div className="space-y-2">
              <Label htmlFor="title" className="required">
                Title <span className="text-destructive">*</span>
              </Label>
              <Input
                id="title"
                type="text"
                value={formData.title}
                onChange={(e) => handleFieldChange("title", e.target.value)}
                placeholder="Enter work title"
                className={formErrors.title ? "border-destructive" : ""}
              />
              {formErrors.title && (
                <p className="text-sm text-destructive">{formErrors.title}</p>
              )}
            </div>

            {/* Authors - Optional */}
            <div className="space-y-2">
              <Label htmlFor="authors">Authors</Label>
              <Input
                id="authors"
                type="text"
                value={formData.authors}
                onChange={(e) => handleFieldChange("authors", e.target.value)}
                placeholder="e.g., John Smith, Jane Doe"
              />
              <p className="text-xs text-muted-foreground">
                Optional: Enter author names separated by commas
              </p>
            </div>

            {/* Year - Optional */}
            <div className="space-y-2">
              <Label htmlFor="year">Year</Label>
              <Input
                id="year"
                type="number"
                value={formData.year}
                onChange={(e) => handleFieldChange("year", e.target.value)}
                placeholder="e.g., 2020"
                min="1000"
                max="9999"
                className={formErrors.year ? "border-destructive" : ""}
              />
              {formErrors.year && (
                <p className="text-sm text-destructive">{formErrors.year}</p>
              )}
              <p className="text-xs text-muted-foreground">
                Optional: 4-digit year of publication
              </p>
            </div>

            {/* Publisher - Optional */}
            <div className="space-y-2">
              <Label htmlFor="publisher">Publisher</Label>
              <Input
                id="publisher"
                type="text"
                value={formData.publisher}
                onChange={(e) => handleFieldChange("publisher", e.target.value)}
                placeholder="e.g., Psychology Press"
              />
              <p className="text-xs text-muted-foreground">
                Optional: Publisher name
              </p>
            </div>

            {/* ISBN - Optional */}
            <div className="space-y-2">
              <Label htmlFor="isbn">ISBN</Label>
              <Input
                id="isbn"
                type="text"
                value={formData.isbn}
                onChange={(e) => handleFieldChange("isbn", e.target.value)}
                placeholder="e.g., 978-0-12-345678-9"
              />
              <p className="text-xs text-muted-foreground">
                Optional: ISBN for books
              </p>
            </div>

            {/* Edition - Optional */}
            <div className="space-y-2">
              <Label htmlFor="edition">Edition</Label>
              <Input
                id="edition"
                type="text"
                value={formData.edition}
                onChange={(e) => handleFieldChange("edition", e.target.value)}
                placeholder="e.g., 3rd Edition"
              />
              <p className="text-xs text-muted-foreground">
                Optional: Edition information
              </p>
            </div>

            {/* Error Display */}
            {submitError && (
              <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/20">
                <div className="flex items-start gap-2 text-destructive">
                  <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
                  <p className="text-sm">{submitError}</p>
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-3 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={handleCancel}
                disabled={submitting}
                className="flex-1"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={submitting}
                className="flex-1"
              >
                {submitting ? (
                  <>
                    <Loader2Icon className="h-4 w-4 animate-spin mr-2" />
                    Adding...
                  </>
                ) : (
                  "Add to Database"
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}



