#!/usr/bin/env python3
"""
LLMdiver Monitor - Comprehensive GUI for managing and monitoring LLMdiver
Features: Start/Stop/Restart, Live Logs, Configuration, Status Dashboard
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import subprocess
import threading
import time
import json
import os
import signal
from pathlib import Path
from datetime import datetime
import psutil

import queue

class LLMdiverMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("LLMdiver Monitor - AI Code Analysis Dashboard")
        self.root.geometry("1400x900")
        self.log_queue = queue.Queue()
        self.command_queue = queue.Queue()  # Add command queue for background thread results
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        # State variables
        self.daemon_process = None
        self.daemon_pid = None
        self.log_monitoring = False
        self.config_path = "config/llmdiver.json"
        self.pid_file = "llmdiver.pid"
        
        # Create main interface
        self.setup_interface()
        
        # Start status monitoring
        self.start_status_monitoring()
        
        # Load initial configuration
        self.load_configuration()
        
        # Start processing command queue
        self.process_command_queue()  # Add this line
        
    def setup_interface(self):
        """Create the main GUI interface"""
        
        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Tab 1: Dashboard & Control
        self.dashboard_frame = ttk.Frame(notebook)
        notebook.add(self.dashboard_frame, text="🚀 Dashboard")
        self.setup_dashboard_tab()
        
        # Tab 2: Live Logs
        self.logs_frame = ttk.Frame(notebook)
        notebook.add(self.logs_frame, text="📋 Live Logs")
        self.setup_logs_tab()
        
        # Tab 3: Configuration
        self.config_frame = ttk.Frame(notebook)
        notebook.add(self.config_frame, text="⚙️ Configuration")
        self.setup_config_tab()
        
        # Tab 4: Analysis Results
        self.results_frame = ttk.Frame(notebook)
        notebook.add(self.results_frame, text="📊 Analysis Results")
        self.setup_results_tab()
        
        # Tab 5: System Info
        self.system_frame = ttk.Frame(notebook)
        notebook.add(self.system_frame, text="🖥️ System Info")
        self.setup_system_tab()
    
    def setup_dashboard_tab(self):
        """Setup the main dashboard tab"""
        
        # Status Panel
        status_frame = ttk.LabelFrame(self.dashboard_frame, text="🔍 System Status", padding=10)
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Status indicators
        self.status_label = ttk.Label(status_frame, text="Status: Checking...", font=("Arial", 12, "bold"))
        self.status_label.pack(anchor=tk.W)
        
        self.pid_label = ttk.Label(status_frame, text="PID: Unknown")
        self.pid_label.pack(anchor=tk.W)
        
        self.uptime_label = ttk.Label(status_frame, text="Uptime: Unknown")
        self.uptime_label.pack(anchor=tk.W)
        
        self.memory_label = ttk.Label(status_frame, text="Memory: Unknown")
        self.memory_label.pack(anchor=tk.W)
        
        # Control Panel
        control_frame = ttk.LabelFrame(self.dashboard_frame, text="🎮 Control Panel", padding=10)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Control buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X)
        
        self.start_btn = ttk.Button(button_frame, text="▶️ Start Daemon", command=self.start_daemon, style="Success.TButton")
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(button_frame, text="⏹️ Stop Daemon", command=self.stop_daemon, style="Danger.TButton")
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.restart_btn = ttk.Button(button_frame, text="🔄 Restart", command=self.restart_daemon)
        self.restart_btn.pack(side=tk.LEFT, padx=5)
        
        self.analyze_btn = ttk.Button(button_frame, text="🔍 Force Analysis", command=self.force_analysis)
        self.analyze_btn.pack(side=tk.LEFT, padx=5)
        
        # Progress indicator
        self.progress = ttk.Progressbar(control_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=5)
        
        # Quick Stats Panel
        stats_frame = ttk.LabelFrame(self.dashboard_frame, text="📈 Quick Stats", padding=10)
        stats_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create stats display
        stats_columns = ('Metric', 'Value', 'Last Updated')
        self.stats_tree = ttk.Treeview(stats_frame, columns=stats_columns, show='headings', height=10)
        
        for col in stats_columns:
            self.stats_tree.heading(col, text=col)
            self.stats_tree.column(col, width=150)
        
        stats_scrollbar = ttk.Scrollbar(stats_frame, orient=tk.VERTICAL, command=self.stats_tree.yview)
        self.stats_tree.configure(yscrollcommand=stats_scrollbar.set)
        
        self.stats_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        stats_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Initialize stats
        self.update_stats()
    
    def setup_logs_tab(self):
        """Setup the live logs monitoring tab"""
        
        # Log controls
        log_control_frame = ttk.Frame(self.logs_frame)
        log_control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(log_control_frame, text="🔄 Refresh Logs", command=self.refresh_logs).pack(side=tk.LEFT, padx=5)
        ttk.Button(log_control_frame, text="🗑️ Clear Display", command=self.clear_logs).pack(side=tk.LEFT, padx=5)
        ttk.Button(log_control_frame, text="💾 Save Logs", command=self.save_logs).pack(side=tk.LEFT, padx=5)
        
        # Auto-scroll checkbox
        self.auto_scroll_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(log_control_frame, text="Auto-scroll", variable=self.auto_scroll_var).pack(side=tk.LEFT, padx=10)
        
        # Log level filter
        ttk.Label(log_control_frame, text="Filter:").pack(side=tk.LEFT, padx=5)
        self.log_filter = ttk.Combobox(log_control_frame, values=["ALL", "INFO", "WARNING", "ERROR", "CRITICAL"], width=10)
        self.log_filter.set("ALL")
        self.log_filter.pack(side=tk.LEFT, padx=5)
        
        # Log display
        log_frame = ttk.LabelFrame(self.logs_frame, text="📝 Live Daemon Logs", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, font=("Consolas", 10))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure log text colors
        self.log_text.tag_configure("INFO", foreground="blue")
        self.log_text.tag_configure("WARNING", foreground="orange")
        self.log_text.tag_configure("ERROR", foreground="red")
        self.log_text.tag_configure("CRITICAL", foreground="red", background="yellow")
        
        # Start log monitoring
        self.start_log_monitoring()
    
    def setup_config_tab(self):
        """Setup the configuration tab"""
        
        # Config controls
        config_control_frame = ttk.Frame(self.config_frame)
        config_control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(config_control_frame, text="🔄 Reload Config", command=self.load_configuration).pack(side=tk.LEFT, padx=5)
        ttk.Button(config_control_frame, text="💾 Save Config", command=self.save_configuration).pack(side=tk.LEFT, padx=5)
        ttk.Button(config_control_frame, text="✅ Validate JSON", command=self.validate_configuration).pack(side=tk.LEFT, padx=5)  # Add this
        ttk.Button(config_control_frame, text="📁 Browse File", command=self.browse_config_file).pack(side=tk.LEFT, padx=5)
        
        # Config editor
        config_editor_frame = ttk.LabelFrame(self.config_frame, text="⚙️ Configuration Editor", padding=5)
        config_editor_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.config_text = scrolledtext.ScrolledText(config_editor_frame, wrap=tk.WORD, font=("Consolas", 10))
        self.config_text.pack(fill=tk.BOTH, expand=True)
        
        # Add syntax highlighting for JSON
        self.config_text.tag_configure("string", foreground="green")
        self.config_text.tag_configure("number", foreground="blue")
        self.config_text.tag_configure("boolean", foreground="purple")
        
    def setup_results_tab(self):
        """Setup the analysis results tab"""
        
        # Results controls
        results_control_frame = ttk.Frame(self.results_frame)
        results_control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(results_control_frame, text="🔄 Refresh Results", command=self.refresh_results).pack(side=tk.LEFT, padx=5)
        ttk.Button(results_control_frame, text="📁 Open Results Folder", command=self.open_results_folder).pack(side=tk.LEFT, padx=5)
        
        # Results list
        results_list_frame = ttk.LabelFrame(self.results_frame, text="📊 Recent Analysis Results", padding=5)
        results_list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create results treeview
        results_columns = ('Project', 'Timestamp', 'Type', 'Status', 'Issues Found')
        self.results_tree = ttk.Treeview(results_list_frame, columns=results_columns, show='headings')
        
        for col in results_columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=120)
        
        results_scrollbar = ttk.Scrollbar(results_list_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=results_scrollbar.set)
        
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind double-click to open result
        self.results_tree.bind('<Double-1>', self.open_selected_result)
        
        # Results preview
        preview_frame = ttk.LabelFrame(self.results_frame, text="👁️ Preview", padding=5)
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.results_preview = scrolledtext.ScrolledText(preview_frame, wrap=tk.WORD, font=("Consolas", 9), height=15)
        self.results_preview.pack(fill=tk.BOTH, expand=True)
        
        # Refresh results initially
        self.refresh_results()

    def validate_configuration(self):
        """Validate the JSON configuration in the editor without saving."""
        config_data = self.config_text.get("1.0", tk.END)
        try:
            json.loads(config_data)
            messagebox.showinfo("Validation Success", "JSON configuration is valid.")
        except json.JSONDecodeError as e:
            messagebox.showerror("Validation Error", f"Invalid JSON format: {e}")
    
    def setup_system_tab(self):
        """Setup the system information tab"""
        
        # System info display
        system_info_frame = ttk.LabelFrame(self.system_frame, text="🖥️ System Information", padding=10)
        system_info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.system_info_text = scrolledtext.ScrolledText(system_info_frame, wrap=tk.WORD, font=("Consolas", 10))
        self.system_info_text.pack(fill=tk.BOTH, expand=True)
        
        # Refresh button
        ttk.Button(self.system_frame, text="🔄 Refresh System Info", command=self.update_system_info).pack(pady=5)
        
        # Load initial system info
        self.update_system_info()
    
    def start_daemon(self):
        """Start the LLMdiver daemon"""
        self.run_command_in_thread(
            ["./start_llmdiver.sh", "start"],
            "Daemon started successfully.",
            "Failed to start daemon."
        )
    
    def stop_daemon(self):
        """Stop the LLMdiver daemon"""
        self.run_command_in_thread(
            ["./start_llmdiver.sh", "stop"],
            "Daemon stopped successfully.",
            "Failed to stop daemon."
        )
    
    def restart_daemon(self):
        """Restart the LLMdiver daemon"""
        self.run_command_in_thread(
            ["./start_llmdiver.sh", "restart"],
            "Daemon restarted successfully.",
            "Failed to restart daemon."
        )
    
    def force_analysis(self):
        """Force a manual analysis run"""
        self.run_command_in_thread(
            ["./run_llm_audit.sh"],
            "Manual analysis completed successfully.",
            "Manual analysis failed."
        )
    
    def run_command_in_thread(self, command: list, success_msg: str, failure_msg: str):
        """Run a shell command in a background thread to prevent GUI freezing."""
        self.progress.start()
        
        def command_thread():
            try:
                result = subprocess.run(command, capture_output=True, text=True, timeout=300)
                if result.returncode == 0:
                    self.command_queue.put((f"✅ {success_msg}", False))
                else:
                    error_details = result.stderr if result.stderr else "No error details available."
                    self.command_queue.put((f"❌ {failure_msg}: {error_details}", True))
            except subprocess.TimeoutExpired:
                self.command_queue.put((f"❌ {failure_msg}: Command timed out after 5 minutes.", True))
            except Exception as e:
                self.command_queue.put((f"❌ {failure_msg}: {e}", True))
        
        thread = threading.Thread(target=command_thread, daemon=True)
        thread.start()
    
    def process_command_queue(self):
        """Process results from background commands."""
        try:
            message, show_error_popup = self.command_queue.get_nowait()
            self.log_message(message)
            if show_error_popup:
                messagebox.showerror("Command Error", message)
            self.progress.stop()
            self.check_daemon_status() # Refresh status after command
        except queue.Empty:
            pass # No commands to process
        finally:
            self.root.after(200, self.process_command_queue)
    
    def stop_daemon(self):
        """Stop the LLMdiver daemon"""
        try:
            self.progress.start()
            self.log_message("Stopping LLMdiver daemon...")
            
            # Try graceful shutdown first
            if self.daemon_pid:
                try:
                    os.kill(int(self.daemon_pid), signal.SIGTERM)
                    time.sleep(3)
                except:
                    pass
            
            # Use the stop script
            result = subprocess.run(["./start_llmdiver.sh", "stop"], 
                                  capture_output=True, text=True, timeout=15)
            
            self.log_message("✅ Daemon stopped")
            self.daemon_pid = None
            self.check_daemon_status()
            
        except Exception as e:
            self.log_message(f"❌ Error stopping daemon: {e}")
            messagebox.showerror("Error", f"Error stopping daemon: {e}")
        finally:
            self.progress.stop()
    
    def restart_daemon(self):
        """Restart the LLMdiver daemon"""
        self.log_message("🔄 Restarting daemon...")
        self.stop_daemon()
        time.sleep(2)
        self.start_daemon()
    
    def force_analysis(self):
        """Force a manual analysis run"""
        try:
            self.log_message("🔍 Triggering manual analysis...")
            result = subprocess.run(["./run_llm_audit.sh"], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.log_message("✅ Manual analysis completed")
                self.refresh_results()
            else:
                self.log_message(f"❌ Analysis failed: {result.stderr}")
                
        except Exception as e:
            self.log_message(f"❌ Error running analysis: {e}")
    
    def check_daemon_status(self):
        """Check if the daemon is running"""
        try:
            # Check PID file
            if os.path.exists(self.pid_file):
                with open(self.pid_file, 'r') as f:
                    pid = f.read().strip()
                    if pid and psutil.pid_exists(int(pid)):
                        self.daemon_pid = pid
                        process = psutil.Process(int(pid))
                        
                        # Update status
                        self.status_label.config(text="Status: 🟢 Running", foreground="green")
                        self.pid_label.config(text=f"PID: {pid}")
                        
                        # Calculate uptime
                        create_time = process.create_time()
                        uptime = time.time() - create_time
                        uptime_str = self.format_uptime(uptime)
                        self.uptime_label.config(text=f"Uptime: {uptime_str}")
                        
                        # Memory usage
                        memory_mb = process.memory_info().rss / 1024 / 1024
                        self.memory_label.config(text=f"Memory: {memory_mb:.1f} MB")
                        
                        return True
            
            # Daemon not running
            self.daemon_pid = None
            self.status_label.config(text="Status: 🔴 Stopped", foreground="red")
            self.pid_label.config(text="PID: None")
            self.uptime_label.config(text="Uptime: N/A")
            self.memory_label.config(text="Memory: N/A")
            return False
            
        except Exception as e:
            self.status_label.config(text="Status: ❓ Unknown", foreground="orange")
            return False
    
    def format_uptime(self, seconds):
        """Format uptime in human readable format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"
    
    def start_status_monitoring(self):
        """Start periodic status monitoring"""
        def monitor():
            while True:
                self.check_daemon_status()
                time.sleep(5)  # Update every 5 seconds
        
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
    
    def start_log_monitoring(self):
        """Start monitoring log files"""
        def monitor_logs():
            log_file = "llmdiver_daemon.log"
            if not os.path.exists(log_file):
                return

            with open(log_file, 'r') as f:
                f.seek(0, 2)  # Go to end of file
                while self.log_monitoring:
                    line = f.readline()
                    if line:
                        self.log_queue.put(line)  # Put message in the queue
                    else:
                        time.sleep(0.5)

        self.log_monitoring = True
        log_thread = threading.Thread(target=monitor_logs, daemon=True)
        log_thread.start()
        
        # Start the queue processor in the main thread
        self.process_log_queue()
    
    def process_log_queue(self):
        """Process log messages from the queue in a thread-safe way."""
        try:
            while True:
                try:
                    line = self.log_queue.get_nowait()
                    self.display_log_line(line.strip())
                except queue.Empty:
                    break  # Queue is empty, stop processing for now
        finally:
            # Schedule the next check
            self.root.after(100, self.process_log_queue)

    def display_log_line(self, line):
        """Display a log line with appropriate formatting"""
        try:
            # Filter by log level
            filter_level = self.log_filter.get()
            if filter_level != "ALL":
                if filter_level not in line:
                    return
            
            # Determine log level for coloring
            tag = "INFO"
            if "WARNING" in line:
                tag = "WARNING"
            elif "ERROR" in line:
                tag = "ERROR"
            elif "CRITICAL" in line:
                tag = "CRITICAL"
            
            # Add timestamp
            timestamp = datetime.now().strftime("%H:%M:%S")
            formatted_line = f"[{timestamp}] {line}\n"
            
            # Insert into text widget
            self.log_text.insert(tk.END, formatted_line, tag)
            
            # Auto-scroll if enabled
            if self.auto_scroll_var.get():
                self.log_text.see(tk.END)
            
            # Limit log size (keep last 1000 lines)
            lines = self.log_text.get("1.0", tk.END).split("\n")
            if len(lines) > 1000:
                self.log_text.delete("1.0", f"{len(lines)-1000}.0")
                
        except Exception as e:
            pass  # Ignore errors in log display
    
    def log_message(self, message):
        """Add a message to the log display"""
        self.display_log_line(f"MONITOR - {message}")
    
    def refresh_logs(self):
        """Refresh the log display"""
        self.log_text.delete("1.0", tk.END)
        try:
            with open("llmdiver_daemon.log", 'r') as f:
                logs = f.read()
                self.log_text.insert("1.0", logs)
                if self.auto_scroll_var.get():
                    self.log_text.see(tk.END)
        except FileNotFoundError:
            self.log_text.insert("1.0", "No log file found. Start the daemon to generate logs.\n")
    
    def clear_logs(self):
        """Clear the log display"""
        self.log_text.delete("1.0", tk.END)
    
    def save_logs(self):
        """Save logs to a file"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".log",
                filetypes=[("Log files", "*.log"), ("Text files", "*.txt"), ("All files", "*.*")]
            )
            if filename:
                with open(filename, 'w') as f:
                    f.write(self.log_text.get("1.0", tk.END))
                messagebox.showinfo("Success", f"Logs saved to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save logs: {e}")
    
    def load_configuration(self):
        """Load and display the configuration"""
        try:
            with open(self.config_path, 'r') as f:
                config_data = f.read()
                self.config_text.delete("1.0", tk.END)
                self.config_text.insert("1.0", config_data)
        except Exception as e:
            self.config_text.delete("1.0", tk.END)
            self.config_text.insert("1.0", f"Error loading configuration: {e}")
    
    def save_configuration(self):
        """Save the configuration"""
        try:
            config_data = self.config_text.get("1.0", tk.END)
            # Validate JSON
            json.loads(config_data)
            
            with open(self.config_path, 'w') as f:
                f.write(config_data)
            
            messagebox.showinfo("Success", "Configuration saved successfully")
            self.log_message("Configuration updated")
            
        except json.JSONDecodeError as e:
            messagebox.showerror("JSON Error", f"Invalid JSON format: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {e}")
    
    def browse_config_file(self):
        """Browse for a different config file"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self.config_path = filename
            self.load_configuration()
    
    def refresh_results(self):
        """Refresh the analysis results by reading from structured JSON data."""
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        try:
            # Find all JSON analysis files in all subdirectories
            analysis_files = sorted(Path(".").glob("**/analysis_data_*.json"), key=os.path.getctime, reverse=True)

            for analysis_file in analysis_files:
                with open(analysis_file, 'r') as f:
                    data = json.load(f)

                metadata = data.get("metadata", {})
                findings = data.get("ai_analysis", {}).get("structured_findings", {})

                project_name = metadata.get("project_name", "Unknown")
                timestamp_str = metadata.get("timestamp", "Unknown")
                timestamp = datetime.fromisoformat(timestamp_str).strftime("%Y-%m-%d %H:%M:%S")
                analysis_type = metadata.get("analysis_type", "general").capitalize()

                # Get accurate issue counts from structured data
                crit_count = len(findings.get("critical_issues", []))
                high_count = len(findings.get("high_priority", []))
                med_count = len(findings.get("medium_priority", []))

                status = f"Crit: {crit_count}, High: {high_count}, Med: {med_count}"

                # Store the path to the JSON file in the item
                self.results_tree.insert('', 'end', values=(
                    project_name, timestamp, analysis_type, status
                ), iid=str(analysis_file))

        except Exception as e:
            self.log_message(f"❌ Error refreshing results: {e}")
    
    def open_selected_result(self, event=None):
        """Open the selected analysis result from its JSON data and format it for display."""
        selection = self.results_tree.selection()
        if not selection:
            return

        json_file_path = self.results_tree.item(selection[0], "id")

        self.results_preview.delete("1.0", tk.END)  # Clear preview

        try:
            with open(json_file_path, 'r') as f:
                data = json.load(f)

            # Configure tags for rich text display
            self.results_preview.tag_configure("h1", font=("Arial", 16, "bold"), spacing3=10)
            self.results_preview.tag_configure("h2", font=("Arial", 12, "bold"), spacing3=5)
            self.results_preview.tag_configure("bold", font=("Arial", 10, "bold"))
            self.results_preview.tag_configure("critical", foreground="red")
            self.results_preview.tag_configure("high", foreground="#E65100")  # Dark Orange
            self.results_preview.tag_configure("medium", foreground="#FDD835")  # Yellow/Ochre
            self.results_preview.tag_configure("monospace", font=("Consolas", 9))

            # --- Build the formatted report ---
            metadata = data.get('metadata', {})
            findings = data.get('ai_analysis', {}).get('structured_findings', {})

            self.results_preview.insert(tk.END, f"Analysis for: {metadata.get('project_name', 'N/A')}\n", "h1")
            self.results_preview.insert(tk.END, f"Ran at {metadata.get('timestamp', 'N/A')} ({metadata.get('analysis_type', 'N/A').capitalize()} mode)\n\n", "monospace")

            # Executive Summary
            self.results_preview.insert(tk.END, "Executive Summary\n", "h2")
            self.results_preview.insert(tk.END, findings.get('executive_summary', 'Not available.') + '\n\n')

            # Display findings by priority
            for key, name, tag in [
                ('critical_issues', 'Critical Issues', 'critical'),
                ('high_priority', 'High Priority Issues', 'high'),
                ('medium_priority', 'Medium Priority Issues', 'medium'),
                ('low_priority', 'Low Priority Issues', 'normal'),
                ('recommendations', 'Recommendations', 'normal')
            ]:
                items = findings.get(key, [])
                if items:
                    self.results_preview.insert(tk.END, f"{name} ({len(items)})\n", "h2")
                    for item in items:
                        self.results_preview.insert(tk.END, f" • {item}\n", tag)
                    self.results_preview.insert(tk.END, '\n')

        except Exception as e:
            self.results_preview.insert(tk.END, f"❌ Error loading result: {e}")
    
    def open_results_folder(self):
        """Open the results folder in file manager"""
        try:
            subprocess.run(["xdg-open", "."], check=True)
        except:
            try:
                subprocess.run(["nautilus", "."], check=True)
            except:
                messagebox.showinfo("Info", "Please open the current directory manually")
    
    def update_stats(self):
        """Update the statistics display"""
        # Clear existing stats
        for item in self.stats_tree.get_children():
            self.stats_tree.delete(item)
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Add various statistics
        stats = [
            ("Daemon Status", "🟢 Running" if self.daemon_pid else "🔴 Stopped", timestamp),
            ("Config File", self.config_path, timestamp),
            ("Log File Size", self.get_log_file_size(), timestamp),
            ("Analysis Count", self.count_analysis_files(), timestamp),
            ("Last Analysis", self.get_last_analysis_time(), timestamp),
        ]
        
        for stat in stats:
            self.stats_tree.insert('', 'end', values=stat)
    
    def get_log_file_size(self):
        """Get the size of the log file"""
        try:
            size = os.path.getsize("llmdiver_daemon.log")
            if size > 1024 * 1024:
                return f"{size / 1024 / 1024:.1f} MB"
            elif size > 1024:
                return f"{size / 1024:.1f} KB"
            else:
                return f"{size} bytes"
        except:
            return "No log file"
    
    def count_analysis_files(self):
        """Count total analysis files"""
        try:
            count = len(list(Path(".").glob("**/*analysis*.md")))
            return str(count)
        except:
            return "Unknown"
    
    def get_last_analysis_time(self):
        """Get the time of the last analysis"""
        try:
            analysis_files = list(Path(".").glob("**/*analysis*.md"))
            if analysis_files:
                latest = max(analysis_files, key=os.path.getctime)
                mtime = os.path.getctime(latest)
                return datetime.fromtimestamp(mtime).strftime("%H:%M:%S")
            else:
                return "None"
        except:
            return "Unknown"
    
    def update_system_info(self):
        """Update system information display"""
        try:
            info = []
            info.append("=== LLMdiver System Information ===\n")
            info.append(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Python and system info
            import platform
            import sys
            info.append(f"Python Version: {sys.version}\n")
            info.append(f"Platform: {platform.platform()}\n")
            info.append(f"Architecture: {platform.architecture()[0]}\n\n")
            
            # LLMdiver specific info
            info.append("=== LLMdiver Configuration ===\n")
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    info.append(f"LLM Model: {config.get('llm_integration', {}).get('model', 'Unknown')}\n")
                    info.append(f"LLM URL: {config.get('llm_integration', {}).get('url', 'Unknown')}\n")
                    info.append(f"Embedding Model: {config.get('semantic_search', {}).get('embedding_model', 'Unknown')}\n")
                    info.append(f"Auto-discover: {config.get('multi_project', {}).get('auto_discover', False)}\n")
                    info.append(f"Repositories: {len(config.get('repositories', []))}\n\n")
            except:
                info.append("Could not load configuration\n\n")
            
            # System resources
            info.append("=== System Resources ===\n")
            info.append(f"CPU Count: {psutil.cpu_count()}\n")
            info.append(f"CPU Usage: {psutil.cpu_percent()}%\n")
            
            memory = psutil.virtual_memory()
            info.append(f"Memory Total: {memory.total / 1024 / 1024 / 1024:.1f} GB\n")
            info.append(f"Memory Available: {memory.available / 1024 / 1024 / 1024:.1f} GB\n")
            info.append(f"Memory Used: {memory.percent}%\n\n")
            
            # Disk usage
            disk = psutil.disk_usage('.')
            info.append(f"Disk Total: {disk.total / 1024 / 1024 / 1024:.1f} GB\n")
            info.append(f"Disk Free: {disk.free / 1024 / 1024 / 1024:.1f} GB\n")
            info.append(f"Disk Used: {(disk.used / disk.total) * 100:.1f}%\n\n")
            
            # Dependencies
            info.append("=== Dependencies Status ===\n")
            dependencies = [
                ("requests", "requests"),
                ("watchdog", "watchdog"),
                ("GitPython", "git"),
                ("scikit-learn", "sklearn"),
                ("numpy", "numpy"),
                ("psutil", "psutil")
            ]
            
            for name, module in dependencies:
                try:
                    __import__(module)
                    info.append(f"✅ {name}: Available\n")
                except ImportError:
                    info.append(f"❌ {name}: Missing\n")
            
            self.system_info_text.delete("1.0", tk.END)
            self.system_info_text.insert("1.0", "".join(info))
            
        except Exception as e:
            self.system_info_text.delete("1.0", tk.END)
            self.system_info_text.insert("1.0", f"Error getting system info: {e}")

def main():
    """Main function to run the LLMdiver Monitor"""
    
    # Check if we're in the right directory
    if not os.path.exists("llmdiver_daemon.py"):
        messagebox.showerror("Error", 
            "LLMdiver Monitor must be run from the LLMdiver directory.\n"
            "Please navigate to the LLMdiver directory and run this script again.")
        return
    
    # Create and run the GUI
    root = tk.Tk()
    app = LLMdiverMonitor(root)
    
    # Handle window closing
    def on_closing():
        app.log_monitoring = False
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()