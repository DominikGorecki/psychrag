# T03: Rename Frontend: psychrag_ui → vulcanlab_ui

## Context

- **PRD**: [prd-rename-vulcanlab.md](prd-rename-vulcanlab.md)
- **PRD Sections**: Phase 4 (Frontend), Requirements 4 (Frontend/UI Application)
- **User Value**: Rebrands the Next.js frontend application to use VulcanLab naming, including package name, API endpoint URLs, and internal references. Ensures the UI layer is consistent with the renamed backend.

## Outcome

The `psychrag_ui/` directory is renamed to `vulcanlab_ui/`, the package.json reflects the new name, all API calls use `/vulcanlab/` endpoint paths, and the Next.js application builds and runs successfully.

## Scope

### In scope:
- Rename physical directory `psychrag_ui/` → `vulcanlab_ui/`
- Update `package.json` name field
- Update API base URLs to call `/vulcanlab/` instead of `/psychrag/`
- Update any internal TypeScript/JavaScript references to the package name
- Update any import paths that reference the old package name
- Ensure the application builds successfully: `npm run build`
- Ensure the application runs: `npm run dev`

### Out of scope:
- Core package rename - completed in T01
- API package rename - completed in T02
- User-facing text in the UI (page titles, headers, labels) - handled in T04
- Documentation updates - handled in T04
- Configuration file names - not being renamed per user guidance

## Implementation plan

### Frontend - UI Package Rename

#### Step 1: Verify prerequisites
Before starting, ensure:
1. T01 (core package) is complete
2. T02 (API package) is complete OR you know the new API endpoint structure
3. Backend API is available for testing

#### Step 2: Create feature branch
```bash
git checkout -b feature/rename-ui-package
```

#### Step 3: Rename the UI package directory
1. Rename `psychrag_ui/` → `vulcanlab_ui/`
   - This includes all subdirectories:
     - `src/`
     - `public/`
     - `node_modules/` (will be regenerated)
   - And all config files:
     - `package.json`
     - `tsconfig.json`
     - `next.config.js` (if exists)
     - etc.

#### Step 4: Update package.json
Update the name field in `vulcanlab_ui/package.json`:

```json
{
  "name": "vulcanlab_ui",  // Changed from "psychrag_ui"
  "version": "0.1.0",
  "private": true,
  ...
}
```

**Note**: Keep version as-is unless there's a versioning policy to update.

#### Step 5: Find and update API endpoint URLs
Search for API base URLs or endpoint references:

**Common patterns to search for:**
- `psychrag` in fetch calls
- `/psychrag/` in URL strings
- API_BASE or similar constants

**Files to check:**
- `vulcanlab_ui/src/app/**/*.tsx`
- `vulcanlab_ui/src/components/**/*.tsx`
- `vulcanlab_ui/src/lib/**/*.ts` (if exists)
- `vulcanlab_ui/src/utils/**/*.ts` (if exists)
- Any API client files or service files

**Example changes:**
```typescript
// Before
const API_BASE = 'http://localhost:8000/psychrag/api'
fetch('/psychrag/api/documents')

// After
const API_BASE = 'http://localhost:8000/vulcanlab/api'
fetch('/vulcanlab/api/documents')
```

**Search commands to find references:**
```bash
cd vulcanlab_ui
grep -r "psychrag" src/ --include="*.ts" --include="*.tsx" --include="*.js"
grep -r "/psychrag" src/ --include="*.ts" --include="*.tsx" --include="*.js"
```

#### Step 6: Update any internal package references
Check for references to the old package name in:
- Import statements (if any absolute imports reference the package name)
- Comments or TODOs
- Environment variable names (in `.env` files or `.env.example`)

**Example:**
```typescript
// Check .env.example or .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000/psychrag  // Update to /vulcanlab
```

#### Step 7: Update tsconfig.json paths (if applicable)
If `tsconfig.json` has path mappings that reference the old name:
```json
{
  "compilerOptions": {
    "paths": {
      "@psychrag_ui/*": ["./src/*"]  // Update if present
    }
  }
}
```

Change to:
```json
{
  "compilerOptions": {
    "paths": {
      "@vulcanlab_ui/*": ["./src/*"]
    }
  }
}
```

**Note**: Check if this pattern is actually used before making changes.

#### Step 8: Reinstall dependencies
After renaming and updating package.json:
```bash
cd vulcanlab_ui
rm -rf node_modules package-lock.json
npm install
```

#### Step 9: Verification checks
```bash
cd vulcanlab_ui

# Check for remaining psychrag references in source code
grep -r "psychrag" src/ --include="*.ts" --include="*.tsx" --include="*.js"

# Check package.json
cat package.json | grep "psychrag"  # Should return nothing

# Try building
npm run build

# Try running dev server
npm run dev
```

### Unit tests

Since this is primarily a rename and configuration change, tests focus on build success and import verification:

