# T03: Fix PDF Conversion Tests (6 tests)

## Context

- **PRD**: [PRD.test-suite-fixes.md](PRD.test-suite-fixes.md)
- **PRD Section**: Phase 3: PDF Conversion Tests (Section 5.1, FR3.1-FR3.6)
- This ticket fixes 6 failing tests in `test_conv_pdf2md.py` that are failing because the production module evolved to support compare mode (returning tuples) and added new parameters (`hierarchical`, `compare`, `use_gpu`). Tests expect single string returns and old parameter signatures. The production `convert_pdf_to_markdown()` function documented in lines 103-111 shows the actual behavior.

## Outcome

When this ticket is complete:
- All 6 tests in `test_conv_pdf2md.py` pass
- Tests correctly handle tuple returns when `compare=True` (default)
- Tests correctly expect new parameters in function calls
- Test assertions match actual production behavior (compare mode generates both `.style.md` and `.hier.md` files)
- Total passing tests increases from 174 to 180 (6 new passes, assuming T02 is complete)

## Scope

### In scope:
- Update `test_successful_conversion` to expect `(str, str)` tuple return
- Update `test_output_file_created` to verify both `.style.md` and `.hier.md` files
- Update `test_path_object_input` to handle tuple return
- Update `main()` tests to handle compare mode tuple unpacking
- Add `hierarchical=True, compare=True, use_gpu=True` to expected mock call arguments
- Update assertions to match compare mode behavior (2 files instead of 1)

### Out of scope:
- Modifying production `convert_pdf_to_markdown()` function (no changes to `src/psychrag/conversions/conv_pdf2md.py`)
- Adding new test cases for single-output mode (`compare=False`)
- Testing GPU vs CPU behavior
- Testing timeout scenarios or error handling
- Fixing other test failures (handled in T02, T04, T05)

## Implementation Plan

### Backend - Understanding the Production Behavior

1. **Review production function signature** (already documented in PRD):
   ```python
   def convert_pdf_to_markdown(
       pdf_path: str | Path,
       output_path: Optional[str | Path] = None,
       verbose: bool = False,
       ocr: bool = False,
       hierarchical: bool = True,  # NEW
       compare: bool = True,       # NEW
       use_gpu: bool = True        # NEW
   ) -> str | tuple[str, str]:     # Return type changed
   ```

2. **Understand compare mode behavior**:
   - When `compare=True` (default): Returns `(style_md, hier_md)` tuple
   - Writes two files: `<stem>.style.md` and `<stem>.hier.md`
   - Also extracts TOC to `<stem>.toc_titles.md`
   - When `compare=False`: Returns single string, writes `<stem>.md`

3. **Review `main()` function behavior** (lines 383-502):
   - Default mode: `compare=True`, `hierarchical=True`
   - With `--style-ver`: `compare=False`, `hierarchical=False`
   - With `--hier-ver`: `compare=False`, `hierarchical=True`
   - With `--no-gpu`: `use_gpu=False`

### Backend - Fix TestConvertPdfToMarkdown Class

4. **Fix test_successful_conversion** (lines 181-207 in test output):
   ```python
   @patch("psychrag.conversions.conv_pdf2md.DocumentConverter")
   def test_successful_conversion(self, mock_converter_class, tmp_path):
       """Test successful PDF to Markdown conversion."""
       # Create mock PDF file
       pdf_file = tmp_path / "test.pdf"
       pdf_file.write_text("fake pdf content")

       # Setup mock
       mock_result = MagicMock()
       mock_result.document.export_to_markdown.return_value = "# Test Markdown"
       mock_converter = MagicMock()
       mock_converter.convert.return_value = mock_result
       mock_converter_class.return_value = mock_converter

       # Run conversion
       result = convert_pdf_to_markdown(pdf_file)

       # Verify - NOW EXPECTS TUPLE
       assert isinstance(result, tuple)
       assert len(result) == 2
       style_md, hier_md = result
       assert style_md == "# Test Markdown"
       assert hier_md == "# Test Markdown"  # Both should be same in this mock
   ```

