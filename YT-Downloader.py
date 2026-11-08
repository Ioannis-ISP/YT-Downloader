import re
import os
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from queue import Queue, Empty

print("Starting YT-Downloader...")

# Download location
folder = os.getcwd()

# Communication between background threads and GUI
messages = Queue()


# ---------------- DEPENDENCY INSTALLATION ----------------

def install_tools():
    tools = [
        ["winget", "install", "--id", "ffmpeg.ffmpeg", "-e",
         "--accept-package-agreements", "--accept-source-agreements"],
        ["winget", "install", "--id", "yt-dlp.yt-dlp", "-e",
         "--accept-package-agreements", "--accept-source-agreements"]
    ]

    for command in tools:
        messages.put(("log", f"Checking {command[3]}..."))

        try:
            subprocess.run(command, check=False)

        except FileNotFoundError:
            messages.put(("log", "Winget was not found."))
            messages.put(("dependencies_failed", None))
            return

    messages.put(("dependencies_ready", None))

# ---------------- DOWNLOAD FUNCTION ----------------

def download():
    url = url_entry.get().strip()
    choice = format_var.get()

    if not url:
        messagebox.showwarning("Missing URL", "Please enter a URL.")
        return

    if choice == "1080p":
        command = [
            "yt-dlp",
            "-P", folder,
            "-f", "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
            "--merge-output-format", "mp4",
            "--newline",
            url
        ]

    elif choice == "360p":
        command = [
            "yt-dlp",
            "-P", folder,
            "-f", "bestvideo[height<=360]+bestaudio/best[height<=360]",
            "--merge-output-format", "mp4",
            "--newline",
            url
        ]

    else:
        command = [
            "yt-dlp",
            "-P", folder,
            "-x",
            "--audio-format", "mp3",
            "--audio-quality", "0",
            "--newline",
            url
        ]

    download_button.config(state="disabled")
    status_var.set("Downloading...")

    def run_download():
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1
            )

            for line in process.stdout:
                messages.put(("log", line.rstrip()))

            process.wait()

            if process.returncode == 0:
                messages.put(("download_finished", None))
            else:
                messages.put(("download_failed", None))

        except FileNotFoundError as error:
            messages.put(("log", str(error)))
            messages.put(("download_failed", None))

    threading.Thread(target=run_download, daemon=True).start()


# ---------------- GUI ----------------

root = tk.Tk()
root.title("YT-Downloader")
root.geometry("600x500")
root.minsize(500, 400)

# Main container
main = ttk.Frame(root, padding=20)
main.pack(fill="both", expand=True)

# Title
ttk.Label(
    main,
    text="YT-Downloader",
    font=("Segoe UI", 22, "bold")
).pack(pady=(0, 5))

ttk.Label(
    main,
    text="Download videos and audio from YouTube"
).pack(pady=(0, 20))

# URL input
ttk.Label(main, text="YouTube URL:").pack(anchor="w")

url_entry = ttk.Entry(main, font=("Segoe UI", 11))
url_entry.pack(fill="x", pady=(5, 15))

# Format selection
ttk.Label(
    main,
    text="Select download format:"
).pack(anchor="w")

format_var = tk.StringVar(value="1080p")

formats = ttk.Frame(main)
formats.pack(fill="x", pady=10)

for name in ("1080p", "360p", "MP3"):
    ttk.Radiobutton(
        formats,
        text=name,
        variable=format_var,
        value=name
    ).pack(side="left", padx=(0, 20))

# Download button
download_button = ttk.Button(
    main,
    text="Download",
    command=download,
    state="disabled"
)
download_button.pack(fill="x", pady=10)

# Status
status_var = tk.StringVar(value="Installing/checking required tools...")
# Progress bar
progress_var = tk.DoubleVar(value=0)

progress_bar = ttk.Progressbar(
    main,
    variable=progress_var,
    maximum=100,
    mode="determinate"
)

progress_bar.pack(fill="x", pady=10)

progress_label = ttk.Label(main, text="0%")
progress_label.pack(anchor="e")

ttk.Label(
    main,
    textvariable=status_var
).pack(anchor="w", pady=5)

# Download location
ttk.Label(
    main,
    text=f"Download location: {folder}",
    wraplength=540
).pack(anchor="w", pady=5)

# Output log
ttk.Label(main, text="Output:").pack(anchor="w", pady=(10, 5))

log_frame = ttk.Frame(main)
log_frame.pack(fill="both", expand=True)

log_output = tk.Text(
    log_frame,
    height=10,
    wrap="word",
    state="disabled",
    font=("Consolas", 9)
)

scrollbar = ttk.Scrollbar(
    log_frame,
    command=log_output.yview
)

log_output.configure(yscrollcommand=scrollbar.set)

log_output.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")


# ---------------- MESSAGE HANDLER ----------------

def process_messages():
    try:
        while True:
            message, data = messages.get_nowait()

            if message == "log":
                log_output.config(state="normal")
                log_output.insert("end", str(data) + "\n")
                log_output.see("end")
                log_output.config(state="disabled")

            elif message == "dependencies_ready":
                status_var.set("Ready!")
                download_button.config(state="normal")

            elif message == "dependencies_failed":
                status_var.set("Dependency installation failed.")

            elif message == "download_finished":
                status_var.set("Download completed!")
                download_button.config(state="normal")

            elif message == "download_failed":
                status_var.set("Download failed.")
                download_button.config(state="normal")

    except Empty:
        pass

    root.after(100, process_messages)


# Start dependency installation in background
threading.Thread(target=install_tools, daemon=True).start()

# Start checking messages
root.after(100, process_messages)

root.mainloop()
