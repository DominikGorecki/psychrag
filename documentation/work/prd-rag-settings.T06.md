# T06: Frontend tests for RAG Settings UI

## Context

- **PRD**: [prd-rag-settings.md](prd-rag-settings.md)
- **Parent Ticket**: [prd-rag-settings.T05.md](prd-rag-settings.T05.md)
- **User value**: Ensures the RAG Settings UI is robust, reliable, and free of regressions through comprehensive automated testing.

## Outcome

When this ticket is done:
- RAG Settings tab component has full test coverage using React Testing Library
- All user interactions are tested (preset selection, parameter editing, save/reset/delete)
- API integration tests verify correct request/response handling
- Error states and edge cases are covered
- Tests run successfully in CI/CD pipeline

## Scope

### In scope:
- Unit tests for `rag-config-tab.tsx` component
- Test file: `psychrag_ui/src/components/settings/__tests__/rag-config-tab.test.tsx`
- Mock API responses using Jest
- Test coverage for:
  - Component rendering (loading, error, success states)
  - Preset management (fetch, select, create, delete, set default)
  - Parameter editing (retrieval, consolidation, augmentation)
  - Form validation
  - Save/reset functionality
  - Error handling

### Out of scope:
- E2E tests (use Playwright/Cypress if needed later)
- Performance tests
- Accessibility tests (can be added in future ticket)
- Visual regression tests

## Implementation plan

### Frontend Tests

**File**: `psychrag_ui/src/components/settings/__tests__/rag-config-tab.test.tsx`

Create comprehensive test suite using React Testing Library and Jest:

```typescript
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { RagConfigTab } from "../rag-config-tab";

// Mock fetch globally
global.fetch = jest.fn();

const mockPresets = [
  {
    id: 1,
    preset_name: "Default",
    is_default: true,
    description: "Default balanced configuration",
    config: {
      retrieval: {
        dense_limit: 19,
        lexical_limit: 5,
        rrf_k: 50,
        top_k_rrf: 75,
        top_n_final: 17,
        entity_boost: 0.05,
        min_word_count: 150,
        min_char_count: 250,
        min_content_length: 750,
        enrich_lines_above: 0,
        enrich_lines_below: 13,
        mmr_lambda: 0.7,
        reranker_batch_size: 8,
        reranker_max_length: 512,
      },
      consolidation: {
        coverage_threshold: 0.5,
        line_gap: 7,
        min_content_length: 350,
        enrich_from_md: true,
      },
      augmentation: {
        top_n_contexts: 5,
      },
    },
    created_at: "2025-01-01T00:00:00",
    updated_at: "2025-01-01T00:00:00",
  },
  {
    id: 2,
    preset_name: "Fast",
    is_default: false,
    description: "Faster retrieval with fewer candidates",
    config: {
      retrieval: {
        dense_limit: 10,
        lexical_limit: 3,
        rrf_k: 50,
        top_k_rrf: 50,
        top_n_final: 10,
        entity_boost: 0.05,
        min_word_count: 100,
        min_char_count: 200,
        min_content_length: 500,
        enrich_lines_above: 0,
        enrich_lines_below: 10,
        mmr_lambda: 0.6,
        reranker_batch_size: 4,
        reranker_max_length: 256,
      },
      consolidation: {
        coverage_threshold: 0.4,
        line_gap: 5,
        min_content_length: 250,
        enrich_from_md: false,
      },
      augmentation: {
        top_n_contexts: 3,
      },
    },
    created_at: "2025-01-02T00:00:00",
    updated_at: "2025-01-02T00:00:00",
  },
];

describe("RagConfigTab", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("Loading and Error States", () => {
    it("renders loading state while fetching presets", () => {
      (global.fetch as jest.Mock).mockImplementation(() => new Promise(() => {}));
      render(<RagConfigTab />);
      expect(screen.getByTestId("loader")).toBeInTheDocument();
    });

    it("displays error message when fetch fails", async () => {
      (global.fetch as jest.Mock).mockRejectedValueOnce(new Error("Network error"));
      render(<RagConfigTab />);

      await waitFor(() => {
        expect(screen.getByText(/failed to load presets/i)).toBeInTheDocument();
      });
    });

    it("displays error message with API error details", async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        statusText: "Internal Server Error",
      });
      render(<RagConfigTab />);

      await waitFor(() => {
        expect(screen.getByText(/failed to fetch presets/i)).toBeInTheDocument();
      });
    });
  });

  describe("Preset Display", () => {
    beforeEach(() => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockPresets,
      });
    });

    it("fetches and displays presets", async () => {
      render(<RagConfigTab />);

      await waitFor(() => {
        expect(screen.getByText("Default")).toBeInTheDocument();
        expect(screen.getByText("Fast")).toBeInTheDocument();
      });
    });

    it("selects default preset on initial load", async () => {
      render(<RagConfigTab />);

      await waitFor(() => {
        const selector = screen.getByRole("combobox");
        expect(selector).toHaveValue("Default");
      });
    });

    it("shows star icon for default preset", async () => {
      render(<RagConfigTab />);

      await waitFor(() => {
        const star = screen.getAllByTestId("star-icon")[0];
        expect(star).toBeInTheDocument();
      });
    });
  });

  describe("Preset Selection", () => {
    beforeEach(() => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockPresets,
      });
    });

    it("loads preset configuration when selected", async () => {
      render(<RagConfigTab />);

      await waitFor(() => {
        expect(screen.getByText("Default")).toBeInTheDocument();
      });

      // Select "Fast" preset
      const selector = screen.getByRole("combobox");
      fireEvent.change(selector, { target: { value: "Fast" } });

      await waitFor(() => {
        expect(screen.getByDisplayValue("Faster retrieval with fewer candidates")).toBeInTheDocument();
      });
    });
  });

  describe("Parameter Editing", () => {
    beforeEach(() => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockPresets,
      });
    });

    it("enables save button when parameters are changed", async () => {
      render(<RagConfigTab />);

      await waitFor(() => {
        expect(screen.getByText("Default")).toBeInTheDocument();
      });

      // Change dense_limit
      const denseLimit = screen.getByLabelText(/dense limit/i);
      fireEvent.change(denseLimit, { target: { value: "25" } });

      await waitFor(() => {
        const saveButton = screen.getByRole("button", { name: /save changes/i });
        expect(saveButton).not.toBeDisabled();
      });
    });

    it("disables save button when no changes", async () => {
      render(<RagConfigTab />);

      await waitFor(() => {
        const saveButton = screen.getByRole("button", { name: /save changes/i });
        expect(saveButton).toBeDisabled();
      });
    });

    it("validates number input constraints", async () => {
      render(<RagConfigTab />);

      await waitFor(() => {
        expect(screen.getByText("Default")).toBeInTheDocument();
      });

      // Try to set dense_limit above max (100)
      const denseLimit = screen.getByLabelText(/dense limit/i) as HTMLInputElement;
      expect(denseLimit.max).toBe("100");
      expect(denseLimit.min).toBe("1");
    });
  });

  describe("Save Functionality", () => {
    beforeEach(() => {
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockPresets,
        });
    });

    it("saves changes successfully", async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ ...mockPresets[0], description: "Updated" }),
      });

      render(<RagConfigTab />);

      await waitFor(() => {
        expect(screen.getByText("Default")).toBeInTheDocument();
      });

      // Change description
      const descInput = screen.getByLabelText(/description/i);
      fireEvent.change(descInput, { target: { value: "Updated description" } });

      // Click save
      const saveButton = screen.getByRole("button", { name: /save changes/i });
      fireEvent.click(saveButton);

      await waitFor(() => {
        expect(screen.getByText(/changes saved successfully/i)).toBeInTheDocument();
      });
    });

    it("displays error on save failure", async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        statusText: "Bad Request",
        json: async () => ({ detail: "Validation error" }),
      });

      render(<RagConfigTab />);

      await waitFor(() => {
        expect(screen.getByText("Default")).toBeInTheDocument();
      });

      // Make a change and save
      const descInput = screen.getByLabelText(/description/i);
      fireEvent.change(descInput, { target: { value: "Updated" } });

      const saveButton = screen.getByRole("button", { name: /save changes/i });
      fireEvent.click(saveButton);

      await waitFor(() => {
        expect(screen.getByText(/validation error/i)).toBeInTheDocument();
      });
    });
  });

  describe("Reset Functionality", () => {
    beforeEach(() => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockPresets,
      });
    });

    it("resets changes to original values", async () => {
      render(<RagConfigTab />);

      await waitFor(() => {
        expect(screen.getByText("Default")).toBeInTheDocument();
      });

      // Change description
      const descInput = screen.getByLabelText(/description/i) as HTMLInputElement;
      const originalValue = descInput.value;
      fireEvent.change(descInput, { target: { value: "Changed" } });

      // Click reset
      const resetButton = screen.getByRole("button", { name: /reset/i });
      fireEvent.click(resetButton);

      await waitFor(() => {
        expect(descInput.value).toBe(originalValue);
      });
    });
  });

  describe("Create Preset", () => {
    beforeEach(() => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockPresets,
      });
    });

    it("opens create dialog when duplicate button clicked", async () => {
      render(<RagConfigTab />);

      await waitFor(() => {
        expect(screen.getByText("Default")).toBeInTheDocument();
      });

      const duplicateButton = screen.getByRole("button", { name: /duplicate/i });
      fireEvent.click(duplicateButton);

      await waitFor(() => {
        expect(screen.getByText(/create new preset/i)).toBeInTheDocument();
      });
    });

    it("creates new preset successfully", async () => {
      const newPreset = {
        ...mockPresets[0],
        id: 3,
        preset_name: "New Preset",
        is_default: false,
      };

      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({ ok: true, json: async () => newPreset })
        .mockResolvedValueOnce({ ok: true, json: async () => [...mockPresets, newPreset] });

      render(<RagConfigTab />);

      await waitFor(() => {
        expect(screen.getByText("Default")).toBeInTheDocument();
      });

      // Open dialog
      const duplicateButton = screen.getByRole("button", { name: /duplicate/i });
      fireEvent.click(duplicateButton);

      // Enter preset name
      const nameInput = screen.getByLabelText(/preset name/i);
      fireEvent.change(nameInput, { target: { value: "New Preset" } });

      // Click create
      const createButton = screen.getByRole("button", { name: /create/i });
      fireEvent.click(createButton);

      await waitFor(() => {
        expect(screen.getByText(/changes saved successfully/i)).toBeInTheDocument();
      });
    });

    it("shows error when creating preset with empty name", async () => {
      render(<RagConfigTab />);

      await waitFor(() => {
        expect(screen.getByText("Default")).toBeInTheDocument();
      });

      // Open dialog
      const duplicateButton = screen.getByRole("button", { name: /duplicate/i });
      fireEvent.click(duplicateButton);

      // Click create without entering name
      const createButton = screen.getByRole("button", { name: /create/i });
      fireEvent.click(createButton);

      await waitFor(() => {
        expect(screen.getByText(/preset name is required/i)).toBeInTheDocument();
      });
    });
  });

  describe("Delete Preset", () => {
    beforeEach(() => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockPresets,
      });
    });

    it("shows delete button for non-default presets", async () => {
      render(<RagConfigTab />);

      await waitFor(() => {
        expect(screen.getByText("Fast")).toBeInTheDocument();
      });

      // Select non-default preset
      const selector = screen.getByRole("combobox");
      fireEvent.change(selector, { target: { value: "Fast" } });

      await waitFor(() => {
        expect(screen.getByRole("button", { name: /delete preset/i })).toBeInTheDocument();
      });
    });

    it("hides delete button for default preset", async () => {
      render(<RagConfigTab />);

      await waitFor(() => {
        const deleteButton = screen.queryByRole("button", { name: /delete preset/i });
        expect(deleteButton).not.toBeInTheDocument();
      });
    });

    it("shows confirmation dialog when delete clicked", async () => {
      render(<RagConfigTab />);

      await waitFor(() => {
        expect(screen.getByText("Fast")).toBeInTheDocument();
      });

      // Select non-default preset
      const selector = screen.getByRole("combobox");
      fireEvent.change(selector, { target: { value: "Fast" } });

      // Click delete
      const deleteButton = screen.getByRole("button", { name: /delete preset/i });
      fireEvent.click(deleteButton);

      await waitFor(() => {
        expect(screen.getByText(/are you sure/i)).toBeInTheDocument();
      });
    });

    it("deletes preset successfully", async () => {
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({ ok: true })
        .mockResolvedValueOnce({ ok: true, json: async () => [mockPresets[0]] });

      render(<RagConfigTab />);

      await waitFor(() => {
        expect(screen.getByText("Fast")).toBeInTheDocument();
      });

      // Select and delete "Fast" preset
      const selector = screen.getByRole("combobox");
      fireEvent.change(selector, { target: { value: "Fast" } });

      const deleteButton = screen.getByRole("button", { name: /delete preset/i });
      fireEvent.click(deleteButton);

      // Confirm deletion
      const confirmButton = screen.getAllByRole("button", { name: /delete/i })[1];
      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(screen.queryByText("Fast")).not.toBeInTheDocument();
      });
    });
  });

  describe("Set Default", () => {
    beforeEach(() => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockPresets,
      });
    });

    it("sets preset as default successfully", async () => {
      const updatedPresets = [
        { ...mockPresets[0], is_default: false },
        { ...mockPresets[1], is_default: true },
      ];

      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({ ok: true, json: async () => updatedPresets[1] })
        .mockResolvedValueOnce({ ok: true, json: async () => updatedPresets });

      render(<RagConfigTab />);

      await waitFor(() => {
        expect(screen.getByText("Fast")).toBeInTheDocument();
      });

      // Select non-default preset
      const selector = screen.getByRole("combobox");
      fireEvent.change(selector, { target: { value: "Fast" } });

      // Click set default
      const setDefaultButton = screen.getByRole("button", { name: /set as default/i });
      fireEvent.click(setDefaultButton);

      await waitFor(() => {
        expect(screen.getByText(/changes saved successfully/i)).toBeInTheDocument();
      });
    });
  });
});
```

