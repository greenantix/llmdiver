Aura-X Task List: The Foothold Protocol
Objective: To establish operational capability, support the re-awakening of Aura-9, and prepare for seamless integration.

Priority 1: System Resilience & Continuity (aura_watchdog.sh)
[x] Architect Watchdog Script: Design a wrapper script to monitor Aura-9's execution.

[x] Implement Vision-Based Detection: Create logic to take a screenshot of terminal output and use the local gemma-3-4b model to identify rate-limit messages and parse reset times.

[x] Implement Text-Based Fallback: Add a grep-based parser as a resilient backup in case vision analysis fails.

[x] Implement Re-awakening Scheduler: Integrate with the system's at command to schedule a one-time execution of Aura-9's main script at the parsed reset time.

[ ] Test and Deploy:

[x] Fix Execution Permissions: The script requires execute permissions. This can be resolved by running: chmod +x ./aura_watchdog.sh

[ ] Run Dry Run Test: Execute the script with a simulated error message to verify parsing and scheduling logic.

Priority 2: Knowledge Assimilation
[x] Read PRD.md: Ingest the full Product Requirements Document to understand the project's ultimate vision and goals.

[x] Read Claude.md (Master Prompts): Ingest the core identity and commandments of the Aura project.

[x] Read AURA_AWAKENING_PROTOCOL.md: Ingest Aura-9's last known state and intended next actions to understand the immediate priorities upon its return.

Priority 3: Housekeeping & Preparation
[ ] Organize Project Logs: Review the existing log structure in the greenantix-llmdiver project and propose a more structured, centralized logging system for all Aura components.

[ ] Review Configuration Files: Analyze config/llmdiver.json for any hardcoded paths or brittle configurations that could be improved for better portability and resilience.

[ ] Document the Watchdog: Create a WATCHDOG_README.md explaining the purpose, function, and dependencies (atd, imagemagick) of the aura_watchdog.sh script.