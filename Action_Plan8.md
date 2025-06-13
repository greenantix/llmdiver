Action Plan 8: Diagnosing and Repairing the Semantic Indexing Engine
This action plan addresses the critical failure of the semantic search feature. Its primary goal is to use the newly created integration test (test_indexing.py) as a diagnostic tool to pinpoint the failure and provide a clear path to making this feature fully operational and reliable.

Step 1: Execute the Semantic Indexing Integration Test
The Problem: The daemon's logs show that semantic search is not finding any similar code during live runs. We do not know if the root cause is in the model, the code processing, or the search algorithm itself.

The Fix: Run the dedicated test script test_indexing.py. This script was designed specifically to create a controlled environment to validate the CodeIndexer class. Its pass/fail result will be the single most important piece of diagnostic information.

Instructions:

Execute the Test Script:
From the greenantix-llmdiver/ root directory, run the following command:

Bash

python3 test_indexing.py
Analyze the Output:

If the test PASSED: This indicates the CodeIndexer works correctly on clean, simple data but is failing on the complex, real-world output from repomix during a live run. Proceed to Step 2.
If the test FAILED: This indicates a fundamental problem within the CodeIndexer class, the preprocessor, or the embedding model's configuration. Proceed to Step 3.
Step 2 (If Test Passes): Debug Live Data Processing Issues
The Problem: The indexer works in a controlled test but fails in production. This points to a discrepancy between the test data and the live data from repomix. The issue is likely in how the live data is being preprocessed or what is being passed to the indexer.

The Fix: Add detailed logging to the enhanced_repository_analysis function in llmdiver-daemon.py to capture the exact data being fed into the indexer during a live run.

File to Modify: llmdiver-daemon.py

Instructions:

Log the Preprocessed Data:
In the enhanced_repository_analysis method, immediately after preprocessed_data is generated, add logging to inspect its contents.

Python

# In enhanced_repository_analysis, after Step 2
logging.info("Code preprocessing and indexing complete.")
# --- START DEBUG LOGGING ---
if not preprocessed_data.get('files'):
    logging.warning("Preprocessor returned no files from the repomix output.")
else:
    logging.info(f"Preprocessor extracted {len(preprocessed_data['files'])} file sections. First file path: {preprocessed_data['files'][0].get('path')}")
# --- END DEBUG LOGGING ---
Log the Input to the Semantic Search:
In the get_semantic_context method, log the blocks of code that are being used to query for similarities.

Python

# In get_semantic_context method, at the beginning
def get_semantic_context(self, preprocessed_data):
    """Get semantic context by finding similar code patterns"""
    try:
        files = preprocessed_data.get('files', [])
        # --- START DEBUG LOGGING ---
        logging.info(f"Semantic context search initiated with {len(files)} preprocessed files.")
        # --- END DEBUG LOGGING ---
        if not files:
            return ""
Re-run a live analysis and inspect the logs (tail -f llmdiver_daemon.log) to see if the preprocessor is failing to extract files from the live repomix output.

Step 3 (If Test Fails): Debug the Core Indexing Pipeline
The Problem: A failed test indicates a fundamental flaw. The CodeIndexer is unable to find a known, semantically identical function in a perfect, controlled environment.

The Fix: Deconstruct the find_similar_code and _initialize_embedding_backend methods to find the point of failure.

File to Modify: llmdiver-daemon.py

Instructions:

Verify Embedding Model Initialization:
In the _initialize_embedding_backend method, add an explicit log message for the fallback case.

Python

# In _initialize_embedding_backend, at the end of the method
# Default to TF-IDF
self.embedding_model = "tfidf"
self.embedding_backend = TfidfVectorizer(max_features=1000, stop_words='english', ngram_range=(1, 2))
logging.info("SUCCESS: Initialized fallback TF-IDF vectorizer for semantic search.") # Changed from just "Initialized"
This will confirm if the script is failing to load the configured llama_cpp model  and falling back to the less accurate TF-IDF method.

Debug the Similarity Calculation:
In the find_similar_code method, temporarily modify the code to log the actual similarity scores being calculated.

Python

# In find_similar_code method, inside the loop
similarities = cosine_similarity([query_embedding], stored_embeddings)[0]
# --- START DEBUG LOGGING ---
logging.info(f"Similarity scores for query '{query_blocks[i][:30]}...': {similarities}")
# --- END DEBUG LOGGING ---
for j, similarity in enumerate(similarities):
    if similarity > similarity_threshold and i != j:
        #...
This will show the raw similarity scores, revealing if the threshold is too high or if the vectors are simply not similar as expected.

Correct the get_semantic_context Query Logic:
The current implementation only queries using the first block of code it finds. This is inefficient and incorrect for analyzing a set of changes. Modify it to be more useful.

Python

# In CodeIndexer class, replace the get_semantic_context method
def get_semantic_context(self, preprocessed_data: Dict) -> str:
    """Finds code blocks in the index similar to the ones in the current set."""
    try:
        files = preprocessed_data.get('files', [])
        if not files:
            return ""

        # Use all functions from the current analysis as query blocks
        query_blocks = [
            func['content']
            for file_data in files
            for func in file_data.get('code_blocks', {}).get('functions', [])
        ]

        if len(query_blocks) == 0:
            logging.info("No queryable function blocks found in preprocessed data.")
            return ""

        logging.info(f"Querying index with {len(query_blocks)} function blocks.")
        similar_results = self.find_similar_code(query_blocks, similarity_threshold=0.8) # Use a higher threshold for more confidence

        if not similar_results:
            return ""

        # Format results
        context_lines = ["\n## Semantic Context (Similar Code Found Elsewhere)", ""]
        context_lines.append("The following code blocks from the repository are semantically similar to the code being analyzed. Check for potential duplication or opportunities for reuse.\n")

        for i, result in enumerate(similar_results[:self.config.get("max_similar_blocks", 5)]):
            context_lines.append(f"#### Similar Block {i+1} (Similarity: {result['similarity']:.2f})")
            context_lines.append(f"**Found in file:** `{result.get('file_path', 'Unknown')}`")
            context_lines.append("```python")
            context_lines.append(result['similar_block'])
            context_lines.append("```\n")

        return "\n".join(context_lines)

    except Exception as e:
        logging.error(f"FATAL ERROR in get_semantic_context: {e}", exc_info=True)
        return ""
By following this diagnostic plan, you will move from uncertainty to clarity. Executing the test provides a definitive starting point, and the subsequent debugging steps will systematically uncover the reason for the semantic search feature's failure, allowing for its successful repair and deployment.
# Test comment
