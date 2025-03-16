from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from seleniumbase import Driver
import os
from time import localtime, strftime
import patoolib
import argparse
from requests import get

from selenium.webdriver.support.select import Select
from progress.bar import Bar
import util


def main(args):
    print("Starting web driver...")
    options = webdriver.ChromeOptions()
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    driver : webdriver.Chrome = Driver(uc=True, headless=False)

    driver.uc_open_with_reconnect(args.url, reconnect_time=6)

    print(driver.execute_script("return navigator.userAgent"))

    # Decline optional cookies
    driver.find_element(By.ID, "CybotCookiebotDialogBodyButtonDecline").click()

    time_filter_element = Select(driver.find_element(By.CLASS_NAME, "stats-sub-navigation-simple-filter-time"))
    time_filter_element.select_by_visible_text("All time")

    matches_table = driver.find_element(By.TAG_NAME, "tbody")
    match_rows = matches_table.find_elements(By.TAG_NAME, "tr")

    grouped_matches = []
    current_group = []

    previous_color = None
    match_page_links = []

    with Bar("Finding matches", max=args.count) as bar:
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
                bar.next()
                print(f"\tMatch {len(match_page_links)}: {date} vs {opponent}, {len(current_group)} rounds: {match_page_link}")

                current_group = [row]

            previous_color = bg_color

            if len(match_page_links) >= args.count:
                break

    match_detail_links = []
    with Bar("Fetching match detail pages", max=len(match_page_links)) as bar:
        for index, link in enumerate(match_page_links):
            driver.uc_open_with_reconnect(link, reconnect_time=6)
            match_detail_link = driver.find_element(By.CLASS_NAME, "match-page-link").get_attribute("href")
            match_detail_links.append(match_detail_link)
            bar.next()

    with Bar("Downloading demos", max=len(match_detail_links)) as bar:
        for index, link in enumerate(match_detail_links):
            driver.uc_open_with_reconnect(link, reconnect_time=6)
            download_button = driver.find_element(By.CLASS_NAME, "stream-box")

            download_button.click()
            util.wait_for_after_content(driver, (By.CLASS_NAME, 'vod-loading-status'), '"Download starting..."')
            sleep(3)
            util.monitor_folder_for_changes('./downloaded_files')
            sleep(1)
            bar.next()


    # TODO: time is lower by 1 hour
    destination_path = os.path.normpath(f'./replays_{strftime("%Y-%m-%d_%H-%M-%S", localtime())}')
    os.mkdir(destination_path)

    files = util.get_files_with_extension('./downloaded_files', 'rar')

    with Bar("Extracting files", max=len(files)) as bar:
        for file in files:
            name = file.split('downloaded_files')[-1]
            output_dir = os.path.normpath(f'{destination_path}{name.replace(".rar", "")}')

            patoolib.extract_archive(file, program='unrar', outdir=output_dir)
            if(args.delete):
                os.remove(file)
            bar.next()
    
    driver.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Automatically grab demo the X most recent demo files from a given team')
    parser.add_argument('url', type=str, help='Path to the matches page of the team')
    parser.add_argument('-c', '--count', type=int, required=True, help='The number of replay files to download')
    parser.add_argument('-d', '--delete', action='store_true', help='Delete the .rar files after extracting')

    args = parser.parse_args()
    main(args)
