from os import listdir
from os.path import isfile, join
from datetime import timedelta, datetime
import os, shutil, pathlib, logging, time
from notifications import Notification

folder_names_dict = {
    "Audio": {'aif', 'cda', 'mid', 'midi', 'mp3', 'mpa', 'ogg', 'wav', 'wma', 'flac', 'aac'},
    "Compressed": {'7z', 'deb', 'pkg', 'rar', 'rpm', 'tar.gz', 'z', 'zip', 'tar', 'gz'},
    'Code': {'js', 'jsp', 'html', 'ipynb', 'py', 'java', 'css', 'cpp', 'json', 'xml'},
    'Documents': {'ppt', 'pptx', 'pdf', 'xls', 'xlsx', 'doc', 'docx', 'txt', 'tex', 'epub', 'csv'},
    'Images': {'bmp', 'gif', 'ico', 'jpeg', 'jpg', 'png', 'jfif', 'svg', 'tif', 'tiff', 'raw', 'heif'},
    'Installers': {'dmg', 'app', 'exe', 'bat', 'cmd', 'msi'},
    'Softwares': {'apk', 'bat', 'bin', 'exe', 'jar', 'msi', 'py', 'drawio', 'run', 'com', 'sys', 'dll'},
    'Videos': {'3gp', 'avi', 'flv', 'h264', 'mkv', 'mov', 'mp4', 'mpg', 'mpeg', 'wmv', 'svi'},
    'Others': {'NONE'}
}

notification = Notification()

# Threshold for files which are considered as redundant
time_delta = timedelta(days=365)

def get_download_path():
    """Retrieves the full path to the Downloads folder on the client machine."""
    return pathlib.Path.home() / "Downloads"


def extract_files(downloads_path, folder_names):
    """Get all the visible files from the downloads folder."""
    files = []
    # Gets all files from Downloads except the hidden files
    for file in listdir(downloads_path):
        if isfile(join(download_path, file)) and not file.startswith('.'):
            files.append(file)

    file_type_list = []

    # Gets the file types from the dictionary folder_names
    for folder in folder_names_dict:
        filetypes = folder_names_dict[folder]
        for i in range(0, len(filetypes)):
            file_type_list.append(list(filetypes)[i])

    # Get the new folder names from the dictionary
    folder_names = list(folder_names.keys())

    # Make directories for new folders if they do not already exist
    for name in folder_names:
        path = str(downloads_path) + '/' + name + '/'
        if os.path.exists(os.path.dirname(path)):
            continue
        else:
            os.mkdir(path)

    return files


def move_files(download_path, files):
    """Moves files from the current Downloads folder to the respective folders based on extension.

    Args:
        download_path (str): Full path of Downloads folder
        files (list[str]): List containing names of all files currently in Downloads folder
    """
    found = False
    for file in files:
        # Find extension of source file
        src_path = str(download_path) + '/' + file
        extension = pathlib.Path(src_path).suffix

        # Remove the dot
        file_type = extension.split('.')[1]
        for folder_name, extensions in folder_names_dict.items():
            # Get value from dictionary as it is returned as a set
            for extension in extensions:
                if file_type == extension:
                    dest_path = str(download_path) + '/' + folder_name + '/' + file
                    found = True
                    # Moves file to correct folder
                    shutil.move(src_path, dest_path)
                    break
                else:
                    continue

        if not found:
            dest_path = str(download_path) + '/Others/' + file
            shutil.move(src_path, dest_path)


def delete_files(files_to_delete):
    """Delete expired files after request from user.

    Args:
        files_to_delete (list[str]): List of filepaths which need to be deleted.
    """
    for file in files_to_delete:
        print(f"file {file} is being deleted.")
        os.remove(file)


def calculate_unused_files(download_path, files):
    wasted_storage = 0
    files_to_delete = []
    size = 0
    for file in files:
        expired, days = check_file_date_modified(file, download_path)
        filepath = convert_path_to_string_path(download_path, file)
        if expired:
            size = os.path.getsize(filepath)
            files_to_delete.append(filepath)
            wasted_storage += size

    unit = "bytes"
    if 100 < wasted_storage < 1000000:
        # Convert to KB
        wasted_storage = round(wasted_storage / 1000, 2)
        unit = "KB"
    elif wasted_storage >= 1000000:
        # Convert to MB
        wasted_storage = round(wasted_storage / 1000000, 2)
        unit = "MB"
    elif wasted_storage >= 1000000000:
        # Convert to GB
        wasted_storage = round(wasted_storage / 1000000000, 2)
        unit = "GB"

    if wasted_storage > 0:
        files_deleted = notification.create_notification(f"There are {wasted_storage} {unit} of files in Downloads that haven't been opened for {days} days. Delete unused files.",
                                                True)
        if files_deleted is True:
            delete_files(files_to_delete)
            notification.create_notification(f"We have cleaned up the files and saved {wasted_storage} {unit} in your Downloads folder!", False)
        else:
            notification.create_notification(f"We have cleaned up the files in your Downloads folder!", False)
    else:
        notification.create_notification(f"We have cleaned up the files in your Downloads folder!", False)


def convert_path_to_string_path(download_path, file):
    """Converts path to string

    Args:
        download_path (path): Full path to Downloads folder
        file (str): Name of file

    Returns:
        str: Path of file in Downloads folder
    """
    if file != "":
        return str(download_path) + '/' + file
    else:
        return str(download_path)


def check_file_date_modified(file, download_path):
    """Checks the last date modified of a file and adds to recycle bin."""
    today = datetime.today()
    filepath = convert_path_to_string_path(download_path, file)
    last_date_modified = os.path.getmtime(filepath)
    expiration_date = today - time_delta

    # Convert time (float) from epoch to str time using Time module
    last_date_modified = time.ctime(last_date_modified)
    # Use datetime method to convert str time into datetime object
    format_string = "%a %b %d %H:%M:%S %Y"
    datetime_last_date_modified = datetime.strptime(last_date_modified, format_string)

    to_delete = False
    if datetime_last_date_modified < expiration_date:
        to_delete = True

    return to_delete, 365


def delete_unused_folders(download_path):
    """Deletes unused dynamically generated folders in the Downloads directory.

    Args:
        download_path (str): Full path of Downloads folder
    """
    folder_names = list(folder_names_dict.keys())

    returned_files = []
    for folder in folder_names:
        directory = str(download_path) + '/' + folder
        returned_files = os.listdir(directory)
        if len(returned_files) == 0:
            try:
                os.rmdir(directory)
            except FileNotFoundError:
                logging.debug("Directory could not be found!")
            except OSError:
                logging.debug("Directory was not empty!")
        else:
            continue


if __name__ == "__main__":
    download_path = get_download_path()
    str_download_path = convert_path_to_string_path(download_path, "")
    files = extract_files(download_path, folder_names_dict)
    calculate_unused_files(download_path, files)
    updated_files = extract_files(download_path, folder_names_dict)
    move_files(str_download_path, updated_files)
    delete_unused_folders(str_download_path)
