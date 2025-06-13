Implementation Plan: A Two-Stage Analysis Pipeline
This plan introduces a second model for pre-processing and context enrichment before the main analysis.

Phase 1: Implement a Semantic Search Indexer
The most immediate high-value use of a second model is to create semantic embeddings for code to find duplicates and provide better context.

1. Choose an Embedding Model:
Select a small, fast model optimized for creating embeddings. Good open-source candidates available on platforms like Hugging Face include:

all-MiniLM-L6-v2
bge-small-en-v1.5
These models are small enough to run locally on a CPU and are excellent at capturing semantic meaning.

2. Modify the Daemon to Create and Use an Index:
The core logic would be added to llmdiver_daemon.py.

File to Modify: llmdiver_daemon.py
Proposed Changes:
Create a new class, CodeIndexer, that is initialized by the LLMdiverDaemon. This class will manage the embeddings.
Indexing Step: When an analysis is triggered, the CodeIndexer would first parse the repomix output into logical code blocks (e.g., functions or classes). It would then use the chosen embedding model to generate a vector for each block and store it (for a simple implementation, this could be a dictionary mapping file/function names to vectors, saved as a JSON file).
Search Step: Before calling the main LLM, the CodeIndexer would take the currently changed code blocks, generate their embeddings, and then search the index to find the top 3-5 most semantically similar code blocks from elsewhere in the repository.
Modify enhanced_repository_analysis: This function  would be updated to orchestrate this process.
3. Enhance the Main Analysis Prompt with Semantic Context:
The real power comes from feeding this new context to the main analysis model.

File to Modify: llmdiver_daemon.py

Proposed Change:

Modify the enhanced_summary prompt variable inside the enhanced_repository_analysis function. Add a new section to the prompt dynamically when relevant context is found.
Example Prompt Enhancement:

Python

# Inside enhanced_repository_analysis, after finding similar code
semantic_context = ""
if similar_code_blocks:
    semantic_context = "## Semantic Context (Similar Code Found Elsewhere)\n"
    semantic_context += "The following code blocks from the repository are semantically similar to the code being analyzed. Check for potential duplication or opportunities for reuse.\n\n"
    for block in similar_code_blocks:
        semantic_context += f"- **File:** `{block['file']}`\n"
        semantic_context += f"  ```python\n{block['code']}\n  ```\n"

# Add this to the f-string for enhanced_summary
enhanced_summary = f"""# Repository Analysis: {repo_config['name']}

## Project Context
...

{semantic_context} # <-- NEWLY ADDED CONTEXT

## Code Analysis
{summary}
...
"""
Phase 2: Implement an "Intelligent Router" Model
After implementing semantic search, the next evolution is to use a small model to classify code and select specialized prompts.

1. Concept:
When a file change is detected, a small classification model first determines the nature of the code.

2. Modify the Analysis Workflow:

File to Modify: llmdiver_daemon.py
Proposed Changes:
In the process_analysis_queue method, before calling analyze_repository, add a new call to a "router" function.
This router function would use a small LLM with a very simple prompt, such as:
"Classify the primary purpose of the following code. Respond with a single word from this list: Security, UI, DataAccess, BusinessLogic, Testing, Configuration.\n\n[Code Snippet]"

Based on the single-word response, the system would then select a specialized system prompt for the main analysis model from a dictionary of prompt templates. For instance, if the code is classified as Security, it would use a prompt that is heavily weighted towards finding vulnerabilities, whereas a UI classification would use a prompt focused on state management and component structure.
Impact on Summaries
By implementing this two-model system, the summaries will become significantly more effective:

Context-Aware: Summaries for code changes will automatically include context about similar existing code.
Focused: The main LLM will be guided by the router to focus on the most likely types of issues for a given piece of code.
Actionable: Duplicate code suggestions will be based on semantic meaning, not just syntax, leading to much more useful refactoring recommendations.
The next logical step is to begin with Phase 1, as it provides the highest immediate value and builds a foundation for the more advanced routing capabilities in Phase 2.

Prompt Engineering: Refining the instructions given to the Large Language Model (LLM) to elicit more structured, insightful, and actionable responses.
Configuration Tuning: Optimizing the repomix configuration to provide higher-quality, context-rich input to the LLM.
Process Enhancement: Improving how the daemon handles and interprets different types of code changes, particularly for dependencies.
Below is a detailed, file-by-file guide to implementing these enhancements.

Phase 1: Enhanced LLM Prompting and Configuration
1. Improve Prompts in run_llm_audit.sh
The existing prompts are good but can be made more robust to guide the LLM toward producing superior audits. The key is to provide a stronger persona, a clear framework for analysis, and a strict output format.

File to Modify: run_llm_audit.sh

A. For Standard Audits (non-deep mode):

The goal is to get quick, actionable insights.

Replace the existing system_prompt for the standard mode  with the following, more detailed version:
Bash

