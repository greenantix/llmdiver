#!/usr/bin/env python3

import json
import logging
import sys
import os
from pathlib import Path

# Add current directory to path and import daemon components
sys.path.insert(0, '.')

# Import from the daemon file by loading it directly
daemon_file = Path('llmdiver-daemon.py')
if daemon_file.exists():
    import importlib.util
    spec = importlib.util.spec_from_file_location("daemon", daemon_file)
    daemon_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(daemon_module)
    
    Config = daemon_module.Config
    CodePreprocessor = daemon_module.CodePreprocessor
    CodeIndexer = daemon_module.CodeIndexer
else:
    print("❌ FAILED: llmdiver-daemon.py not found")
    sys.exit(1)

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
    
    # Debug: Print what was extracted
    for i, file_data in enumerate(preprocessed_data['files']):
        print(f"File {i}: {file_data['path']}")
        print(f"  Functions: {len(file_data.get('code_blocks', {}).get('functions', []))}")
        print(f"  Classes: {len(file_data.get('code_blocks', {}).get('classes', []))}")
        if file_data.get('code_blocks', {}).get('functions'):
            print(f"  First function content: {file_data['code_blocks']['functions'][0].get('content', 'N/A')[:100]}...")


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