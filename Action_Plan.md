An evaluation of the latest project files reveals that the core issues from Action Plan 10—the infinite analysis loop and the broken code preprocessor—have been successfully resolved. The `FileChangeHandler` now correctly ignores internal files, and the move to an AST-based parser for Python has fixed the code block extraction.

However, the analysis has exposed the next layer of problems:

1.  [cite_start]**Repetitive, Low-Value AI Analysis:** The generated reports, like `enhanced_analysis_20250613_055048.md`, are generic and repetitive[cite: 1]. The AI consistently points out the same high-level issues (e.g., "missing tests," "complex scripts") without providing new, specific insights on individual file changes.
2.  [cite_start]**Unused Semantic Context:** The semantic search feature is now functional and identifies similar code blocks, as seen in `analysis_data_20250613_035703.json`[cite: 1, 2]. However, this valuable context is not being used effectively. The main analysis prompt does not instruct the LLM on *how* to use this information, so it is ignored in the final report.
3.  **Inefficient Change Analysis:** The daemon still analyzes the entire repository on every change. The incremental `repomix --include-diffs` feature, which is the key to a fast and targeted analysis, has not been implemented.

To make LLMdiver truly useful, the system must evolve from simply running a generic audit to performing a highly contextual, targeted analysis on *what has changed*, using its own semantic understanding of the codebase to enrich the process.

---

### Action Plan 11: Achieving True Context-Aware Incremental Analysis

This action plan will transform LLMdiver from a repetitive, full-scan tool into a sharp, efficient assistant that understands the context of changes. The focus is on leveraging the now-functional semantic index and implementing a true incremental workflow.

#### Step 1: Activate and Utilize Incremental Diff Analysis

**The Problem:** The daemon is still performing a full, resource-intensive scan of the entire repository on every file change. This is inefficient and not the intended workflow.

**The Fix:** We will modify the core analysis trigger to use `repomix --include-diffs`. This will ensure that only the code that has actually been modified is sent to the LLM, making the analysis faster and highly relevant to the developer's immediate actions.

**File to Modify:** `llmdiver-daemon.py`

**Instructions:**

1.  **Create a Dedicated Diff Analysis Function:**
    In the `RepomixProcessor` class, create a new method that specifically runs `repomix` with the `--include-diffs` flag.

    ```python
    # In class RepomixProcessor
    def run_repomix_diff_analysis(self, repo_path: str) -> str:
        """Runs repomix using --include-diffs to get only changed content."""
        try:
            output_dir = Path(repo_path) / '.llmdiver'
            output_dir.mkdir(exist_ok=True)
            diff_output_file = output_dir / 'repomix_diff.md'
            # This command is much faster as it only processes the git diff
            cmd = ['repomix', repo_path, '--output', str(diff_output_file), '--include-diffs']
            
            logging.info(f"Running incremental diff analysis with command: {' '.join(cmd)}")
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            if result.returncode != 0:
                logging.error(f"Repomix diff analysis failed: {result.stderr}")
                return "" # Return empty string on failure

            with open(diff_output_file) as f:
                content = f.read()
            # If repomix finds no changes, it may return a header but no file content.
            if "## File:" not in content:
                logging.info("Repomix diff analysis found no substantive code changes.")
                return ""
            return content

        except Exception as e:
            logging.error(f"Failed to run repomix diff analysis: {e}", exc_info=True)
            return ""
    ```

2.  **Update the Main Analysis Function to Prioritize Diffs:**
    Modify `enhanced_repository_analysis` to use the new diff-based method as its primary source of analysis context.

    ```python
    # In enhanced_repository_analysis, modify Step 1
    # Step 1: Run repomix to generate an INCREMENTAL repository summary
    logging.info("Step 1: Running repomix --include-diffs to get changes...")
    summary = self.run_repomix_diff_analysis(repo_config["path"]) # Use the new diff method

    if not summary:
        logging.info("No file changes detected by git diff. Skipping full analysis cycle.")
        return # Exit the analysis cycle cleanly
    
    logging.info(f"Repomix diff summary generated ({len(summary)} characters).")
    ```

#### Step 2: Inject Semantic Context into the LLM Prompt

**The Problem:** The `get_semantic_context` function finds similar code, but this information is never passed to the main LLM. The `semantic_context` variable is populated but not included in the final `enhanced_summary` prompt, representing a major missed opportunity.

**The Fix:** We will modify the final prompt construction in `enhanced_repository_analysis` to dynamically insert the semantic context when it's available, and explicitly instruct the LLM to use it.

**File to Modify:** `llmdiver-daemon.py`

**Instructions:**

1.  **Update the Prompt F-String:**
    In the `enhanced_repository_analysis` method (Step 6), modify the `enhanced_summary` f-string to include the `{semantic_context}` variable.

    ```python
    # In enhanced_repository_analysis, Step 6
    enhanced_summary = f"""# Repository Analysis for: {repo_config['name']}

    ## Project Context
    - Primary Language: {project_info['primary_language']}
    - Framework: {project_info['framework']}

    {manifest_analysis}

    {semantic_context} # <-- THIS IS THE CRITICAL ADDITION

    ## Code To Be Analyzed (Recent Changes)
    {formatted_summary}

    ## Analysis Instructions
    You are a principal software architect. Your task is to review the provided code changes ("Code To Be Analyzed").
    1.  **Primary Focus:** Analyze the new code for bugs, security vulnerabilities, and maintainability issues.
    2.  **Use Semantic Context:** If "Semantic Context" is provided, check if the new code is redundant or could be refactored to use the existing similar code blocks. This is a high-priority task.
    3.  **Be Concise:** Provide specific, actionable feedback with file and line numbers.
    """
    ```

#### Step 3: Centralize and Consolidate Analysis Reports

[cite_start]**The Problem:** The system still creates a new, timestamped JSON file for every analysis run[cite: 2], leading to clutter.

**The Fix:** The system will now update a single, canonical report file for each project. This makes the latest result easily accessible and relies on Git for historical tracking.

**File to Modify:** `llmdiver-daemon.py`

**Instructions:**

1.  **Use a Static Filename:**
    In `enhanced_repository_analysis` (Step 8), change the output filenames to be static.

    ```python
    # In enhanced_repository_analysis, modify Step 8
    logging.info("Step 8: Saving consolidated analysis reports...")
    analysis_dir = Path(repo_config["path"]) / ".llmdiver"
    analysis_dir.mkdir(exist_ok=True)

    # --- FIX: Use static, predictable filenames ---
    analysis_file = analysis_dir / "LATEST_ENHANCED_ANALYSIS.md"
    json_analysis_file = analysis_dir / "LATEST_ANALYSIS_DATA.json"

    # ... (rest of the data saving logic) ...
    
    logging.info(f"Consolidated reports updated: {analysis_file} and {json_analysis_file}")
    ```

By implementing this action plan, LLMdiver will operate as originally envisioned: a lean, context-aware tool that analyzes only relevant changes, uses its own index to provide deeper insights, and maintains a clean, single-source-of-truth report for each monitored project.
