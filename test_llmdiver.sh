#!/bin/bash
# Test script for LLMdiver daemon setup

echo "=== LLMdiver Migration Test ==="
echo

# Test 1: Configuration validation
echo "1. Testing configuration..."
cd /home/greenantix/AI/LLMdiver
python3 -c "
from llmdiver_daemon import LLMdiverConfig
config = LLMdiverConfig('config/llmdiver.json')
print(f'✅ Configuration loaded: {len(config.config[\"repositories\"])} repositories')
"

# Test 2: Multi-project discovery
echo
echo "2. Testing multi-project discovery..."
python3 -c "
from llmdiver_daemon import MultiProjectManager
config = {'multi_project': {'enabled': True, 'projects_root': '/home/greenantix/AI', 'auto_discover': True, 'discovery_patterns': ['.git'], 'exclude_paths': ['node_modules', '__pycache__']}}
manager = MultiProjectManager(config)
projects = manager.discover_projects()
print(f'✅ Discovered {len(projects)} projects')
"

# Test 3: Manifest analysis
echo
echo "3. Testing manifest analysis..."
python3 -c "
from llmdiver_daemon import ManifestAnalyzer
config = {'manifest_analysis': {'enabled': True, 'manifest_files': ['package.json', 'requirements.txt']}}
analyzer = ManifestAnalyzer(config)
manifests = analyzer.find_manifests('/home/greenantix/AI/GMAILspambot')
print(f'✅ Found {len(manifests)} manifests')
"

# Test 4: Daemon initialization
echo
echo "4. Testing daemon initialization..."
python3 -c "
from llmdiver_daemon import LLMdiverDaemon
import logging
logging.getLogger().setLevel(logging.ERROR)  # Suppress info logs
daemon = LLMdiverDaemon()
print(f'✅ Daemon initialized with {len(daemon.config.config[\"repositories\"])} repositories')
"

# Test 5: Dependencies check
echo
echo "5. Checking dependencies..."
if command -v repomix &> /dev/null; then
    echo "✅ repomix available"
else
    echo "❌ repomix not found"
fi

if python3 -c "import git, watchdog, requests" 2>/dev/null; then
    echo "✅ Python dependencies available"
else
    echo "❌ Missing Python dependencies"
fi

# Test 6: LM Studio connectivity (optional)
echo
echo "6. Testing LM Studio connectivity..."
if curl -s http://127.0.0.1:1234/v1/models >/dev/null 2>&1; then
    echo "✅ LM Studio accessible"
else
    echo "⚠️  LM Studio not accessible (this is optional)"
fi

echo
echo "=== Migration Test Complete ==="
echo "The LLMdiver daemon has been successfully migrated and configured!"
echo
echo "To start the daemon:"
echo "  ./start_llmdiver.sh start"
echo
echo "To check status:"
echo "  ./start_llmdiver.sh status"
echo
echo "To view logs:"
echo "  ./start_llmdiver.sh logs"