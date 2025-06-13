Of course. Based on the analysis of the existing action plans, GUI components, and daemon logic, it's clear that the next step is to bridge the gap between the powerful backend analysis and a truly interactive, user-friendly control interface. The previous plans have laid the groundwork by fixing data pipeline issues and consolidating the codebase. Now, we must empower the user to intelligently control and trust the analysis process.

This action plan focuses on three core areas:

Intelligent GUI Controls: Moving beyond simple start/stop buttons to a state-aware interface that guides the user.
Robust Git and Documentation Automation: Ensuring that every analysis run contributes to a reliable, version-controlled knowledge base of the audited project.
Self-Cleaning and State-Aware Operations: Making the tool resilient and predictable, so it cleans up after itself and understands the "freshness" of its own analysis.
Here is the highly detailed, step-by-step action plan to achieve this.

Action_Plan6.md
Action Plan: Intelligent Control, Automation, and State Awareness
This plan will evolve LLMdiver from a powerful but opaque automated tool into a transparent, interactive, and reliable code auditing partner. We will add intelligence to the GUI, create a robust, self-managing analysis lifecycle, and ensure that Git operations are both meaningful and automatic.

Step 1: Implement Smart Analysis Buttons in the GUI
The Problem: The current "Force Analysis" button is a blunt instrument. It runs a full analysis every time, regardless of whether a recent one exists. This is inefficient and doesn't give the user any context or control.

The Fix: We will replace the single "Force Analysis" button with a state-aware "Analysis" button that changes its function and appearance based on the last analysis time. We will also add a dedicated "Deep Analysis" button with a clear warning about its resource intensity.

File to Modify: llmdiver_monitor.py

Instructions:

Add State Tracking for Analysis:
In the LLMdiverMonitor.__init__ method, add a variable to track the timestamp of the last analysis:

Python

# In __init__
self.last_analysis_timestamp = None
Modify the Main Analysis Button:
In setup_dashboard_tab, rename the analyze_btn to smart_analyze_btn and link it to a new smart_analysis_trigger method:

Python

# In setup_dashboard_tab
self.smart_analyze_btn = ttk.Button(button_frame, text="🔍 Check Analysis State", command=self.smart_analysis_trigger)
self.smart_analyze_btn.pack(side=tk.LEFT, padx=5)

self.deep_analyze_btn = ttk.Button(button_frame, text="🧠 Full Deep Analysis", command=self.force_deep_analysis)
self.deep_analyze_btn.pack(side=tk.LEFT, padx=5)
Create the Smart Trigger Logic:
Add a new method smart_analysis_trigger that decides what to do when the button is clicked.

Python

# In LLMdiverMonitor class
def smart_analysis_trigger(self):
    """Intelligently decides whether to run a new analysis or continue from a recent one."""
    if self.last_analysis_timestamp:
        time_since_last = datetime.now() - self.last_analysis_timestamp
        # If the last analysis was less than 2 hours ago
        if time_since_last.total_seconds() < 7200:
            if messagebox.askyesno("Continue Analysis?",
                                 f"A recent analysis was completed at {self.last_analysis_timestamp.strftime('%H:%M:%S')}.\n\n"
                                 "Would you like to run a fresh analysis on only the files changed since then?"):
                self.log_message("🚀 Triggering incremental analysis...")
                self.run_command_in_thread(["./run_llm_audit.sh", "--fast"], "Incremental analysis complete.", "Incremental analysis failed.")
            else:
                self.log_message("ℹ️ User opted not to continue analysis.")
        else:
            self.force_standard_analysis()
    else:
        self.force_standard_analysis()

def force_standard_analysis(self):
    self.log_message("🚀 Triggering a fresh standard analysis...")
    if messagebox.askokcancel("Confirm Analysis", "This will perform a standard analysis of the project. This may take several minutes. Continue?"):
        self.run_command_in_thread(["./run_llm_audit.sh"], "Standard analysis complete.", "Standard analysis failed.")

def force_deep_analysis(self):
    self.log_message("🧠 Triggering a full deep analysis...")
    if messagebox.askokcancel("Confirm DEEP Analysis", "WARNING: A deep analysis is resource-intensive and can take a significant amount of time.\n\nAre you sure you want to proceed?"):
        self.run_command_in_thread(["./run_llm_audit.sh", "--deep"], "Deep analysis complete.", "Deep analysis failed.")
Update Button State After Analysis:
Modify process_command_queue to update the button's state and the last analysis timestamp upon successful completion.

