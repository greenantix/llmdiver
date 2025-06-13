# Repomix Integration for LLMdiver

## Setup

1. Install Repomix globally:
```bash
npm install -g repomix
```

2. Start the LLMdiver daemon:
```bash
# Option 1: Run directly
python3 llmdiver-daemon.py

# Option 2: Install as systemd service
sudo cp llmdiver.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable llmdiver
sudo systemctl start llmdiver
```

3. Verify daemon status:
```bash
curl http://localhost:8080/status
```

## Configuration

The integration is configured in `config/llmdiver.json`:

```json
{
  "repomix": {
    "enabled": true,
    "style": "markdown",
    "compress": true,
    "remove_comments": true,
    "remove_empty_lines": true,
    "include_patterns": ["*.py", "*.js", "*.ts", "*.jsx", "*.tsx", "*.sh"],
    "ignore_patterns": ["*.md", "*.log", "*.tmp"],
    "use_gitignore": false,
    "token_encoding": "cl100k_base"
  }
}
```

## Running Code Analysis

```bash
# Standard analysis
./run_llm_audit.sh /path/to/repo

# Fast mode (minimal summary)
./run_llm_audit.sh /path/to/repo --fast

# Deep architectural analysis
./run_llm_audit.sh /path/to/repo --deep

# Show repomix payload without running
./run_llm_audit.sh /path/to/repo --show-payload
```

## Generated Files

The integration creates several files in the audit directory:
- `_repomix_summary.txt`: Raw repomix output
- `full_audit.md`: LM Studio analysis
- Task files in `tasks/`:
  - `todo_issues.md`
  - `dead_code.md`
  - `mocks_and_stubs.md`
  - `duplicate_code.md`
  - `unwired_components.md`
- Claude prompts in `prompts/`
- Documentation in `docs/`:
  - `llmdiver_analysis.md`: Auto-generated analysis documentation

## Git Automation

The system supports automated git operations:
1. Auto-commit changes when threshold is reached
2. Optional auto-push to remote repositories
3. Protected branch configuration
4. Auto-generated documentation commits

Configuration in `llmdiver.json`:
```json
{
  "git_automation": {
    "enabled": true,
    "commit_message_template": "🤖 LLMdiver: {summary}\n\n{details}",
    "auto_push": false,
    "documentation_update": true,
    "branch_protection": ["main", "master"]
  }
}
```

## Remote Repository Support

Clone and analyze remote repositories:
```bash
# Clone a repository
curl -X POST http://localhost:8080/repos/new-repo/clone \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com/user/repo.git"}'

# Trigger analysis
curl -X POST http://localhost:8080/repos/new-repo/analyze
```

## API Endpoints

### Repository Management
- `GET /status` - Check daemon health
- `GET /repos` - List monitored repositories
- `POST /repos/{name}/clone` - Clone remote repository
- `POST /repos/{name}/analyze` - Trigger analysis
- `GET /repos/{name}/issues` - Get current issues
- `GET /repos/{name}/insights` - Get LLM insights

### Analysis Results
Response format for `/repos/{name}/issues`:
```json
{
  "issues": [
    {
      "type": "todo",
      "file": "src/main.py",
      "line": 42,
      "description": "Implement error handling"
    }
  ]
}
```

## Token Optimization

The integration optimizes token usage through:
1. Compressed analysis output
2. Comment and empty line removal
3. Token counting with cl100k_base encoding
4. Customizable file patterns and ignore rules

## Troubleshooting

1. Verify Repomix installation:
```bash
repomix --version
```

2. Check daemon logs:
```bash
# If running directly
tail -f llmdiver-daemon.log

# If using systemd
journalctl -u llmdiver -f
```

3. Test API server:
```bash
curl http://localhost:8080/status
```

4. Verify git automation:
```bash
# Check auto-commit status
curl http://localhost:8080/repos/your-repo/status

# Force documentation update
curl -X POST http://localhost:8080/repos/your-repo/docs/update
```

## Development

### Adding New API Endpoints
1. Extend APIHandler class in `llmdiver-daemon.py`
2. Update REPOMIX_INTEGRATION.md documentation
3. Add tests for new endpoints

### Token Optimization Tips
1. Use `.gitignore.llmdiver` for precise file filtering
2. Configure `include_patterns` and `ignore_patterns`
3. Enable compression and whitespace removal
4. Monitor token usage in logs