# Installing LLMdiver in Your Project

LLMdiver is a powerful code audit tool that uses LM Studio for AI-powered code analysis. This guide will help you set it up in any project.

## Prerequisites

1. **LM Studio**
   - Download and install LM Studio from their official website
   - Make sure the API server is running (default: http://127.0.0.1:1234)

2. **Required Tools**
   - `jq` command line tool
     - Ubuntu/Debian: `sudo apt-get install jq`
     - MacOS: `brew install jq`

## Installation

1. Clone LLMdiver repository in a convenient location:
   ```bash
   git clone https://github.com/yourusername/LLMdiver.git ~/tools/LLMdiver
   ```

2. Navigate to your project directory:
   ```bash
   cd /path/to/your/project
   ```

3. Run the easy installer:
   ```bash
   ~/tools/LLMdiver/easy_install.sh
   ```

## Usage

After installation, you'll have access to these commands in your project:

- `llm-audit` - Run a full deep scan of your codebase
- `llm-audit-quick` - Run a smart fast audit
- `claude-sync` - Run full auto Claude loop

### Configuration

The installer creates a basic config file at `config/llmdiver.json` with default settings:

```json
{
    "llm_model": "meta-llama-3.1-8b-instruct",
    "llm_temp": 0.3,
    "llm_url": "http://127.0.0.1:1234/v1/chat/completions"
}
```

### Output Location

Audit results will be saved in the `audits/` directory in your project.

## Example Usage

```bash
# Run a quick audit
llm-audit-quick

# Run a full deep scan
llm-audit

# Run with specific options
llm-audit --deep  # For deep architectural analysis
llm-audit --fast  # For quick overview
llm-audit --dry   # To see what would be analyzed
```

## Troubleshooting

1. If commands aren't found, make sure your project's `node_modules/.bin` is in your PATH
2. Check if LM Studio is running and accessible at the configured URL
3. Verify `jq` is installed by running `jq --version`

For more detailed information, refer to the full documentation in the LLMdiver repository.