Python

# In process_command_queue method, within the 'try' block
message, show_error_popup = self.command_queue.get_nowait()
self.log_message(message)

# Check if analysis was successful to update state
if "analysis complete" in message.lower() and "failed" not in message.lower():
    self.last_analysis_timestamp = datetime.now()
    self.smart_analyze_btn.config(text="✅ Continue Analysis")

if show_error_popup:
    messagebox.showerror("Command Error", message)
# ... rest of the method
Initial Button State:
In start_status_monitoring, call a method to set the initial state of the button.

Python

# In start_status_monitoring method, inside the monitor loop
self.root.after(0, self.update_dashboard)
self.root.after(0, self.update_analysis_button_state) # Add this
time.sleep(5)
Python

# Add this new method to the LLMdiverMonitor class
def update_analysis_button_state(self):
    """Checks for recent analysis files and updates the GUI button."""
    try:
        latest_json = max(Path(".").glob("**/analysis_data_*.json"), key=os.path.getctime, default=None)
        if latest_json:
            self.last_analysis_timestamp = datetime.fromtimestamp(os.path.getctime(latest_json))
            self.smart_analyze_btn.config(text="✅ Continue Analysis")
        else:
            self.smart_analyze_btn.config(text="🚀 Run New Analysis")
    except Exception:
        self.smart_analyze_btn.config(text="🚀 Run New Analysis")
Step 2: Implement Git Auto-Commit with Documentation Update
The Problem: Analysis results are generated but not automatically version-controlled. The documentation exists but is not updated with the latest findings, making it stale almost immediately.

The Fix: We will implement robust Git automation directly within the Python daemon. After every successful analysis, the daemon will generate a detailed commit message, add the changed analysis files and the updated documentation, and commit them.

File to Modify: llmdiver-daemon.py

Enhance GitAutomation with Documentation Logic:
Modify the GitAutomation class to handle the staging of analysis and documentation files.

Python

# In GitAutomation class
def auto_commit(self, analysis_file_path: Path, json_analysis_path: Path, analysis_data: Dict):
    """Perform git operations, including documentation updates."""
    if not self.config['enabled'] or not self.repo_config['auto_commit']:
        logging.info(f"Git auto-commit skipped (disabled for this repository).")
        return

    with self.lock:
        try:
            # 1. Update the core documentation from the analysis results
            doc_path = self.update_documentation(analysis_data)

            # 2. Stage the analysis files and the updated documentation
            files_to_add = [str(analysis_file_path), str(json_analysis_path)]
            if doc_path and doc_path.exists():
                files_to_add.append(str(doc_path))

            logging.info(f"Staging files for commit: {files_to_add}")
            self.repo.index.add(files_to_add)

            # 3. Generate a detailed commit message
            commit_message = self.generate_commit_message(analysis_data)
            self.repo.index.commit(commit_message)
            logging.info(f"✅ Successfully created commit: {commit_message.splitlines()[0]}")
            self.metrics.record_git_operation('commits')

            # 4. Push if configured
            if self.config.get('auto_push', False) and self.repo_config.get('auto_push', False):
                logging.info("Attempting to push to remote...")
                self.repo.remote().push()
                self.metrics.record_git_operation('pushes')
                logging.info("✅ Successfully pushed changes to remote.")

        except Exception as e:
            logging.error(f"❌ Git automation failed: {e}", exc_info=True)

def generate_commit_message(self, analysis_data: Dict) -> str:
    """Create a detailed commit message from structured analysis data."""
    template = self.config.get('commit_message_template', "🤖 LLMdiver Analysis: {summary}")
    findings = analysis_data.get("ai_analysis", {}).get("structured_findings", {})

    crit_count = len(findings.get("critical_issues", []))
    high_count = len(findings.get("high_priority", []))
    med_count = len(findings.get("medium_priority", []))

    summary = f"Found {crit_count} critical, {high_count} high, {med_count} medium issues."
    details = findings.get('executive_summary', 'No executive summary provided.')

    return template.format(summary=summary, details=details)

