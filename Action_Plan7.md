Based on a thorough review of the project files and the previous action plans, it is clear there are significant concerns about the functionality and transparency of the indexing and semantic search features. Action Plan 3 was designed to add logging to the CodeIndexer to provide visibility, but the output still does not confirm if the core indexing is effective. The system has logging to attempt initialization, but no definitive proof of successful indexing or searching is present in the analysis outputs.



This new action plan will provide a definitive method to determine if indexing is working and then lay out the steps to make it a robust, reliable, and central part of the analysis pipeline.

Action Plan 7: Verifying and Hardening the Semantic Indexing Engine
This plan will address the critical question of whether the semantic indexing feature is operational. It will establish a clear "pass/fail" test for the feature and then introduce robust enhancements to ensure its output is actively used and its health is continuously monitored.

Step 1: Create a Dedicated Integration Test for Semantic Search
The Problem: There is no direct way to know if the CodeIndexer is successfully creating meaningful vector embeddings and finding relevant similar code. The logs show initialization attempts but not the results of a search operation.

The Fix: We will create a new, standalone test script (test_indexing.py) that performs a controlled experiment. This script will create a dummy repository with known duplicate functions, run the indexer, and assert that the correct duplicates are found. This provides a clear, repeatable "litmus test" for the feature.

Instructions:

Create a Test Directory and Files:
Create a new directory named indexing_test/ in the project root. Inside it, create three files:

file_a.py:

Python

def calculate_price(base, tax, discount):
    """This is a standard price calculator."""
    return (base * (1 + tax)) - discount
file_b.py:

Python

def get_total_cost(price, tax_rate, coupon):
    """This is a semantically identical price calculator."""
    return (price * (1 + tax_rate)) - coupon
file_c.py:

Python

def generate_random_string(length):
    """This function is completely different."""
    import random
    import string
    return ''.join(random.choice(string.ascii_letters) for i in range(length))
Create the Test Script (test_indexing.py):
Create a new file test_indexing.py in the root directory. This script will use the core daemon classes to run the test.

Python

import json
import logging
from pathlib import Path
from llmdiver_daemon import Config, CodePreprocessor, CodeIndexer

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_indexing_test():
    """Tests the CodeIndexer's ability to find semantically similar code."""
    print("--- Running Semantic Indexing Integration Test ---")

    # 1. Load Configuration
    try:
        config = Config().config.get('semantic_search', {})
        if not config.get('enabled', False):
            print("⚠️  SKIPPED: Semantic search is not enabled in config/llmdiver.json.")
            return
        logging.info("Configuration loaded.")
    except Exception as e:
        print(f"❌ FAILED: Could not load configuration. Error: {e}")
        return

    # 2. Initialize Components
    preprocessor = CodePreprocessor()
    indexer = CodeIndexer(config)
    logging.info(f"Using embedding model: {indexer.embedding_model}")

    # 3. Create a mock repomix output from our test files
    test_repo_path = Path("indexing_test")
    mock_repomix_content = ""
    for py_file in test_repo_path.glob("*.py"):
        with open(py_file, 'r') as f:
            content = f.read()
            mock_repomix_content += f"## File: {py_file}\n```python\n{content}\n```\n\n"

    # 4. Preprocess the mock output
    preprocessed_data = preprocessor.preprocess_repomix_output(mock_repomix_content)
    if not preprocessed_data or not preprocessed_data.get('files'):
         print("❌ FAILED: Code preprocessor did not extract any files.")
         return
    logging.info(f"Preprocessor extracted {len(preprocessed_data['files'])} files.")


    # 5. Index the code blocks
    all_code_blocks = [
        block['content']
        for file_data in preprocessed_data['files']
        for block in file_data.get('code_blocks', {}).get('functions', [])
    ]
    indexer.update_index(all_code_blocks)
    logging.info("Code index updated with test functions.")

    # 6. Create a query block (the function from file_a.py)
    query_block = [f['content'] for f in preprocessed_data['files'][0].get('code_blocks', {}).get('functions', [])]
    if not query_block:
        print("❌ FAILED: Could not extract the query function from test file.")
        return

    # 7. Perform the search
    logging.info("Performing semantic search...")
    similar_results = indexer.find_similar_code(query_block, similarity_threshold=0.7)

    # 8. Validate the results
    print("\n--- Test Results ---")
    if not similar_results:
        print("❌ FAILED: No similar code blocks were found.")
        return

    found_match = False
    for result in similar_results:
        # Check if the similar block found is the one from file_b.py
        if "get_total_cost" in result.get('similar_block', ''):
            found_match = True
            print(f"✅ PASSED: Found correct similar function with similarity score: {result['similarity']:.2f}")
            break

    if not found_match:
        print("❌ FAILED: The correct similar function was NOT found in the results.")
    else:
        print("✅ Semantic Indexing Test Completed Successfully!")

