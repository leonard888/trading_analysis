import subprocess
import webbrowser
import os
import sys
import time
import tkinter as tk
from tkinter import messagebox
import threading

# Configuration
BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
FRONTEND_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend', 'index.html')
ICON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend', 'favicon.ico') # If exists

class TradingLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Trading Terminal Launcher")
        self.root.geometry("300x150")
        self.process = None

        # Label
        self.status_label = tk.Label(root, text="Starting Backend...", font=("Arial", 12))
        self.status_label.pack(pady=20)

        # Buttons
        self.btn_frame = tk.Frame(root)
        self.btn_frame.pack(pady=10)

        self.browser_btn = tk.Button(self.btn_frame, text="Open Browser", command=self.open_browser, state=tk.DISABLED)
        self.browser_btn.pack(side=tk.LEFT, padx=5)

        self.quit_btn = tk.Button(self.btn_frame, text="Stop & Quit", command=self.quit_app, bg="#ffdddd")
        self.quit_btn.pack(side=tk.LEFT, padx=5)

        # Start backend in background thread
        self.start_thread = threading.Thread(target=self.start_backend)
        self.start_thread.daemon = True
        self.start_thread.start()

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.quit_app)


    def start_backend(self):
        try:
            # Command to run: python main.py
            # We assume python is in path. If bundled, we might need handling.
            cmd = [sys.executable, "main.py"]
            
            # Use a log file to prevent pipe deadlock and allow debugging
            self.log_file = open("backend.log", "w")
            
            self.process = subprocess.Popen(
                cmd,
                cwd=BACKEND_DIR,
                stdout=self.log_file,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )

            # Wait a bit for server to spin up
            time.sleep(3)
            
            self.root.after(0, self.on_backend_started)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to start backend:\n{str(e)}"))

    def on_backend_started(self):
        self.status_label.config(text="Backend Running • Port 8000")
        self.browser_btn.config(state=tk.NORMAL)
        self.open_browser()

    def open_browser(self):
        webbrowser.open('http://localhost:8000')

    def quit_app(self):
        if self.process:
            self.status_label.config(text="Stopping Backend...")
            self.process.terminate()
            self.process.wait()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = TradingLauncher(root)
    root.mainloop()