5. **Fix test_output_file_created** (lines 208-237 in test output):
   ```python
   @patch("psychrag.conversions.conv_pdf2md.DocumentConverter")
   def test_output_file_created(self, mock_converter_class, tmp_path):
       """Test that output files are created when output_path is specified."""
       # Create mock PDF file
       pdf_file = tmp_path / "test.pdf"
       pdf_file.write_text("fake pdf content")
       output_file = tmp_path / "output" / "test.md"

       # Setup mock
       mock_result = MagicMock()
       mock_result.document.export_to_markdown.return_value = "# Test Output"
       mock_converter = MagicMock()
       mock_converter.convert.return_value = mock_result
       mock_converter_class.return_value = mock_converter

       # Run conversion
       convert_pdf_to_markdown(pdf_file, output_path=output_file)

       # Verify output files were created (compare mode creates 2 files)
       style_path = output_file.parent / "test.style.md"
       hier_path = output_file.parent / "test.hier.md"

       assert style_path.exists(), "Style output file should exist"
       assert hier_path.exists(), "Hierarchical output file should exist"
       assert style_path.read_text() == "# Test Output"
       assert hier_path.read_text() == "# Test Output"

       # Also verify PDF was copied
       pdf_copy = output_file.parent / "test.pdf"
       assert pdf_copy.exists(), "PDF should be copied to output directory"
   ```

6. **Fix test_path_object_input** (lines 238-259 in test output):
   ```python
   @patch("psychrag.conversions.conv_pdf2md.DocumentConverter")
   def test_path_object_input(self, mock_converter_class, tmp_path):
       """Test that Path objects are accepted as input."""
       pdf_file = tmp_path / "test.pdf"
       pdf_file.write_text("fake content")

       # Setup mock
       mock_result = MagicMock()
       mock_result.document.export_to_markdown.return_value = "# Test"
       mock_converter_class.return_value.convert.return_value = mock_result

       result = convert_pdf_to_markdown(Path(pdf_file))

       # Now returns tuple in compare mode
       assert isinstance(result, tuple)
       assert len(result) == 2
       style_md, hier_md = result
       assert isinstance(style_md, str)
       assert isinstance(hier_md, str)
   ```

### Backend - Fix TestMain Class

7. **Fix test_main_stdout_output** (lines 260-278 in test output):
   ```python
   @patch("psychrag.conversions.conv_pdf2md.convert_pdf_to_markdown")
   def test_main_stdout_output(self, mock_convert, capsys, monkeypatch):
       """Test main function prints to stdout when no output file."""
       # Mock returns tuple in compare mode
       mock_convert.return_value = ("# Style Content", "# Hier Content")
       monkeypatch.setattr("sys.argv", ["conv_pdf2md", "test.pdf"])

       result = main()

       assert result == 0

       # Verify both outputs are printed
       captured = capsys.readouterr()
       assert "# Style Content" in captured.out
       assert "# Hier Content" in captured.out
       assert "STYLE-BASED OUTPUT" in captured.out
       assert "HIERARCHICAL OUTPUT" in captured.out
   ```

8. **Fix test_main_with_output_file** (lines 279-341 in test output):
   ```python
   @patch("psychrag.conversions.conv_pdf2md.convert_pdf_to_markdown")
   def test_main_with_output_file(self, mock_convert, monkeypatch, tmp_path):
       """Test main function with output file argument."""
       output_file = tmp_path / "output.md"
       mock_convert.return_value = ("# Test", "# Test")
       monkeypatch.setattr(
           "sys.argv",
           ["conv_pdf2md", "test.pdf", "-o", str(output_file)]
       )

       result = main()

       assert result == 0

       # Verify convert was called with ALL expected parameters
       mock_convert.assert_called_once_with(
           pdf_path="test.pdf",
           output_path=str(output_file),
           verbose=False,
           ocr=False,
           hierarchical=True,  # NEW: default is True
           compare=True,       # NEW: default is True
           use_gpu=True        # NEW: default is True
       )
   ```

9. **Fix test_main_verbose_flag** (lines 342-400 in test output):
   ```python
   @patch("psychrag.conversions.conv_pdf2md.convert_pdf_to_markdown")
   def test_main_verbose_flag(self, mock_convert, monkeypatch):
       """Test main function passes verbose flag."""
       mock_convert.return_value = ("# Test", "# Test")
       monkeypatch.setattr("sys.argv", ["conv_pdf2md", "test.pdf", "-v"])

       main()

       # Verify ALL parameters including new defaults
       mock_convert.assert_called_once_with(
           pdf_path="test.pdf",
           output_path=None,
           verbose=True,
           ocr=False,
           hierarchical=True,  # NEW
           compare=True,       # NEW
           use_gpu=True        # NEW
       )
   ```

### Backend - Additional Considerations

10. **Check for other tests in the file**:
    - Review entire `test_conv_pdf2md.py` for other test methods
    - The test output shows TestMain has at least these 3 tests
    - Verify no other test methods need updates

11. **Update test docstrings if needed**:
    - Update docstrings to mention "compare mode" where relevant
    - Example: "Test successful PDF to Markdown conversion in compare mode (default)"