system_prompt="You are a senior software engineer conducting a focused code audit for immediate improvements.
Prioritize findings by impact and actionability.

**ANALYSIS PRIORITIES:**
- CRITICAL: Security issues, crash risks, data leaks
- HIGH: Performance problems, architectural violations  
- MEDIUM: Technical debt, maintainability issues
- LOW: Style inconsistencies, minor optimizations

**REQUIRED OUTPUT FORMAT:**

## Executive Summary
[2-3 sentences: Key findings and recommended immediate actions]

## Critical Issues (CRITICAL/HIGH Priority)
[Security vulnerabilities, performance bottlenecks, architectural problems - with file:line references]

## Technical Debt & TODOs (MEDIUM Priority)
[TODO/FIXME items, mock implementations, maintainability issues - include locations]

## Dead Code & Optimizations (LOW Priority)
[Unused functions, redundant code, minor improvements - include removal suggestions]

## Quick Win Recommendations
[Top 3-5 actionable items that can be fixed immediately with high impact]

**REQUIREMENTS:**
- Provide 
specific file:line references for all findings
- Include relevant code snippets for context
- Focus on actionable recommendations, not theoretical issues"
B. For Deep Architectural Audits (--deep mode):

This prompt needs to guide the LLM to think like a high-level architect.

Replace the existing system_prompt for the DEEP_MODE  with this enhanced version:
Bash

system_prompt="You are a principal software architect and security expert conducting a comprehensive deep architectural audit. This analysis will guide critical refactoring decisions and security improvements.

**DEEP ANALYSIS FRAMEWORK:**
Evaluate the codebase across these dimensions with severity-based prioritization:

**CRITICAL PRIORITY:**
- Security vulnerabilities and data exposure risks
- System stability threats and potential crashes
- Performance bottlenecks affecting user experience

**HIGH PRIORITY:**
- Architectural violations and design pattern misuse
- Missing error handling and edge cases
- Scalability limitations and technical debt

**MEDIUM PRIORITY:**
- Code maintainability and readability issues
- Test coverage gaps and quality concerns
- Documentation and API design problems

**REQUIRED OUTPUT FORMAT:**

## Executive Summary
[3-4 sentences: Overall architecture health, 
most critical risks, immediate action priorities]

## Critical Security & Stability Issues (CRITICAL)
[Security vulnerabilities, crash risks, data leaks - include file:line references and code snippets]

## Architectural Problems (HIGH)
[Design violations, coupling issues, pattern misuse - provide specific examples with locations]

## Performance & Scalability Concerns (HIGH)
[Bottlenecks, inefficient algorithms, resource usage - include measurements where possible]

## Technical Debt Analysis (MEDIUM)
[Maintainability issues, code smells, refactoring opportunities - prioritized by impact]

## Implementation Roadmap
[Phased approach: Quick wins (1-2 days), Major improvements (1-2 weeks), Strategic refactoring (1+ months)]

## Claude Code Action Items
[Specific, executable tasks for automated fixes with priority and estimated effort]

**ANALYSIS REQUIREMENTS:**
- Provide file:line references for all 
findings
- Include code snippets for context
- Assess business impact and technical risk
- Consider the project's domain and constraints
- Focus on actionable, measurable improvements"
2. Optimize repomix Configuration
The data gathered by repomix is the foundation of the audit. By refining its configuration, we can reduce noise and increase the signal sent to the LLM.

File to Modify: config/llmdiver.json

Update the repomix section with the following improvements:
JSON

"repomix": {
    "style": "markdown",
    "compress": true,
    "remove_comments": false,
    "remove_empty_lines": true,
    "include_patterns": [
      "*.py", "*.js", "*.ts", "*.jsx", "*.tsx", "*.sh", "*.rs", "*.go", "*.java", "*.c", "*.cpp", "*.h",
      "Dockerfile", "docker-compose.yml", "*.yaml", "*.yml", "*.toml", "*.ini", "*.conf"
    ],
    "ignore_patterns": [
      "*.md", "*.log", "*.tmp", "*.cache", "*.bak", "*.swp", "*.swo",
      "node_modules", "__pycache__", ".git", ".llmdiver", "venv", ".venv", "env", ".env",
      
"dist", "build", "target", "coverage", ".coverage", ".pytest_cache",
      "*.min.js", "*.bundle.js", "*.test.js", "*.spec.js", "*test*.py", "*spec*.py",
      "migrations", "fixtures", "mock*", "test_data", "sample_data", "*.mock.*"
    ],
    "use_gitignore": true,
    "token_encoding": "cl100k_base",
    "max_file_size": 50000,
    "include_file_tree": true
  }
Rationale for Changes:

