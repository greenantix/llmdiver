#!/usr/bin/env python3
"""
LLMdiver GUI Control Panel
Simple interface to manage the LLMdiver daemon
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import threading
import time
import os
import json
from pathlib import Path
import queue

class LLMdiverGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("LLMdiver Control Panel")
        self.root.geometry("900x700")
        
        # Queue for thread communication
        self.log_queue = queue.Queue()
        self.daemon_running = False
        self.log_thread = None
        self.stop_log_thread = False
        
        self.setup_ui()
        self.check_status()
        
        # Start log monitoring
        self.start_log_monitoring()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="🤖 LLMdiver Control Panel", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Status section
        status_frame = ttk.LabelFrame(main_frame, text="Daemon Status", padding="10")
        status_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        status_frame.columnconfigure(1, weight=1)
        
        self.status_label = ttk.Label(status_frame, text="Checking...", font=("Arial", 10, "bold"))
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        self.pid_label = ttk.Label(status_frame, text="PID: Unknown")
        self.pid_label.grid(row=0, column=1, sticky=tk.W, padx=(20, 0))
        
        # Control buttons
        control_frame = ttk.LabelFrame(main_frame, text="Daemon Control", padding="10")
        control_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.start_btn = ttk.Button(control_frame, text="▶️ Start", command=self.start_daemon)
        self.start_btn.grid(row=0, column=0, padx=(0, 5))
        
        self.stop_btn = ttk.Button(control_frame, text="⏹️ Stop", command=self.stop_daemon)
        self.stop_btn.grid(row=0, column=1, padx=5)
        
        self.restart_btn = ttk.Button(control_frame, text="🔄 Restart", command=self.restart_daemon)
        self.restart_btn.grid(row=0, column=2, padx=5)
        
        self.pause_btn = ttk.Button(control_frame, text="⏸️ Pause", command=self.pause_daemon)
        self.pause_btn.grid(row=0, column=3, padx=5)
        
        # Refresh button
        refresh_btn = ttk.Button(control_frame, text="🔍 Refresh Status", command=self.check_status)
        refresh_btn.grid(row=0, column=4, padx=(20, 0))
        
        # Projects section
        projects_frame = ttk.LabelFrame(main_frame, text="Monitored Projects", padding="10")
        projects_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        projects_frame.columnconfigure(0, weight=1)
        projects_frame.rowconfigure(0, weight=1)
        
        # Projects list
        self.projects_tree = ttk.Treeview(projects_frame, columns=("Path", "Auto-commit"), show="tree headings", height=8)
        self.projects_tree.heading("#0", text="Project")
        self.projects_tree.heading("Path", text="Path")
        self.projects_tree.heading("Auto-commit", text="Auto-commit")
        self.projects_tree.column("#0", width=150)
        self.projects_tree.column("Path", width=300)
        self.projects_tree.column("Auto-commit", width=80)
        
        projects_scroll = ttk.Scrollbar(projects_frame, orient=tk.VERTICAL, command=self.projects_tree.yview)
        self.projects_tree.configure(yscrollcommand=projects_scroll.set)
        
        self.projects_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        projects_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Log viewer
        log_frame = ttk.LabelFrame(main_frame, text="Live Logs", padding="10")
        log_frame.grid(row=3, column=1, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=50, 
                                                 font=("Consolas", 9))
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Log controls
        log_controls = ttk.Frame(log_frame)
        log_controls.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        clear_btn = ttk.Button(log_controls, text="Clear Logs", command=self.clear_logs)
        clear_btn.grid(row=0, column=0)
        
        self.auto_scroll_var = tk.BooleanVar(value=True)
        auto_scroll_cb = ttk.Checkbutton(log_controls, text="Auto-scroll", 
                                        variable=self.auto_scroll_var)
        auto_scroll_cb.grid(row=0, column=1, padx=(10, 0))
        
        # Update projects list
        self.update_projects_list()
        
    def run_command(self, command):
        """Run a shell command and return the result"""
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=".")
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)
            
    def check_status(self):
        """Check daemon status"""
        success, stdout, stderr = self.run_command("./start_llmdiver.sh status")
        
        if success and "is running" in stdout:
            self.daemon_running = True
            self.status_label.config(text="✅ Running", foreground="green")
            
            # Extract PID
            lines = stdout.split('\n')
            for line in lines:
                if "PID:" in line:
                    pid = line.split("PID:")[-1].strip().rstrip(")")
                    self.pid_label.config(text=f"PID: {pid}")
                    break
        else:
            self.daemon_running = False
            self.status_label.config(text="❌ Stopped", foreground="red")
            self.pid_label.config(text="PID: None")
            
        # Update button states
        self.start_btn.config(state="disabled" if self.daemon_running else "normal")
        self.stop_btn.config(state="normal" if self.daemon_running else "disabled")
        self.restart_btn.config(state="normal" if self.daemon_running else "disabled")
        self.pause_btn.config(state="normal" if self.daemon_running else "disabled")
        
    def start_daemon(self):
        """Start the daemon"""
        self.log_text.insert(tk.END, "🚀 Starting LLMdiver daemon...\n")
        success, stdout, stderr = self.run_command("./start_llmdiver.sh start")
        
        if success:
            self.log_text.insert(tk.END, "✅ Daemon started successfully\n")
        else:
            self.log_text.insert(tk.END, f"❌ Failed to start daemon: {stderr}\n")
            
        self.check_status()
        self.auto_scroll()
        
    def stop_daemon(self):
        """Stop the daemon"""
        self.log_text.insert(tk.END, "🛑 Stopping LLMdiver daemon...\n")
        success, stdout, stderr = self.run_command("./start_llmdiver.sh stop")
        
        if success:
            self.log_text.insert(tk.END, "✅ Daemon stopped successfully\n")
        else:
            self.log_text.insert(tk.END, f"❌ Failed to stop daemon: {stderr}\n")
            
        self.check_status()
        self.auto_scroll()
        
    def restart_daemon(self):
        """Restart the daemon"""
        self.log_text.insert(tk.END, "🔄 Restarting LLMdiver daemon...\n")
        success, stdout, stderr = self.run_command("./start_llmdiver.sh restart")
        
        if success:
            self.log_text.insert(tk.END, "✅ Daemon restarted successfully\n")
        else:
            self.log_text.insert(tk.END, f"❌ Failed to restart daemon: {stderr}\n")
            
        self.check_status()
        self.auto_scroll()
        
    def pause_daemon(self):
        """Pause the daemon (send SIGSTOP)"""
        if not self.daemon_running:
            return
            
        try:
            with open("llmdiver.pid", "r") as f:
                pid = f.read().strip()
            
            success, stdout, stderr = self.run_command(f"kill -STOP {pid}")
            if success:
                self.log_text.insert(tk.END, f"⏸️ Daemon paused (PID: {pid})\n")
                self.pause_btn.config(text="▶️ Resume", command=self.resume_daemon)
            else:
                self.log_text.insert(tk.END, f"❌ Failed to pause daemon: {stderr}\n")
                
        except Exception as e:
            self.log_text.insert(tk.END, f"❌ Error pausing daemon: {e}\n")
            
        self.auto_scroll()
        
    def resume_daemon(self):
        """Resume the daemon (send SIGCONT)"""
        try:
            with open("llmdiver.pid", "r") as f:
                pid = f.read().strip()
            
            success, stdout, stderr = self.run_command(f"kill -CONT {pid}")
            if success:
                self.log_text.insert(tk.END, f"▶️ Daemon resumed (PID: {pid})\n")
                self.pause_btn.config(text="⏸️ Pause", command=self.pause_daemon)
            else:
                self.log_text.insert(tk.END, f"❌ Failed to resume daemon: {stderr}\n")
                
        except Exception as e:
            self.log_text.insert(tk.END, f"❌ Error resuming daemon: {e}\n")
            
        self.auto_scroll()
        
    def update_projects_list(self):
        """Update the projects list"""
        try:
            with open("config/llmdiver.json", "r") as f:
                config = json.load(f)
                
            # Clear existing items
            for item in self.projects_tree.get_children():
                self.projects_tree.delete(item)
                
            # Add projects
            repositories = config.get("repositories", [])
            for repo in repositories:
                name = repo.get("name", "Unknown")
                path = repo.get("path", "Unknown")
                auto_commit = "✅" if repo.get("auto_commit", False) else "❌"
                discovered = " 🔍" if repo.get("discovered", False) else ""
                
                self.projects_tree.insert("", tk.END, text=f"{name}{discovered}", 
                                        values=(path, auto_commit))
                                        
        except Exception as e:
            print(f"Error loading projects: {e}")
            
    def start_log_monitoring(self):
        """Start monitoring logs in a separate thread"""
        if self.log_thread and self.log_thread.is_alive():
            return
            
        self.stop_log_thread = False
        self.log_thread = threading.Thread(target=self.monitor_logs, daemon=True)
        self.log_thread.start()
        
        # Start processing log queue
        self.process_log_queue()
        
    def monitor_logs(self):
        """Monitor log file for changes"""
        log_file = "llmdiver_daemon.log"
        
        if not os.path.exists(log_file):
            return
            
        try:
            with open(log_file, "r") as f:
                # Go to end of file
                f.seek(0, 2)
                
                while not self.stop_log_thread:
                    line = f.readline()
                    if line:
                        self.log_queue.put(line.strip())
                    else:
                        time.sleep(0.1)
                        
        except Exception as e:
            self.log_queue.put(f"❌ Error reading log file: {e}")
            
    def process_log_queue(self):
        """Process log messages from the queue"""
        try:
            while True:
                line = self.log_queue.get_nowait()
                self.log_text.insert(tk.END, f"{line}\n")
                
                # Limit log size
                if int(self.log_text.index('end-1c').split('.')[0]) > 1000:
                    self.log_text.delete('1.0', '100.0')
                    
                if self.auto_scroll_var.get():
                    self.log_text.see(tk.END)
                    
        except queue.Empty:
            pass
            
        # Schedule next check
        self.root.after(100, self.process_log_queue)
        
    def auto_scroll(self):
        """Auto scroll to bottom if enabled"""
        if self.auto_scroll_var.get():
            self.log_text.see(tk.END)
            
    def clear_logs(self):
        """Clear the log display"""
        self.log_text.delete('1.0', tk.END)
        
    def on_closing(self):
        """Handle window closing"""
        self.stop_log_thread = True
        self.root.destroy()

def main():
    # Check if we're in the right directory
    if not os.path.exists("start_llmdiver.sh"):
        messagebox.showerror("Error", "Please run this GUI from the LLMdiver directory!")
        return
        
    root = tk.Tk()
    app = LLMdiverGUI(root)
    
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()