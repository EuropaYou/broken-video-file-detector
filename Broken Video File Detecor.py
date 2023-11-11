import time
import os
import mimetypes
import tkinter as tk
from tkinter import filedialog, messagebox
from moviepy.editor import VideoFileClip
import joblib
import asyncio
import threading
import logging


recursive_search = False
cache_search = True
current_directory = None
cache_file = "broken_video_files_cache.pkl"
logging.basicConfig(filename='broken_video_detector.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

task_queue = asyncio.Queue()

dark_mode = True
LIGHT_MODE_BG = "#FFFFFF"
LIGHT_MODE_FG = "#000000"
DARK_MODE_BG = "#242424"
DARK_MODE_FG = "#FFFFFF"


def toggle_dark_light_mode():
    global dark_mode
    dark_mode = not dark_mode
    logging.info(f"Toggled dark_light_button: {dark_mode}")
    bg_color = DARK_MODE_BG if dark_mode else LIGHT_MODE_BG
    fg_color = DARK_MODE_FG if dark_mode else LIGHT_MODE_FG

    root.config(bg=bg_color)
    label.config(bg=bg_color, fg=fg_color)
    frame.config(bg=bg_color)
    browse_button.config(bg=bg_color, fg=fg_color)
    rescan_button.config(bg=bg_color, fg=fg_color)
    recursive_button.config(bg=bg_color, fg=fg_color)
    cache_button.config(bg=bg_color, fg=fg_color)
    frame3.config(bg=bg_color)
    listbox.config(bg=bg_color, fg=fg_color)
    yscrollbar.config(bg=bg_color)
    xscrollbar.config(bg=bg_color)
    frame1.config(bg=bg_color)
    delete_button.config(bg=bg_color, fg=fg_color)
    delete_all_button.config(bg=bg_color, fg=fg_color)
    status_label.config(bg=bg_color, fg="blue")
    dark_light_button.config(bg=bg_color, fg=fg_color)

    
def is_video_file(file_path):
    mime_type, _ = mimetypes.guess_type(file_path)
    video_mime_types = [
        'video/mp4',
        'video/quicktime',
        'video/x-msvideo',
        'video/x-ms-wmv',
        'video/x-flv',
        'video/webm',
        'video/x-matroska',
        'video/3gpp',
        'video/mpeg',
        'video/x-mpeg',
    ]

    return mime_type in video_mime_types
    
    
async def is_video_file_broken(file_path):
    update_status_label(f"Scanning directory... Checking if video is broken: \n{os.path.basename(file_path).split('/')[-1]}")
    logging.info(f"Scanning directory... Checking if video is broken: \n{os.path.basename(file_path).split('/')[-1]}")
    root.update_idletasks()
    try:
        video = VideoFileClip(file_path)
        video.close()
        return False
    except Exception as e:
        return True
        
        
async def background_task():
    while True:
        task = await task_queue.get()
        await task


def browse_directory():
    asyncio.run_coroutine_threadsafe(scan_directory(), asyncio.get_event_loop())
    logging.info("Browsing directory.")
    
    
async def scan_directory():
    global current_directory
    directory_path = filedialog.askdirectory()
    if directory_path:
        current_directory = directory_path    
        logging.info(f"Selected directory: {current_directory}")


def toggle_recursive_search():
    global recursive_search
    recursive_search = not recursive_search
    recursive_button.config(text="Recursive: " + ("On" if recursive_search else "Off"))
    logging.info("Toggled Recursive Search " + ("On" if recursive_search else "Off"))

def toggle_cache_search():
    global cache_search
    cache_search = not cache_search
    cache_button.config(text="Cache: " + ("On" if cache_search else "Off"))
    logging.info("Toggled Cache " + + ("On" if cache_search else "Off"))


def find_broken_video_files(directory, recursive, cache_search):
    logging.info(f"Finding broken video files in directory: {directory}")
    
    if os.path.exists(cache_file):
        if cache_search:
            cache = joblib.load(cache_file)
            if cache['directory'] == directory and not re_scan:
                return cache['broken_files']
    else:
        logging.error(f"Cache file doesn't exist! {cache_file}")

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

    cache = {'directory': directory, 'broken_files': broken_files}
    joblib.dump(cache, cache_file)
    logging.info(f"Dumped broken video files in cache file: {cache_file}")

    return broken_files


def delete_selected_file(arg):
    selected_index = listbox.curselection()
    logging.info("User is trying to delete a file.")
    if selected_index:
        selected_index = int(selected_index[0])
        selected_file = listbox.get(selected_index)

        result = messagebox.askquestion("Confirm Deletion", f"Are you sure you want to delete '{selected_file}'?")
        logging.info(f"A messagebox sent to user to confirm deletion of {selected_file}.")
        if result == "yes":
            try:
                update_status_label(f"Deleting '{selected_file}'...")
                logging.info(f"Deleting '{selected_file}'...")
                os.remove(selected_file)
                messagebox.showinfo("File Deleted", f"'{selected_file}' has been deleted.")
                logging.info("File Deleted", f"'{selected_file}' has been deleted.")
                listbox.delete(selected_index)
                update_status_label("Deletion complete.")
                logging.info("Deletion complete.")
            except Exception as e:
                messagebox.showerror("Error", f"Unable to delete '{selected_file}': {e}")
                logging.error("Error", f"Unable to delete '{selected_file}': {e}")
                update_status_label("Deletion failed.")
        else:
            messagebox.showinfo("Deletion Canceled", f"Deletion of '{selected_file}' canceled.")
            logging.info("Deletion Canceled", f"Deletion of '{selected_file}' canceled.")
    else:
        messagebox.showwarning("No File Selected", "Please select a file to delete.")
        logging.warning("No File Selected", "Please select a file to delete.")


def delete_all_files(arg):
    if listbox.size() == 0:
        messagebox.showwarning("No File Selected", f"There is no entries in result tab")
        logging.warning("No File Selected", f"There is no entries in result tab")
        return
    
    result = messagebox.askquestion("Confirm Deletion", f"Are you sure you want to delete all files?")
    logging.info(f"A messagebox sent to user to confirm deletion of all files.")
    if result == "yes":
        all_indices = listbox.get(0, tk.END)
        for index in all_indices:
                try:
                    update_status_label(f"Deleting '{index}'...")
                    logging.info(f"Deleting '{index}'...")
                    os.remove(index)
                    update_status_label(f"'{index}' has been deleted.")
                    update_status_label("Deletion complete.")
                    logging.info("File Deleted", f"'{index}' has been deleted.")
                    logging.info("Deletion complete.")
                except Exception as e:
                    messagebox.showerror("Error", f"Unable to delete '{index}': {e}")
                    logging.error("Error", f"Unable to delete '{index}': {e}")
                    update_status_label("Deletion failed.")
                    logging.error("Deletion failed.")
        listbox.delete(0, tk.END)
    else:
        messagebox.showinfo("Deletion Canceled", f"Deletion of files canceled.")
        logging.info("Deletion Canceled", f"Deletion of files canceled.")
    
    
def rescan_directory():
    global re_scan
    re_scan = True
    if current_directory:
        update_status_label("Scanning directory...")
        logging.info("Scanning directory...")
        broken_files = find_broken_video_files(current_directory, recursive_search, cache_search)
        update_listbox(broken_files)
        update_status_label("Scan complete.")
        logging.info("Scan complete.")


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
          

loop = asyncio.get_event_loop()
thread = threading.Thread(target=loop.run_forever)
thread.start()
loop.create_task(background_task())

root = tk.Tk()
root.config(bg="#242424")
root.geometry("400x460")
root.title("Broken Video File Detector")
root.bind("<Delete>", delete_selected_file)
root.bind("<Control-Delete>", delete_all_files)

label = tk.Label(root, text="Select a directory to check for broken video files:", bg="#26242f", fg="white")
label.pack()

frame = tk.Frame(root, bg="#242424")
frame.pack()

browse_button = tk.Button(frame, text="Browse", command=lambda: browse_directory(), bg="#242424", fg="white")
browse_button.pack(side=tk.LEFT)

rescan_button = tk.Button(frame, text="Scan", command=lambda: rescan_directory(), bg="#242424", fg="white")
rescan_button.pack(side=tk.LEFT)

recursive_button = tk.Button(frame, text="Recursive: Off", command=toggle_recursive_search, bg="#242424", fg="white")
recursive_button.pack(side=tk.LEFT)

cache_button = tk.Button(frame, text="Cache: On", command=toggle_cache_search, bg="#242424", fg="white")
cache_button.pack(side=tk.LEFT)

frame3 = tk.Frame(root)
frame3.pack(fill=tk.BOTH, expand=1)

listbox = tk.Listbox(frame3, bg="#26242f", fg="white")
listbox.pack(padx=1, pady=1, expand=True, fill=tk.BOTH, side =tk.LEFT)

yscrollbar = tk.Scrollbar(frame3, orient="vertical", command=listbox.yview)
yscrollbar.pack(side=tk.RIGHT, fill="both")
xscrollbar = tk.Scrollbar(root, orient="horizontal", command=listbox.xview)
xscrollbar.pack(fill="both")

frame1 = tk.Frame(root, bg="#242424")
frame1.pack()

delete_button = tk.Button(frame1, text="Delete Selected", command=delete_selected_file, bg="#242424", fg="white")
delete_button.pack(side=tk.LEFT)

delete_all_button = tk.Button(frame1, text="Delete All", command=delete_all_files, bg="#242424", fg="white")
delete_all_button.pack(side=tk.LEFT)

status_label = tk.Label(root, text="Idle", fg="blue", bg="#242424")
status_label.pack()

dark_light_button = tk.Button(frame, text="Dark/Light Mode", command=toggle_dark_light_mode, bg="#242424", fg="white")
dark_light_button.pack(side=tk.LEFT)


re_scan = False
root.protocol("WM_DELETE_WINDOW", exit_program)
root.mainloop()
