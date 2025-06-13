# Quick Start Guide for LLMdiver

## 🚀 5-Minute Setup

### First Time Setup

1. Make sure you have LM Studio installed and running:
   - Download from [LM Studio Website](https://lmstudio.ai)
   - Start LM Studio
   - Click "Start Server" in LM Studio (this enables the API)

2. Install jq (one-time setup):
   ```bash
   # On Ubuntu/Debian:
   sudo apt-get install jq

   # On MacOS:
   brew install jq
   ```

### Setting Up in a New Project

1. Go to your project folder:
   ```bash
   cd your-project-folder
   ```

2. Copy and run the installer:
   ```bash
   # Copy installer from LLMdiver
   cp /path/to/LLMdiver/easy_install.sh .
   
   # Make it executable and run
   chmod +x easy_install.sh
   ./easy_install.sh
   ```

## 🔍 Using LLMdiver in GMAILspambot

LLMdiver is already installed in GMAILspambot! Here's how to use it:

1. Go to the GMAILspambot directory:
   ```bash
   cd repo    # if you're in LLMdiver
   # or
   cd path/to/GMAILspambot
   ```

2. Run a quick audit:
   ```bash
   ./node_modules/.bin/llm-audit-quick
   ```

3. Run a deep scan:
   ```bash
   ./node_modules/.bin/llm-audit
   ```

4. View results:
   - Audit results are saved in the `audits/` folder
   - Quick summaries are in `audits/[projectname]/_repomix_summary.txt`
   - Full analysis is in `audits/[projectname]/full_audit.md`

## ⚡ Common Commands

```bash
# Quick scan (good for starting out)
./node_modules/.bin/llm-audit-quick

# Full deep scan (more thorough)
./node_modules/.bin/llm-audit

# Preview what would be analyzed without running
./node_modules/.bin/llm-audit --dry

# Deep architectural analysis
./node_modules/.bin/llm-audit --deep
```

## 🔧 Configuration

The config file is at `config/llmdiver.json` in your project. Default settings work well with LM Studio.

## 📁 Where to Find Results

- `audits/` - Main folder for all audit results
- `audits/[projectname]/_repomix_summary.txt` - Quick overview
- `audits/[projectname]/full_audit.md` - Detailed analysis
- `audits/[projectname]/tasks/` - Individual issues to fix

## 🆘 Troubleshooting

1. If LM Studio isn't running:
   - Open LM Studio
   - Click "Start Server" button
   - Wait for "Server Running" message

2. If commands aren't found:
   - Use the full path: `./node_modules/.bin/llm-audit`
   - Or add to PATH: `export PATH="./node_modules/.bin:$PATH"`

3. If you see "jq not found":
   - Install it using the commands in the setup section above

Need more help? Check the full documentation in INSTALL.md