if __name__ == "__main__":
    run_indexing_test()
Step 2: Integrate Indexing Results Directly into the Final Report
The Problem: Even if the indexer is working, its findings are not visible in the final markdown or JSON reports. The semantic_context is generated but not prominently displayed, making the feature invisible to the end-user.

The Fix: We will modify the enhanced_repository_analysis function to ensure that if similar code is found, it is explicitly included in both the markdown report and the structured JSON output.

File to Modify: llmdiver-daemon.py

Instructions:

Enhance the Markdown Report:
In the enhanced_repository_analysis method, find where the enhanced_summary f-string is constructed (Step 6) and ensure the {semantic_context} is placed prominently.

Python

# In enhanced_repository_analysis (Step 6)
enhanced_summary = f"""# Repository Analysis: {repo_config['name']}

## Project Context
{project_info_text}

{manifest_analysis}

{semantic_context} # <-- ENSURE THIS IS PRESENT AND PROMINENT

## Preprocessed Code Analysis
{formatted_summary}
...
"""
Add Semantic Findings to Structured JSON:
In the enhanced_repository_analysis method, find where the analysis_data dictionary is created (Step 8) and ensure the semantic_analysis block is correctly populated.

Python

# In enhanced_repository_analysis (Step 8)
analysis_data = {
    "metadata": { ... },
    "project_context": { ... },
    "code_metrics": preprocessed_data.get('code_metrics', {}),
    "ai_analysis": {
        "raw_text": analysis,
        "structured_findings": self._extract_structured_findings(analysis)
    },
    "semantic_analysis": { # <-- VERIFY AND ENHANCE THIS BLOCK
        "has_similar_code": bool(semantic_context.strip()),
        "similar_blocks_found": len(semantic_context.split('File:')) - 1 if semantic_context.strip() else 0,
        "context_text": semantic_context # The raw context for reference
    },
}
Step 3: Add Indexing Health to the GUI Dashboard
The Problem: The user has no easy way to see the status of the indexing engine from the GUI.

The Fix: We will add a new section to the "Quick Stats" panel in the llmdiver_monitor.py GUI to report on the state of the last semantic analysis.

File to Modify: llmdiver_monitor.py

Instructions:

Update the update_stats method:
Modify the update_stats method to parse the new semantic_analysis block from the analysis_data_*.json file.

Python

# In update_stats method, inside the 'try' block for the latest_json file
if latest_json:
    with open(latest_json, 'r') as f:
        data = json.load(f)

    # ... (existing metadata, metrics, findings extraction) ...

    # --- NEW SEMANTIC STATS ---
    semantic_info = data.get("semantic_analysis", {})
    if semantic_info.get("has_similar_code"):
        blocks_found = semantic_info.get("similar_blocks_found", 0)
        stats.append(("Semantic Search", f"✅ Found {blocks_found} similar blocks", timestamp))
    else:
        stats.append(("Semantic Search", "ℹ️ No similar code found", timestamp))
    # --- END NEW STATS ---

    crit_count = len(findings.get("critical_issues", []))
    high_count = len(findings.get("high_priority", []))
    stats.append(("Critical/High Issues", f"{crit_count} / {high_count}", timestamp))

By executing this action plan, you will first get a definitive answer to "is the indexing even working?" via the integration test. Then, you will make the feature's output a first-class citizen in all reports and provide crucial visibility into its health directly within the GUI dashboard, restoring trust and transparency to this key feature.
