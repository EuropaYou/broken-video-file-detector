import os
import mimetypes
import tkinter as tk
from tkinter import filedialog, messagebox
import moviepy
import joblib
import asyncio
import threading
import logging
import requests
import sys
import datetime


recursive_search = False
cache_search = True
current_directory = None
cache_file = "broken_video_files_cache.pkl"
logging.basicConfig(
    filename="broken_video_detector.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def log(message, level="info"):
    level_color_code = ""
    color_code_reset = "\033[00m"

    if level == "info":
        level_color_code = "\033[90m"
        logging.info(message)
    elif level == "warning":
        level_color_code = "\033[93m"
        logging.warning(message)
    elif level == "error":
        level_color_code = "\033[91m"
        logging.error(message)
    elif level == "critical":
        level_color_code = "\033[91m"
        logging.critical(message)
    print(
        f"\033[92m{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {level_color_code}{level.upper()}{color_code_reset} {message}"
    )


log(sys.version)

if moviepy.__version__ < "2.0.0":
    from moviepy.editor import VideoFileClip

    log("\nPlease update your moviepy version:\n\tpip install -U moviepy\n", "warning")

else:
    from moviepy import VideoFileClip

task_queue = asyncio.Queue()

dark_mode = True
LIGHT_MODE_BG = "#FFFFFF"
DARK_MODE_BG = "#2b2b2b"
LIGHT_MODE_BUTTON_BG = "#898989"
LIGHT_MODE_LISTBOX_BG = "#3d3d3d"
DARK_MODE_LISTBOX_BG = "#3d3d3d"
LIGHT_MODE_SCROLLBAR_BG = "#717171"
DARK_MODE_SCROLLBAR_BG = "#717171"
LIGHT_MODE_FG = "black"
DARK_MODE_FG = "#FFFFFF"
BUTTON_BG = "#1c72b0"
BVFD_VERSION = "v0.5.0-beta"


def check_for_updates(current_version):
    repo_url = (
        "https://api.github.com/repos/EuropaYou/broken-video-file-detector/releases"
    )

    try:
        response = requests.get(repo_url)
        data = response.json()
        latest_version_name: str = data[0]["name"]
        latest_version_body: str = data[0]["body"]

        if latest_version_name.lower() != current_version.lower():
            log(
                "There is newer version (%s) available. (Current version is: %s)\nRelease notes are:\n\n%s"
                % (latest_version_name, current_version, latest_version_body)
            )
            return True
        else:
            return False
    except Exception as e:
        log(f"An error occurred while checking for updates: {e}", "error")
        return False


def toggle_dark_light_mode():
    global dark_mode
    dark_mode = not dark_mode
    log(f"Toggled dark mode {dark_mode}")
    bg_color = DARK_MODE_BG if dark_mode else LIGHT_MODE_BG
    bg_button_color = BUTTON_BG if dark_mode else BUTTON_BG
    bg_listbox_color = DARK_MODE_LISTBOX_BG if dark_mode else LIGHT_MODE_BG
    bg_scrollbar_color = DARK_MODE_LISTBOX_BG if dark_mode else LIGHT_MODE_BG
    fg_color = DARK_MODE_FG if dark_mode else LIGHT_MODE_FG
    label_color = "white" if dark_mode else "black"
    label_color_r = "white"

    root.config(bg=bg_color)
    label.config(bg=bg_color, fg=fg_color)
    frame.config(bg=bg_color)
    browse_button.config(bg=bg_button_color, fg=label_color_r)
    rescan_button.config(bg=bg_button_color, fg=label_color_r)
    recursive_button.config(bg=bg_button_color, fg=label_color_r)
    cache_button.config(bg=bg_button_color, fg=label_color_r)
    frame3.config(bg=bg_color)
    listbox.config(bg=bg_listbox_color, fg=label_color)
    dark_light_button.config(bg=bg_button_color, fg=label_color_r)
    yscrollbar.config(bg=bg_scrollbar_color)
    xscrollbar.config(bg=bg_scrollbar_color)
    frame1.config(bg=bg_color)
    delete_button.config(bg=bg_button_color, fg=label_color_r)
    delete_all_button.config(bg=bg_button_color, fg=label_color_r)
    status_label.config(bg=bg_color, fg=label_color)


def is_video_file(file_path):
    mime_type, _ = mimetypes.guess_type(file_path)
    video_mime_types = [
        "video/mp4",
        "video/quicktime",
        "video/x-msvideo",
        "video/x-ms-wmv",
        "video/x-flv",
        "video/webm",
        "video/x-matroska",
        "video/3gpp",
        "video/mpeg",
        "video/x-mpeg",
    ]

    return mime_type in video_mime_types


async def is_video_file_broken(file_path):
    string = f"Scanning directory... Checking if video is broken: \n{os.path.basename(file_path).split('/')[-1]}"

    update_status_label(string)
    log(string)
    root.update_idletasks()
    try:
        video = VideoFileClip(file_path)
        video.close()
        return False
    except Exception as e:
        log(
            f"An error occurred while checking if video file broken or not: {e}",
            "error",
        )
        return True


async def background_task():
    while True:
        task = await task_queue.get()
        await task


def browse_directory():
    log("Browsing directory.")
    asyncio.run_coroutine_threadsafe(scan_directory(), asyncio.get_event_loop())


async def scan_directory():
    global current_directory
    directory_path = filedialog.askdirectory()
    if directory_path:
        current_directory = directory_path
        log(f"Selected directory: {current_directory}")


def toggle_recursive_search():
    global recursive_search
    recursive_search = not recursive_search
    recursive_button.config(text="Recursive: " + ("On" if recursive_search else "Off"))
    log("Toggled Recursive Search " + ("On" if recursive_search else "Off"))


def toggle_cache_search():
    global cache_search
    cache_search = not cache_search
    cache_button.config(text="Cache: " + ("On" if cache_search else "Off"))
    log("Toggled Cache " + ("On" if cache_search else "Off"))


def find_broken_video_files(directory, recursive, cache_search):
    log(f"Finding broken video files in directory: {directory}")

    if os.path.exists(cache_file) and cache_search:
        cache = joblib.load(cache_file)
        if cache["directory"] == directory and not re_scan:
            return cache["broken_files"]
    else:
        log(f"Cache file doesn't exist! {cache_file}", "warning")

    broken_files = []
    if recursive:
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                if is_video_file(file_path):
                    if is_video_file_broken(file_path):
                        broken_files.append(file_path)
    else:
        for file in os.listdir(directory):
            file_path = os.path.join(directory, file)
            if os.path.isfile(file_path) and is_video_file(file_path):
                if is_video_file_broken(file_path):
                    broken_files.append(file_path)

    cache = {"directory": directory, "broken_files": broken_files}
    joblib.dump(cache, cache_file)
    log(f"Dumped broken video files in cache file: {cache_file}")

    return broken_files


def delete_selected_file():
    selected_index = listbox.curselection()
    log("User is trying to delete a file.")
    if selected_index:
        selected_index = int(selected_index[0])
        selected_file = listbox.get(selected_index)

        result = messagebox.askquestion(
            "Confirm Deletion", f"Are you sure you want to delete '{selected_file}'?"
        )
        log(f"A messagebox sent to user to confirm deletion of {selected_file}.")
        if result == "yes":
            try:
                update_status_label(f"Deleting '{selected_file}'...")
                log(f"Deleting '{selected_file}'...")
                os.remove(selected_file)
                messagebox.showinfo(
                    "File Deleted", f"'{selected_file}' has been deleted."
                )
                log("File Deleted", f"'{selected_file}' has been deleted.")
                listbox.delete(selected_index)
                update_status_label("Deletion complete.")
                log("Deletion complete.")
            except Exception as e:
                messagebox.showerror(
                    "Error", f"Unable to delete '{selected_file}': {e}"
                )
                log(f"Unable to delete '{selected_file}': {e}", "error")
                update_status_label("Deletion failed.")
        else:
            messagebox.showinfo(
                "Deletion Canceled", f"Deletion of '{selected_file}' canceled."
            )
            log("Deletion Canceled", f"Deletion of '{selected_file}' canceled.")
    else:
        messagebox.showwarning("No File Selected", "Please select a file to delete.")
        log("No File Selected Please select a file to delete.", "warning")


def delete_all_files():
    if listbox.size() == 0:
        messagebox.showwarning("No File Selected", "There are no entries in result tab")
        log("No File Selected There are no entries in result tab", "warning")
        return

    result = messagebox.askquestion(
        "Confirm Deletion", "Are you sure you want to delete all files?"
    )
    log("A messagebox sent to user to confirm deletion of all files.")
    if result == "yes":
        log("User said yes. Deleting...")
        all_indices = listbox.get(0, tk.END)
        for index in all_indices:
            try:
                update_status_label(f"Deleting '{index}'...")
                log(f"Deleting '{index}'...")
                os.remove(index)
                update_status_label(f"'{index}' has been deleted.")
                update_status_label("Deletion complete.")
                log("File Deleted", f"'{index}' has been deleted.")
                log("Deletion complete.")
            except Exception as e:
                messagebox.showerror("Error", f"Unable to delete file '{index}': {e}")
                log(f"Error Unable to delete file '{index}': {e}", "error")
                update_status_label("Deletion failed.")
                log("Deletion failed.", "error")
        listbox.delete(0, tk.END)
    else:
        messagebox.showinfo("Deletion Canceled", "Deletion of files canceled.")
        log("Deletion Canceled Deletion of files canceled.")


def rescan_directory():
    global re_scan
    re_scan = True
    if current_directory:
        update_status_label("Scanning directory...")
        log("Scanning directory...")
        broken_files = find_broken_video_files(
            current_directory, recursive_search, cache_search
        )
        update_listbox(broken_files)
        update_status_label("Scan complete.")
        log("Scan complete.")


def update_status_label(text):
    status_label.config(text=text)


def update_listbox(broken_files):
    listbox.delete(0, tk.END)
    if broken_files:
        for file in broken_files:
            listbox.insert(tk.END, file.replace(current_directory, ""))
    else:
        listbox.insert(tk.END, "No broken video files found in the selected directory.")


def exit_program():
    root.destroy()
    loop.call_soon_threadsafe(loop.stop)
    thread.join()


check_for_updates(BVFD_VERSION)
loop = asyncio.get_event_loop()
thread = threading.Thread(target=loop.run_forever)
thread.start()
loop.create_task(background_task())


root = tk.Tk()
root.config(bg="#2b2b2b")
root.geometry("560x420")
root.title("Broken Video File Detector")
root.bind("<Delete>", delete_selected_file)
root.bind("<Control-Delete>", delete_all_files)

label = tk.Label(
    root,
    text="Select a directory to check for broken video files:",
    bg="#2b2b2b",
    fg="white",
    font="Helvetica 10",
    padx=10,
    pady=5,
)
label.pack()

frame = tk.Frame(root, bg="#2b2b2b")
frame.pack()

browse_button = tk.Button(
    frame, text="Browse", command=lambda: browse_directory(), bg="#1c72b0", fg="white"
)
browse_button.pack(side=tk.LEFT, padx=10, pady=5)

rescan_button = tk.Button(
    frame, text="Scan", command=lambda: rescan_directory(), bg="#1c72b0", fg="white"
)
rescan_button.pack(side=tk.LEFT, padx=10, pady=5)

recursive_button = tk.Button(
    frame,
    text="Recursive: Off",
    command=toggle_recursive_search,
    bg="#1c72b0",
    fg="white",
)
recursive_button.pack(side=tk.LEFT, padx=10, pady=5)

cache_button = tk.Button(
    frame, text="Cache: On", command=toggle_cache_search, bg="#1c72b0", fg="white"
)
cache_button.pack(side=tk.LEFT, padx=10, pady=5)

frame3 = tk.Frame(root)
frame3.pack(fill=tk.BOTH, expand=1)

listbox = tk.Listbox(frame3, bg="#3d3d3d", fg="white")
listbox.pack(padx=1, pady=1, expand=True, fill=tk.BOTH, side=tk.LEFT)

yscrollbar = tk.Scrollbar(
    frame3, orient="vertical", command=listbox.yview, bg="#717171"
)
yscrollbar.pack(side=tk.RIGHT, fill="both")
xscrollbar = tk.Scrollbar(
    root, orient="horizontal", command=listbox.xview, bg="#717171"
)
xscrollbar.pack(fill="both")

frame1 = tk.Frame(root, bg="#2b2b2b")
frame1.pack()

delete_button = tk.Button(
    frame1,
    text="Delete Selected",
    command=delete_selected_file,
    bg="#1c72b0",
    fg="white",
)
delete_button.pack(side=tk.LEFT, padx=10, pady=5)

delete_all_button = tk.Button(
    frame1, text="Delete All", command=delete_all_files, bg="#1c72b0", fg="white"
)
delete_all_button.pack(side=tk.LEFT, padx=10, pady=5)

status_label = tk.Label(
    root, text="Idle", fg="white", bg="#2b2b2b", font="Helvetica 10 bold"
)
status_label.pack()

dark_light_button = tk.Button(
    frame,
    text="Dark/Light Mode",
    command=toggle_dark_light_mode,
    bg="#1c72b0",
    fg="white",
)
dark_light_button.pack(side=tk.LEFT, padx=10, pady=5)

re_scan = False
root.protocol("WM_DELETE_WINDOW", exit_program)
root.mainloop()