12. **Consider adding clarifying comments**:
    - Add comments explaining tuple unpacking: `# Compare mode returns (style_md, hier_md)`
    - Add comments on file naming: `# Compare mode creates .style.md and .hier.md files`

### Verification Steps

13. **Run test_conv_pdf2md.py in isolation**:
    ```bash
    pytest tests/unit/test_conv_pdf2md.py -v
    ```
    - Expected: All 6+ tests pass (may be more tests in file)
    - Previous: 6 failed

14. **Run specific failing tests**:
    ```bash
    pytest tests/unit/test_conv_pdf2md.py::TestConvertPdfToMarkdown::test_successful_conversion -v
    pytest tests/unit/test_conv_pdf2md.py::TestMain::test_main_with_output_file -v
    ```
    - Expected: Both PASSED

15. **Check for unexpected failures**:
    ```bash
    pytest tests/unit/test_conv_pdf2md.py --tb=short
    ```
    - Verify error messages are gone: "assert ('# Test Markdown', '# Test Markdown') == '# Test Markdown'"
    - Verify error messages are gone: "expected call not found... hierarchical=True, compare=True, use_gpu=True"

## Unit Tests

This ticket fixes 6 existing unit tests rather than creating new ones:

### Tests to Fix (All in test_conv_pdf2md.py)