"remove_comments": false: Well-written comments provide invaluable context to the LLM.
Expanded include_patterns: Includes more source code and crucial configuration files (like Dockerfile and *.yaml) that define the project's structure and deployment.
Refined ignore_patterns: More comprehensively excludes low-signal files like test data, mock files, and minified assets, focusing the LLM on the core application logic. 
"max_file_size": 50000: Prevents single, massive files (e.g., auto-generated code) from overwhelming the context window.
"include_file_tree": true: Gives the LLM a high-level map of the repository structure, aiding in architectural analysis.
Phase 2: Improving the Daemon's Analytical Process
The background daemon is the core of continuous analysis. These changes will make its automated summaries significantly more intelligent.

1. Enhance the Daemon's Primary Analysis Prompt
File to Modify: llmdiver_daemon.py

Replace the system_prompt string within the analyze_repo_summary method  with the following expert-level prompt. This ensures that even automated, background analyses are held to a high standard.
Python

system_prompt = """You are a principal software architect and security expert conducting a comprehensive code review for maintainability, security, and performance.
Your analysis will be used by development teams to prioritize technical improvements.
**ANALYSIS PRIORITY FRAMEWORK:**
- CRITICAL: Security vulnerabilities, data leaks, system crashes
- HIGH: Performance bottlenecks, architectural violations, breaking changes
- MEDIUM: Code maintainability issues, technical debt, missing tests
- LOW: Style inconsistencies, minor optimizations, documentation gaps

**REQUIRED OUTPUT FORMAT:**

## Executive Summary
[3-4 sentence overview of codebase health, most critical findings, and recommended immediate actions]

## Critical Issues (Priority: CRITICAL)
[Security vulnerabilities, potential crashes, data exposure risks - include code snippets and file:line references]

## High Priority Concerns (Priority: HIGH)  
[Performance bottlenecks, architectural problems, breaking changes - include specific examples]

## Technical Debt & TODOs (Priority: MEDIUM)
[TODO/FIXME items, mock implementations, maintainability issues - provide file locations]

## Dead Code & Optimization 
(Priority: LOW)
[Unused functions, redundant code, minor optimizations - include removal suggestions]

## Actionable Recommendations
[Specific, prioritized action items with estimated impact and effort]

**ANALYSIS REQUIREMENTS:**
- Provide file:line references for all findings
- Include relevant code snippets for context
- Prioritize findings by business impact and security risk
- Focus on actionable recommendations, not theoretical issues
- Consider the project's architecture and technology stack"""
2. Improve Manifest Change Analysis
When a dependency file changes, the daemon should prompt the LLM to perform a more targeted and insightful analysis.

File to Modify: llmdiver_daemon.py

Replace the analyze_manifest_changes method  with this enhanced version that generates more direct instructions for the LLM:
Python

def analyze_manifest_changes(self, repo_config: Dict) -> str:
    """Analyze manifest 
changes for incremental analysis"""
    if not self.config.config.get("manifest_analysis", {}).get("enabled", False):
        return ""
    
    changes = self.manifest_analyzer.check_manifest_changes(repo_config["path"])
    if not changes:
        return ""
    
    analysis_text = "## Dependency Change Analysis\n\n"
    
  
  for change in changes:
        if change["type"] == "modified":
            analysis_text += f"### 🔄 Modified: {change['file']}\n"
            if change["added_deps"]:
                analysis_text += f"**➕ Added dependencies ({len(change['added_deps'])}):** {', '.join(change['added_deps'])}\n"
       
     analysis_text += f"   *Security Assessment Required*: Review new packages for vulnerabilities and licensing\n"
            if change["removed_deps"]:
                analysis_text += f"**➖ Removed dependencies ({len(change['removed_deps'])}):** {', '.join(change['removed_deps'])}\n"
                analysis_text += f"   *Impact Assessment Required*: Check for breaking changes and 
unused imports\n"
            analysis_text += "\n"
        elif change["type"] == "new":
            analysis_text += f"### 🆕 New manifest: {change['file']}\n"
            analysis_text += f"**Total dependencies ({len(change['dependencies'])}):** {', '.join(change['dependencies'])}\n"
            analysis_text += f"   *Full 
Security Review Required*: New dependency ecosystem introduced\n\n"
    
    # Add analysis instructions for the LLM
    if changes:
        analysis_text += "### 🎯 LLM Analysis Focus Areas:\n"
        analysis_text += "- **Security**: Check for known vulnerabilities in added packages\n"
        analysis_text += "- **Compatibility**: Assess version conflicts and breaking changes\n"

       analysis_text += "- **Necessity**: Evaluate if dependencies are actually needed\n"
        analysis_text += "- **Alternatives**: Suggest lighter or more secure alternatives where applicable\n"
        analysis_text += "- **Impact**: Assess bundle size, performance, and maintenance implications\n\n"
    
    return analysis_text
By implementing this comprehensive action plan, the LLMdiver tool will be significantly more effective, providing summaries that are not only more accurate but also more strategically valuable to the development workflow.
