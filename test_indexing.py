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
    files = preprocessed_data['files']
    print("\n--- File Analysis ---")
    for i, file_data in enumerate(files):
        print(f"File {i}: {file_data['path']}")
        print(f"  Language: {file_data['language']}")
        print(f"  Size: {file_data['size']} characters")
        
        code_blocks = file_data.get('code_blocks', [])
        functions = [block for block in code_blocks if block.get('type') == 'function']
        classes = [block for block in code_blocks if block.get('type') == 'class']
        
        print(f"  Code blocks: {len(code_blocks)}")
        print(f"  Functions: {len(functions)}")
        print(f"  Classes: {len(classes)}")
        
        # Show first function if exists
        if functions:
            print(f"  First function: {functions[0].get('name', 'unnamed')}")
            print(f"  Content preview: {functions[0].get('content', '')[:100]}...")
        print()


    # 5. Index the code blocks using the new update method
    indexer.update_index(preprocessed_data)
    logging.info("Code index updated with preprocessed data.")

    # 6. Get all function blocks for semantic search  
    all_functions = []
    for file_data in preprocessed_data['files']:
        code_blocks = file_data.get('code_blocks', [])
        functions = [block for block in code_blocks if block.get('type') == 'function']
        all_functions.extend(functions)
    
    if not all_functions:
        print("❌ FAILED: No functions were extracted from test files.")
        return
    
    print(f"Extracted {len(all_functions)} functions total.")

    # 7. Create a query from the first function
    query_functions = [all_functions[0]['content']] if all_functions else []
    if not query_functions:
        print("❌ FAILED: Could not extract the query function from test file.")
        return

    # 8. Perform the search
    logging.info("Performing semantic search...")
    similar_results = indexer.find_similar_code(query_functions, similarity_threshold=0.6)

    # 9. Validate the results
    print("\n--- Test Results ---")
    if not similar_results:
        print("❌ FAILED: No similar code blocks were found.")
        print("This indicates that semantic indexing is not working properly.")
        return

    print(f"Found {len(similar_results)} similar code patterns:")
    found_match = False
    for i, result in enumerate(similar_results):
        print(f"  Result {i+1}: Similarity {result['similarity']:.3f}")
        print(f"    Location: {result.get('file_path', 'Unknown')}")
        
        # Check if the similar block found is the other price calculation function
        if "calculate_price" in result.get('similar_block', '') or "get_total_cost" in result.get('similar_block', ''):
            found_match = True
            print(f"✅ PASSED: Found correct similar function with similarity score: {result['similarity']:.3f}")

    if not found_match:
        print("❌ FAILED: The correct similar function was NOT found in the results.")
        print("Expected to find either 'calculate_price' or 'get_total_cost' function")
    else:
        print("✅ Semantic Indexing Test Completed Successfully!")

if __name__ == "__main__":
    run_indexing_test()