import random
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

def download_file(url, file_path):
    reply = get(url, stream=True)
    with open(file_path, 'wb') as file:
        for chunk in reply.iter_content(chunk_size=1024): 
            if chunk:
                file.write(chunk)

def follow_redir_to_download(path: str):
    curl_command = [
        'curl', path,
        '-H', 'accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        '-H', 'accept-language: en-GB,en-US;q=0.9,en;q=0.8',
        '-H', 'priority: u=0, i',
        '-H', 'referer: https://www.hltv.org/matches/2380059/vitality-vs-mouz-esl-pro-league-season-21',
        '-H', 'sec-ch-ua: "Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
        '-H', 'sec-ch-ua-mobile: ?0',
        '-H', 'sec-ch-ua-platform: "macOS"',
        '-H', 'sec-fetch-dest: document',
        '-H', 'sec-fetch-mode: navigate',
        '-H', 'sec-fetch-site: same-origin',
        '-H', 'upgrade-insecure-requests: 1',
        '-H', 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
        '-i',  # This flag tells curl to include the response headers
        '-L',  # Follow redirects
        '-v'  # Show verbose output to get details of the redirect (if any)
    ]

    # Run the cURL command and capture the output
    process = subprocess.Popen(curl_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    # Decode the output to get the response and error (if any)
    stdout = stdout.decode('utf-8')
    stderr = stderr.decode('utf-8')

    for line in stdout.splitlines():
        if line.lower().startswith('location:'):
            redirect_url = line.split(' ', 1)[1].strip()
            print("Redirect URL:", redirect_url)
            return redirect_url
    return None

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

    wait()
    time_filter_element = driver.find_element(By.CLASS_NAME, "stats-sub-navigation-simple-filter-time")
    time_filter_element.click()
    wait()

    time_filter_element.find_elements(By.CSS_SELECTOR, "*")[0].click()

    matches_table = driver.find_element(By.TAG_NAME, "table")
    match_rows = matches_table.find_elements(By.TAG_NAME, "tr")

    match_page_links = []
    for index, row in enumerate(match_rows):
        # Skip header row
        if index == 0:
            continue

        if index > args.count: 
            break
        
        match_link = row.find_element(By.TAG_NAME, "a").get_attribute("href")
        match_page_links.append(match_link)
        print(f"{index - 1}: {match_link}")

    match_detail_links = []
    for index, link in enumerate(match_page_links):
        driver.uc_open_with_reconnect(link, reconnect_time=6)
        match_detail_link = driver.find_element(By.CLASS_NAME, "match-page-link").get_attribute("href")
        match_detail_links.append(match_detail_link)

    download_links = []
    for index, link in enumerate(match_detail_links):
        driver.uc_open_with_reconnect(link, reconnect_time=6)
        download_button = driver.find_element(By.CLASS_NAME, "stream-box")
        print(f"{index}: download at: {download_button.get_attribute("data-demo-link")}")
        download_links.append(download_button.get_attribute("data-demo-link"))
        # download_button.click()

    destination_path = f'./replays_{strftime("%Y-%m-%d_%H-%M-%S", gmtime())}'
    os.mkdir(destination_path)

    # Link we want is: https://r2-demos.hltv.org/demos/112914/esl-pro-league-season-21-vitality-vs-mouz-bo3-Ko5VJMvyF1OsCx2TbVU9pb.rar
    for index, link in enumerate(download_links):
        actual_download_link = follow_redir_to_download(f"https://www.hltv.org{link}")
        print(f"Downloading file {index + 1} of {len(download_links)}: {actual_download_link}")
        if actual_download_link:
            download_file(actual_download_link, f"{destination_path}/{actual_download_link.split('/')[-1]}")

    files = get_rar_files(destination_path)

    for file in files:
        name = file.split('/')[-1]

        if args.extract:
            patoolib.extract_archive(file, program='unrar', outdir=f'./{destination_path}/{name.replace('.rar', '')}')
            os.remove(file)

    input("Press any key to quit...")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Automatically grab demo the X most recent demo files from a given team')
    parser.add_argument('url', type=str, help='Path to the matches page of the team')
    parser.add_argument('-c', '--count', type=int, required=True, help='The number of replay files to download')
    parser.add_argument('-e', '--extract', action='store_true', help='Extract the rar files')

    args = parser.parse_args()
    main(args)