1. **TestConvertPdfToMarkdown class (3 tests)**:

   - **test_successful_conversion**:
     - **Current failure**: `AssertionError: assert ('# Test Markdown', '# Test Markdown') == '# Test Markdown'`
     - **Root cause**: Function returns tuple but test expects string
     - **Fix**: Expect tuple, unpack both values

   - **test_output_file_created**:
     - **Current failure**: `AssertionError: assert False` (file doesn't exist)
     - **Root cause**: Test checks for `test.md` but compare mode creates `test.style.md` and `test.hier.md`
     - **Fix**: Check for both `.style.md` and `.hier.md` files

   - **test_path_object_input**:
     - **Current failure**: `AssertionError: assert False` (isinstance check fails)
     - **Root cause**: Function returns tuple but test expects string
     - **Fix**: Expect tuple, check both values are strings

2. **TestMain class (3 tests)**:

   - **test_main_stdout_output**:
     - **Current failure**: `assert 1 == 0` (exit code), error message: "too many values to unpack (expected 2)"
     - **Root cause**: Mock returns string but main() tries to unpack tuple
     - **Fix**: Mock should return tuple; verify both outputs are printed

   - **test_main_with_output_file**:
     - **Current failure**: Expected call not found (missing `hierarchical`, `compare`, `use_gpu` parameters)
     - **Root cause**: Test expects old function signature
     - **Fix**: Add new parameters to expected call

   - **test_main_verbose_flag**:
     - **Current failure**: Expected call not found (missing new parameters)
     - **Root cause**: Test expects old function signature
     - **Fix**: Add new parameters to expected call

### Testing Strategy

For each test:
- **Update expectations**: Change from single string to tuple where appropriate
- **Update assertions**: Check for `.style.md` and `.hier.md` files instead of `.md`
- **Update mock calls**: Include `hierarchical`, `compare`, `use_gpu` parameters
- **Maintain test intent**: Still testing the same behaviors, just with correct expectations

### No New Tests Required

Per PRD scope (NG4: "Performance optimization of tests or production code"), we are only fixing existing tests, not adding new coverage for:
- Single-output mode (`compare=False`)
- GPU vs CPU mode
- Timeout scenarios
- Error handling edge cases

These could be future enhancements but are out of scope for this ticket.

## Dependencies and Sequencing

### Must Complete Before:
- **T01**: Test Infrastructure & Database Fixtures
  - Reason: General pytest setup must be in place

### Must Complete Before Starting:
- None (can run in parallel with T02, T04, T05 after T01)

### Blocks If Not Done:
- None (other tickets are independent)

### Sequencing Notes:
- Can be implemented immediately after T01 merges
- Independent from T02 (async tests), T04 (prompt templates), T05 (inspection)
- Low risk of merge conflicts
- Small, focused changes to one test file
- Recommended: Can merge in any order after T01

## Clarifications and Assumptions

### Assumptions Made:

1. **Default Behavior is Compare Mode**: Production function defaults to `compare=True`
   - Tests should expect tuple returns by default
   - Tests should verify both `.style.md` and `.hier.md` files
   - Verified in source code: `compare: bool = True` (line 109)

2. **Mock Setup is Otherwise Correct**: Assuming existing mock configurations for DocumentConverter are correct
   - Only changing return value expectations, not mock setup
   - If tests still fail after tuple changes, may need to adjust mock call counts (2 conversions in compare mode)

3. **PDF Copy Behavior**: Production code copies PDF to output directory
   - Test should verify `<stem>.pdf` exists in output directory
   - Already tested in `test_output_file_created`, will update accordingly

4. **Main Function Handles Both Modes**: `main()` function checks if `compare=True` and unpacks tuple
   - Source code confirms this (lines 478-486)
   - Test mocks should return tuples to match

5. **No Single-Output Mode Tests**: Not adding tests for `compare=False` mode
   - Out of scope per PRD (not fixing new scenarios, only fixing broken tests)
   - Future enhancement if needed

### Questions for Product Owner (Non-blocking):

- **Q1**: Should we add tests for single-output mode (`--style-ver`, `--hier-ver` flags)?
  - **Current approach**: No new tests, only fix broken ones per PRD
  - **Recommendation**: Add in future ticket if coverage is desired

- **Q2**: Should we test GPU vs CPU behavior?
  - **Current approach**: No, out of scope (just fixing parameter expectations)
  - **Recommendation**: Defer to integration test ticket if needed

### No Blocking Questions

All information needed for implementation is available in:
- Production source code (`src/psychrag/conversions/conv_pdf2md.py`)
- Test failure output (shows exact assertion failures)
- PRD requirements (FR3.1-FR3.6)

### Implementer Notes:

> **Before implementing**:
> 1. Re-read lines 103-111 of `src/psychrag/conversions/conv_pdf2md.py` to confirm return type
> 2. Re-read lines 383-502 to understand `main()` function behavior
> 3. Note that compare mode calls converter TWICE (lines 180, 200) - mocks may need call count adjustments
>
> **Implementation strategy**:
> 1. Start with `test_successful_conversion` (simplest fix - just expect tuple)
> 2. Run it to verify fix works: `pytest tests/unit/test_conv_pdf2md.py::TestConvertPdfToMarkdown::test_successful_conversion -v`
> 3. Apply similar pattern to `test_path_object_input`
> 4. Fix `test_output_file_created` (more complex - checks file system)
> 5. Fix all three `TestMain` tests (update expected call arguments)
> 6. Run full file to verify all pass
>
> **If tests still fail after tuple changes**:
> - Check mock call counts: `mock_converter.convert.assert_called_once()` may fail in compare mode (called twice)
> - May need to change to `assert mock_converter.convert.call_count == 2` for compare mode
> - Check for exception handling in mocks (compare mode has fallback logic)

## Manual Test Plan (Acceptance Criteria)

Run these commands in sequence to verify completion:

```bash
# 1. Run test_conv_pdf2md.py in isolation
pytest tests/unit/test_conv_pdf2md.py -v
# Expected: All tests pass (at least 6, possibly more)
# Previously: 6 failed

# 2. Run specific converted tests
pytest tests/unit/test_conv_pdf2md.py::TestConvertPdfToMarkdown::test_successful_conversion -v
# Expected: PASSED (was: AssertionError about tuple vs string)

pytest tests/unit/test_conv_pdf2md.py::TestConvertPdfToMarkdown::test_output_file_created -v
# Expected: PASSED (was: AssertionError about file not existing)

pytest tests/unit/test_conv_pdf2md.py::TestMain::test_main_with_output_file -v
# Expected: PASSED (was: AssertionError about expected call not found)

# 3. Verify error messages are gone
pytest tests/unit/test_conv_pdf2md.py 2>&1 | grep "too many values to unpack"
# Expected: No output (error should be gone)

pytest tests/unit/test_conv_pdf2md.py 2>&1 | grep "expected call not found"
# Expected: No output (error should be gone)

# 4. Run full test suite and check progress
pytest tests/unit/ --tb=no -q | tail -1
# Expected: "180 passed, 29 failed" (assuming T02 complete: 174 + 6 = 180)
# Or: "164 passed, 35 failed" (if T02 not yet merged: 158 + 6 = 164)

# 5. Verify no regressions in baseline
pytest tests/unit/test_api_endpoints.py -v
# Expected: All baseline tests still pass (15 tests)

# 6. Quick sanity check on test file syntax
python -m py_compile tests/unit/test_conv_pdf2md.py
# Expected: No syntax errors
```

**Success Criteria**:
- All 6 verification steps pass
- At least 6 additional tests pass (164-180 total depending on T02 status)
- No "tuple vs string" or "expected call not found" errors
- No regressions in baseline passing tests
- Ready to proceed with T04 (prompt template test fixes)