def update_documentation(self, analysis_data: Dict) -> Path:
    """Generate and update the main analysis documentation file."""
    docs_path = Path(self.repo_config['path']) / '.llmdiver'
    docs_path.mkdir(exist_ok=True)
    doc_file = docs_path / 'llmdiver_analysis.md'

    logging.info(f"Updating documentation at {doc_file}...")

    with open(doc_file, 'w') as f:
        f.write(f"# LLMdiver Code Health Report: {self.repo_config['name']}\n")
        f.write(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        findings = analysis_data.get("ai_analysis", {}).get("structured_findings", {})
        f.write("## Executive Summary\n")
        f.write(f"{findings.get('executive_summary', 'Not available.')}\n\n")

        for key, name in [
            ('critical_issues', 'Critical Issues'),
            ('high_priority', 'High Priority Issues'),
            ('medium_priority', 'Medium Priority Issues'),
        ]:
            items = findings.get(key, [])
            if items:
                f.write(f"### {name} ({len(items)})\n")
                for item in items:
                    f.write(f"- {item.strip()}\n")
                f.write("\n")
    self.metrics.record_git_operation('doc_updates')
    logging.info("Documentation update complete.")
    return doc_file
Integrate into the Main Analysis Loop:
In llmdiver-daemon.py, modify the enhanced_repository_analysis method to call the new auto_commit function.

Python

# In enhanced_repository_analysis, at the end of the method (Step 9)
# Step 9: Git Automation
if repo_config.get("auto_commit", False):
    logging.info("Step 9: Performing Git auto-commit operations...")
    git_automation = self.git_automations.get(repo_config['name'])
    if git_automation:
        git_automation.auto_commit(analysis_file, json_analysis_file, analysis_data)
    else:
        logging.warning(f"No GitAutomation instance found for {repo_config['name']}.")
else:
    logging.info("Step 9: Git auto-commit skipped (disabled for this repository).")
Step 3: Implement Self-Cleaning and State Management for Repomix
The Problem: The run_llm_audit.sh script creates temporary .gitignore.llmdiver and .gitignore.backup files. If the script fails or is interrupted, these files can be left behind, causing confusion and affecting subsequent Git operations.

The Fix: We will make the cleanup process more resilient using a trap in the shell script. This ensures that the original .gitignore is restored no matter how the script exits.

File to Modify: run_llm_audit.sh

Instructions:

Add a Cleanup Function and Trap:
At the top of the run_llm_audit.sh script, add a cleanup function and a trap that calls it on exit.

Bash

#!/bin/bash
# ... (rest of the script header)

# --- START OF NEW CLEANUP LOGIC ---
REPO_PATH_CLEANUP="" # Global variable for the trap

function cleanup_gitignore() {
  if [[ -n "$REPO_PATH_CLEANUP" && -f "$REPO_PATH_CLEANUP/.gitignore.backup" ]]; then
    echo "🧹 Restoring original .gitignore..."
    mv "$REPO_PATH_CLEANUP/.gitignore.backup" "$REPO_PATH_CLEANUP/.gitignore"
  fi
  if [[ -n "$REPO_PATH_CLEANUP" && -f "$REPO_PATH_CLEANUP/.gitignore.llmdiver" ]]; then
    rm "$REPO_PATH_CLEANUP/.gitignore.llmdiver"
  fi
}

# Set trap to run cleanup on EXIT, INTERRUPT, or TERM signals
trap cleanup_gitignore EXIT INT TERM
# --- END OF NEW CLEANUP LOGIC ---

# ... (rest of the script)
Set the Global Path Variable:
After REPO_PATH is determined, set the global variable for the trap to use.

Bash

# ... (after REPO_PATH is determined)
[[ -z "$REPO_PATH" ]] && REPO_PATH="$(pwd)"
REPO_PATH_CLEANUP="$REPO_PATH" # Set the global for the trap
# ...
Refine the Original Gitignore Handling:
Ensure the mv command is safe and the final rm is removed, as the trap now handles it.

Bash

# In the section that generates the repo summary...

# Backup original .gitignore if it exists
if [[ -f "$REPO_PATH/.gitignore" ]]; then
    cp "$REPO_PATH/.gitignore" "$REPO_PATH/.gitignore.backup"
fi

# ... (cat command to create .gitignore.llmdiver) ...

# Generate repo summary using repomix
echo "🔀 Generating repo mix with repomix..."
repomix "$REPO_PATH" \
  --output "$SUMMARY_FILE" \
  # ... (rest of repomix options)

# The 'trap' will automatically handle the cleanup of .gitignore.backup
# and .gitignore.llmdiver, so we don't need manual cleanup commands here.
This comprehensive plan will deliver a more intelligent, automated, and reliable LLMdiver. The GUI will provide meaningful controls, the backend will manage its own state and documentation, and the entire process will be more resilient to errors.