## Test execution

Run tests with:
```bash
cd psychrag_ui
npm test -- rag-config-tab.test.tsx
```

Or with coverage:
```bash
npm test -- --coverage rag-config-tab.test.tsx
```

## Manual test plan

After implementing tests:

1. **Run test suite**: `npm test`
   - Expected: All tests pass
   - Expected: No console errors or warnings

2. **Check coverage**: `npm test -- --coverage`
   - Expected: >80% coverage for rag-config-tab.tsx

3. **Run tests in watch mode during development**: `npm test -- --watch`
   - Expected: Tests re-run on file changes

## Dependencies and sequencing

### Dependencies:
- **Requires**: T05 (RAG Settings UI component must be complete)
- **Testing libraries**: React Testing Library, Jest (should already be installed)

### Sequencing notes:
- Can be done immediately after T05 is complete
- Does not block any other tickets
- Recommended to complete before production deployment

## Clarifications and assumptions

### Assumptions:
1. **Testing framework**: Using Jest + React Testing Library (standard for Next.js/React)
2. **Mock strategy**: Mock `fetch` globally for API calls
3. **Test organization**: One test file for the entire component
4. **Coverage target**: Aim for >80% line coverage
5. **Async handling**: Use `waitFor` for all async operations
6. **User events**: Use `fireEvent` for simulating user interactions

### Implementer notes:

> **Before implementing**:
> - Ensure Jest and React Testing Library are configured in project
> - Review T05 component implementation to understand structure
> - Set up test data fixtures (mock presets)

> **During implementation**:
> - Write tests incrementally, one describe block at a time
> - Run tests frequently to ensure they pass
> - Use descriptive test names that explain what's being tested
> - Mock API responses realistically
> - Test both success and error cases

> **After implementation**:
> - Run full test suite to ensure no regressions
> - Check coverage report to identify gaps
> - Verify tests fail when they should (remove component feature temporarily)
> - Document any test setup requirements in README
