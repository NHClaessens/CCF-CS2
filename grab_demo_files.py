from email import header
import random
import shutil
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from seleniumbase import Driver
import os
from time import gmtime, strftime
import patoolib
import argparse
from requests import get
import subprocess
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select


team_url = "https://www.hltv.org/stats/teams/matches/9565/vitality?startDate=2024-12-13&endDate=2025-03-13&rankingFilter=Top20"

def wait():
    return
    sleep(random.randint(5, 15) / 10)

def get_rar_files(path):
    rar_files = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith('.rar'):
                rar_files.append(os.path.join(root, file))
    
    return rar_files

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
    print(f"::after content is now: '{expected_content}'")

def monitor_folder(folder_path):
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
            print(f"{file_path}: {size1}")
            sleep(1)
            if not os.path.exists(file_path):
                continue
            size2 = os.path.getsize(file_path)

            # If the size of the file has not changed, it's considered stable
            if size1 != size2:
                all_files_stable = False

        # Exit the loop when all files are stable
        if all_files_stable:
            print("All files have finished downloading.")
            break

def main(args):
    print("Starting web driver...")
    options = webdriver.ChromeOptions()
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    driver : webdriver.Chrome = Driver(uc=True, headless=False)

    driver.uc_open_with_reconnect(team_url, reconnect_time=6)

    print(driver.execute_script("return navigator.userAgent"))

    # Decline optional cookies
    wait()
    driver.find_element(By.ID, "CybotCookiebotDialogBodyButtonDecline").click()

    time_filter_element = Select(driver.find_element(By.CLASS_NAME, "stats-sub-navigation-simple-filter-time"))
    time_filter_element.select_by_visible_text("All time")

    matches_table = driver.find_element(By.TAG_NAME, "tbody")
    match_rows = matches_table.find_elements(By.TAG_NAME, "tr")

    grouped_matches = []
    current_group = []

    previous_color = None
    match_page_links = []
    for index, row in enumerate(match_rows):
        bg_color = row.value_of_css_property("background-color")


        if previous_color is None or bg_color == previous_color:
            # Continue current group
            current_group.append(row)
        else:
            # Start a new group and save the previous one
            grouped_matches.append(current_group)

            columns = current_group[0].find_elements(By.TAG_NAME, "td")
            date = columns[0].text
            opponent = columns[3].text
            match_page_link = current_group[0].find_element(By.TAG_NAME, "a").get_attribute("href")
            match_page_links.append(match_page_link)
            print(f"Match {len(match_page_links)}: {date} vs {opponent}, {len(current_group)} rounds: {match_page_link}")

            current_group = [row]

        previous_color = bg_color

        if len(match_page_links) >= args.count:
            break

    match_detail_links = []
    for index, link in enumerate(match_page_links):
        driver.uc_open_with_reconnect(link, reconnect_time=6)
        match_detail_link = driver.find_element(By.CLASS_NAME, "match-page-link").get_attribute("href")
        match_detail_links.append(match_detail_link)

    for index, link in enumerate(match_detail_links):
        driver.uc_open_with_reconnect(link, reconnect_time=6)
        download_button = driver.find_element(By.CLASS_NAME, "stream-box")
        print(f"{index}: download at: {download_button.get_attribute("data-demo-link")}")

        download_button.click()
        wait_for_after_content(driver, (By.CLASS_NAME, 'vod-loading-status'), '"Download starting..."')
        print("Wait for download to start")
        sleep(3)
        monitor_folder('./downloaded_files')


    # TODO: time is lower by 1 hour
    destination_path = f'./replays_{strftime("%Y-%m-%d_%H-%M-%S", gmtime())}'
    os.mkdir(destination_path)

    files = get_rar_files('./downloaded_files')

    for file in files:
        name = file.split('/')[-1]

        if args.extract:
            patoolib.extract_archive(file, program='unrar', outdir=f'./{destination_path}/{name.replace('.rar', '')}')
        else:
            shutil.move(file, f'./{destination_path}/{name}') 
        os.remove(file)

    input("Press any key to quit...")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Automatically grab demo the X most recent demo files from a given team')
    parser.add_argument('url', type=str, help='Path to the matches page of the team')
    parser.add_argument('-c', '--count', type=int, required=True, help='The number of replay files to download')
    parser.add_argument('-e', '--extract', action='store_true', help='Extract the rar files')

    args = parser.parse_args()
    main(args)
