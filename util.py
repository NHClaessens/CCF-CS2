import os

def get_files_with_extension(path, extension):
    if not extension.startswith('.'):
        extension = "." + extension

    files = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(extension):
                files.append(os.path.normpath(os.path.join(root, file)))
    
    return files

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def wait_for_after_content(driver, element_locator, expected_content, timeout=10):
    # Wait for the element to be present in the DOM
    element = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located(element_locator)
    )
    
    # Wait until the ::after content matches the expected value
    WebDriverWait(driver, timeout).until(
        lambda driver: driver.execute_script("""
            var element = arguments[0];
            var styles = window.getComputedStyle(element, '::after');
            return styles.getPropertyValue('content') === arguments[1];
        """, element, expected_content)
    )

from time import sleep
def monitor_folder_for_changes(folder_path):
    # Ensure the folder exists
    if not os.path.exists(folder_path):
        print("Folder not found")
        return

    # Dictionary to store the file size for each file in the folder
    file_sizes = {}

    # Initialize the file_sizes dictionary with the current sizes of files
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        if os.path.isfile(file_path):  # Only monitor files, not subdirectories
            file_sizes[file_path] = os.path.getsize(file_path)

    # Monitor files in the folder
    while True:
        all_files_stable = True  # Flag to track if all files have stabilized
        for file_path in file_sizes.keys():
            if not os.path.exists(file_path):
                continue
            size1 = os.path.getsize(file_path)
            sleep(1)
            if not os.path.exists(file_path):
                continue
            size2 = os.path.getsize(file_path)

            # If the size of the file has not changed, it's considered stable
            if size1 != size2:
                all_files_stable = False

        # Exit the loop when all files are stable
        if all_files_stable:
            break
