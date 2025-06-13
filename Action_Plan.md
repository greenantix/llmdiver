Action Plan: Enhancing LLMdiver's Summarization Effectiveness ✅ PHASE 1 COMPLETE
This action plan is designed to improve the quality of the AI-generated summaries by refining what data is sent to the LLM and how the LLM is instructed to analyze it.

## ✅ COMPLETED IMPROVEMENTS (Phase 1)
- **Enhanced System Prompts**: Added severity-based prioritization framework (CRITICAL/HIGH/MEDIUM/LOW)
- **Executive Summaries**: All analyses now start with 2-4 sentence executive summaries
- **Structured Output**: Consistent markdown formatting with specific sections and requirements
- **Improved Repomix Config**: Better signal-to-noise ratio with preserved comments and expanded file coverage
- **Enhanced Dependency Analysis**: Detailed manifest change tracking with security focus
- **Actionable Recommendations**: Specific file:line references and code snippets required

Phase 1: Foundational Prompt and Configuration Improvements
This phase focuses on immediate, high-impact changes to the prompts and configurations that guide the LLM's analysis.

1. Refine System Prompts for Clarity and Specificity:

The current prompts are functional but can be enhanced to provide stronger guidance to the LLM.

File: run_llm_audit.sh

Current Deep Mode Prompt: The prompt for deep mode is comprehensive but could be more structured. 
Action:
Add explicit instructions to prioritize findings by severity (critical, high, medium, low).
Instruct the LLM to provide code snippets for context when referencing specific issues.
Demand a concluding "Executive Summary" section at the beginning of the output for quick comprehension.
File: llmdiver_daemon.py

Current analyze_repo_summary Prompt: This prompt is a good starting point for general code auditing. 
Action:
Modify the system prompt to require the LLM to adopt the persona of a senior software architect with a specific goal (e.g., "You are a principal software architect reviewing a codebase for maintainability, security, and performance.").
Incorporate a section in the prompt that asks for "Actionable Recommendations," distinct from the identified issues.
File: prompts/audit_plan.txt

Current Prompt: The user-defined audit plan is a good list of requirements. 
Action: Convert this into a more structured system prompt that can be used by the scripts. For example: "Analyze the codebase to identify the following, presenting each in its own dedicated markdown section: 1. Unused functions or dead code...".
2. Optimize repomix Configuration for Higher Signal Output:

The quality of the LLM's summary is highly dependent on the quality of the input it receives. The repomix tool generates this input.

File: config/llmdiver.json
Current repomix Configuration: The configuration is set to include a broad range of files and removes comments and empty lines. 


Action:
Fine-tune the include_patterns and ignore_patterns to be more project-specific if possible. For instance, exclude test data or mock server files that might not be relevant for a high-level summary. 

Experiment with not removing comments ("remove_comments": false), as well-written comments can provide crucial context for the LLM.
3. Enhance the Final Report Generation:

The audit.sh script generates a final summary. This can be improved to be more comprehensive.

File: audit.sh
Current Summary Generation: The script uses grep to pull out key sections for an executive summary. 
Action:
Instead of grep, which can be brittle, modify the deep_audit.py script (called by audit.sh) to generate a structured JSON output with distinct fields for "Key Insights," "Security Concerns," and "Performance Issues."
The audit.sh script can then parse this JSON to build a more reliable and detailed executive summary.
Phase 2: Advanced Data Processing and Incremental Analysis
This phase introduces more advanced techniques for processing the data before it reaches the LLM.

1. Implement Pre-processing of repomix Output:

Instead of sending the raw repomix output to the LLM, a pre-processing step can structure the data more effectively.

File: llmdiver_daemon.py
Action:
Create a new method within the RepomixProcessor class that reads the repomix.md file. 
This method should parse the markdown to identify file sections, and then for each file, categorize the code into logical blocks (e.g., imports, class definitions, function definitions).
The pre-processed data sent to the LLM would then be a more structured representation of the codebase, which can lead to better analysis.
2. Refine Manifest and Dependency Analysis:

The system already tracks manifest files, but this can be leveraged more effectively in the prompts. 


File: llmdiver_daemon.py
Action:
When manifest file changes are detected, the prompt sent to the LLM should include the specific dependencies that were added or removed.
The prompt should then explicitly ask the LLM to consider the implications of these changes, such as potential security vulnerabilities from new packages or breaking changes from removed ones.
Phase 3: Iterative Feedback and Architectural Refinements
This final phase focuses on long-term improvements and making the system "smarter" over time.

1. Create a Feedback Loop for Summary Quality:

Action:
Introduce a new API endpoint, for example POST /api/v1/feedback, where a user can submit a rating (e.g., 1-5) and comments on a generated summary.
Store this feedback in a database.
Periodically review the feedback to identify patterns in poor summaries, which can then inform further prompt tuning.
2. Develop Specialized Prompts for Different Analysis Types:

Action:
Instead of a one-size-fits-all prompt, create different prompt templates based on the analysis trigger.
For example, a change in a package.json file would trigger a "Dependency Analysis" prompt, while a change in a Python file would trigger a "Code Logic and Quality Analysis" prompt. This specialization will yield more relevant summaries.
By systematically implementing these changes, the LLMdiver tool can evolve to produce consistently higher-quality, more actionable summaries, transforming it into an even more powerful automated code auditing assistant.
