# Broken Video File Detector

The Broken Video File Detector is a Python script that helps you identify and manage broken video files within a directory. It provides a user-friendly graphical interface for selecting a directory, scanning for broken video files, and performing various actions on them, such as deletion.

## Features

Easily browse and select a directory for scanning.

Perform a recursive scan to find broken video files within subdirectories.

Display a list of broken video files found during the scan.

Delete individual broken video files.

Delete all broken video files at once.

Rescan the directory to find newly broken files.

## Requirements
Python 3.x
 
Tkinter (included with most Python installations)

moviepy library (pip install moviepy)

joblib library (pip install joblib)

## Usage

Run the script using Python: python broken_video_detector.py

Click the "Browse" button to select a directory for scanning.

Toggle the "Recursive" button if you want to include subdirectories in the scan.

Click the "Scan" button to initiate the scanning process. The listbox will display any broken video files found.

Select one or more files in the listbox and click the "Delete Selected" button to remove them.

To delete all broken video files in one go, click the "Delete All" button.

Click the "Scan" button to re-scan the current directory and find newly broken files.

Click the "Cache" button to initiate the scanning process without cache.

## Note

***Be cautious when deleting files, as they cannot be recovered once deleted.***
***Some video files may take longer to scan, depending on their size.***

## License

This project is licensed under the MIT License.

## Acknowledgments

    The Broken Video File Detector uses the moviepy library for video file analysis.

Contributing

Feel free to open an issue or create a pull request to contribute to this project.
Questions or Issues

If you have any questions or encounter issues, please open an issue.