#### Test 1: Package name verification
**Manual verification** (Next.js doesn't typically have unit tests for package.json):
- Open `vulcanlab_ui/package.json`
- Verify `"name": "vulcanlab_ui"`

#### Test 2: Build succeeds
```bash
cd vulcanlab_ui
npm run build
```

**Expected outcome**: Build completes without errors

#### Test 3: Dev server starts
```bash
cd vulcanlab_ui
npm run dev
```

**Expected outcome**:
- Server starts on http://localhost:3000
- No console errors about missing modules
- No errors about API endpoints (if backend is running)

#### Test 4: TypeScript compilation
```bash
cd vulcanlab_ui
npx tsc --noEmit
```

**Expected outcome**: No TypeScript compilation errors

#### Test 5: Lint passes (if configured)
```bash
cd vulcanlab_ui
npm run lint
```

**Expected outcome**: No linting errors related to the rename

### Integration verification
If the backend is running, manually verify:

#### Test 6: API calls work with new endpoints
1. Start backend: `python -m vulcanlab_api`
2. Start frontend: `npm run dev` (in vulcanlab_ui/)
3. Open browser to http://localhost:3000
4. Check browser console for API call errors
5. Verify API requests go to `/vulcanlab/` endpoints (use browser DevTools Network tab)

## Dependencies and sequencing

### Dependencies:
- **Prerequisite**: T01 (core package rename) completed
- **Prerequisite**: T02 (API package rename) completed - Frontend needs to know new API paths
- **Blocks**: None
- **Can be done in parallel with**: T04 (Documentation) after T02 is complete

### Sequencing notes:
- T01 and T02 should be complete before starting T03
- After this ticket, the frontend will call `/vulcanlab/` API endpoints
- If T02 changed API routes from `/psychrag/` to `/vulcanlab/`, this ticket MUST update the frontend URLs accordingly
- Consider doing this work in a feature branch and merging after build succeeds

### Breaking Changes:
**If API endpoints changed in T02:**
- Frontend API calls must be updated to match
- This ticket ensures frontend and backend stay in sync

## Clarifications and assumptions

### Assumptions:
1. **API routes changed to /vulcanlab/**: Per T02, we assume API routes now use `/vulcanlab/` instead of `/psychrag/`
2. **Node.js/npm are available**: Development environment has Node.js and npm installed
3. **No custom build scripts**: The project uses standard Next.js build commands
4. **UI text updates are separate**: User-facing text (titles, labels) will be updated in T04, not here
5. **package.json name doesn't affect routing**: Next.js doesn't use package.json name for routing, so this is just metadata

### Questions (NOT blocking):
- Are there any CI/CD scripts that reference `psychrag_ui/` directory path?
- Are there any deployment configs (Vercel, Docker) that need the new directory name?
- Is there a `.env` file template that should be updated?

### Pre-implementation checklist:
> **Before implementing, review the following:**
> 1. Confirm T02 (API rename) is complete and you know the new API endpoint structure
> 2. Confirm Node.js and npm are available
> 3. Have a backup or be prepared to use git to rollback if needed
> 4. Understand where API base URLs are defined (centralized config or scattered)

## Manual test plan

After implementation, manually verify:

### Test 1: Directory renamed
```bash
# Should exist
ls vulcanlab_ui/

# Should NOT exist
ls psychrag_ui/  # Should fail
```

### Test 2: Package name updated
```bash
cat vulcanlab_ui/package.json | grep "name"
# Should show: "name": "vulcanlab_ui"
```

### Test 3: Install dependencies
```bash
cd vulcanlab_ui
npm install
```
**Expected**: No errors

### Test 4: Build the app
```bash
cd vulcanlab_ui
npm run build
```
**Expected**:
- Build succeeds
- Output directory `.next/` is created
- No errors about missing modules or imports

### Test 5: Run dev server
```bash
cd vulcanlab_ui
npm run dev
```
**Expected**:
- Server starts on http://localhost:3000
- No import errors in console
- App loads in browser

### Test 6: Check API endpoint calls (with backend running)
1. Start backend API: `python -m vulcanlab_api` (in separate terminal)
2. Start frontend: `npm run dev` (in vulcanlab_ui/)
3. Open browser to http://localhost:3000
4. Open browser DevTools → Network tab
5. Interact with the app to trigger API calls
6. Verify API requests go to `http://localhost:8000/vulcanlab/...` (or appropriate base URL)

**Expected**:
- No 404 errors for API endpoints
- API calls use `/vulcanlab/` paths
- Data loads correctly

### Test 7: Check for missed references
```bash
cd vulcanlab_ui
# Should return no results in src/
grep -r "psychrag" src/ --include="*.ts" --include="*.tsx" --include="*.js"
grep -r "/psychrag" src/ --include="*.ts" --include="*.tsx"
```

### Test 8: TypeScript check
```bash
cd vulcanlab_ui
npx tsc --noEmit
```
**Expected**: No TypeScript errors

## Success criteria

- [ ] Directory `psychrag_ui/` renamed to `vulcanlab_ui/`
- [ ] `package.json` name updated to `"vulcanlab_ui"`
- [ ] All API endpoint URLs updated to use `/vulcanlab/` paths
- [ ] Dependencies reinstalled successfully: `npm install`
- [ ] Build succeeds: `npm run build`
- [ ] Dev server starts: `npm run dev`
- [ ] App loads in browser at http://localhost:3000
- [ ] No grep results for `psychrag` in `vulcanlab_ui/src/`
- [ ] API calls work (when backend is running)
- [ ] TypeScript compilation succeeds: `npx tsc --noEmit`
- [ ] Browser console shows no import or API errors
- [ ] Network tab shows API calls to `/vulcanlab/` endpoints
