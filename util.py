import hashlib
import os
import pickle
from typing import List
import pandas as pd
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
from demoparser2 import DemoParser
import argparse
from tqdm import tqdm
import numpy as np

def get_files_with_extension(path, extension) -> List[str]:
    if not extension.startswith('.'):
        extension = "." + extension

    results = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(extension):
                results.append(os.path.normpath(os.path.join(root, file)))
    
    return results



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


def parse_demos_from_folder(folder_path, limit: int = None) -> List[tuple[str, DemoParser]]:
    # Find all .dem files in the folder
    demo_files = get_files_with_extension(folder_path, '.dem')
    print(f"Found {len(demo_files)} demo files")

    parsers = []

    total = len(demo_files)
    if limit and limit < total:
        total = limit
        
    for demo_file in tqdm(demo_files, desc="Parsing demo files", total=total):
        if limit and len(parsers) >= limit:
            break
        
        parent_folder_name = os.path.basename(os.path.dirname(demo_file))
        name = os.path.basename(demo_file)
        parsers.append((f"{parent_folder_name}_{name}", DemoParser(demo_file)))

    
    return parsers

def parse_players_from_ticks(ticks: pd.DataFrame) -> pd.DataFrame:
    return ticks.drop_duplicates(subset=['steamid', 'name'])[['steamid', 'name']]

def parse_maps_from_ticks(ticks: pd.DataFrame) -> pd.DataFrame:
    return ticks.drop_duplicates(subset=['map',])[['map']]

def parse_matches_from_ticks(ticks: pd.DataFrame) -> pd.DataFrame:
    return ticks.drop_duplicates(subset=['match',])[['match']]

def file_path(path):
    if os.path.isfile(path):
        return path
    else:
        raise argparse.ArgumentTypeError(f"{path} is not a valid file")


def dir_path(path):
    if os.path.isdir(path):
        return path
    else:
        raise argparse.ArgumentTypeError(f"{path} is not a valid directory")
    
def split_list_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna().copy()  # Drop None/NaN rows and avoid modifying original DataFrame

    for col in tqdm(df.columns, desc="Splitting columns", total=len(df.columns)):
        valid_rows = df[col].notna()
        if valid_rows.any():  # Ensure there are valid rows to process
            first_valid = df.loc[valid_rows, col].iloc[0]
            
            if isinstance(first_valid, (list, np.ndarray)) and len(first_valid) in [2, 3]:
                # Convert list column to DataFrame and assign directly
                expanded_df = pd.DataFrame(df.loc[valid_rows, col].to_list(), index=df.index[valid_rows])
                expanded_df.columns = [f"{col}_X", f"{col}_Y"] if len(first_valid) == 2 else [f"{col}_X", f"{col}_Y", f"{col}_Z"]

                df = df.drop(columns=[col])  # Drop original column
                df = df.join(expanded_df)  # Join expanded columns back
        
    return df

# def split_list_columns(df: pd.DataFrame) -> pd.DataFrame:
#     for col in tqdm(df.columns, desc="Splitting columns", total=len(df.columns)):
#         print(f"Processing column {col}")
#         # Check if the column contains lists of length 2 or 3
#         if isinstance(df[col].iloc[0], list) or isinstance(df[col].iloc[0], np.ndarray):
#             # Filter out rows where the column contains None or NaN
#             valid_rows = df[col].notna()
#             if valid_rows.any():  # Ensure there are valid rows to process

#                 if len(df[col].iloc[0]) == 3:
#                     df.loc[valid_rows, [f'{col}_X', f'{col}_Y', f'{col}_Z']] = pd.DataFrame(df[col].to_list(), index=df.index)
#                 elif len(df[col].iloc[0]) == 2:
#                     df.loc[valid_rows, [f'{col}_X', f'{col}_Y']] = pd.DataFrame(df[col].to_list(), index=df.index)
#             # Drop the original list column
#             df = df.drop(columns=[col])
#     return df

def store_cache(data, args):
    input_hash = hashlib.sha1((str(args)).encode('utf-8')).hexdigest()
    stored_name = f'./cache/{input_hash}.pkl'
    print(f"Storing to cache {input_hash}, with args {str(args)}")

    os.makedirs('./cache', exist_ok=True)
    pickle.dump(data, open(stored_name, 'wb'))

def load_cache(args):
    input_hash = hashlib.sha1((str(args)).encode('utf-8')).hexdigest()
    stored_name = f'./cache/{input_hash}.pkl'
    if os.path.exists(stored_name):
        print(f"Found stored data in cache {input_hash}, for args {str(args)}")
        return pickle.load(open(stored_name, 'rb'))
    
    return None