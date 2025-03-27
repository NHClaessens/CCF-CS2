import pickle
from time import strftime, localtime
from typing import List
import util
import pandas as pd
import os
import hashlib
from tqdm import tqdm

# TODO: Filter by players of interest, as to not load all players into memory
def merge_demo_files(folder_path : str, tick_props : List[str], save : bool = True, players_of_interest : List[str] = None, limit: int = None, map_name: str = None):
    input_hash = hashlib.sha1((folder_path + str(tick_props) + str(players_of_interest) + (str(limit) if limit else "") + (map_name if map_name else "")).encode('utf-8')).hexdigest()
    stored_name = f'./stored_dfs/{input_hash}'
    if os.path.exists(stored_name):
        print(f"Found stored data in: {input_hash}")
        merged_ticks = pd.read_feather(stored_name+'/merged_ticks')
        with open(stored_name+'/merged_events.pkl', 'rb') as file:
            merged_events = pickle.load(file)
            
        
        return merged_ticks, merged_events

    # Parse all demo files in the folder
    parsers = util.parse_demos_from_folder(folder_path, limit=limit)

    # Merge the demo files
    merged_ticks = pd.DataFrame()
    merged_events = []


    for name, parser in tqdm(parsers, desc="Merging demo files", total=len(parsers)):
        info = parser.parse_header()
        ticks = parser.parse_ticks(wanted_props=tick_props)

        if players_of_interest is not None:
            ticks = ticks[ticks['name'].isin(players_of_interest)]
        if map_name is not None and info['map_name'] != map_name:
            continue

        ticks['match'] = name
        ticks['map'] = info['map_name']

        events = parser.parse_events(event_name=['all'])

        merged_ticks = pd.concat([merged_ticks, ticks], ignore_index=True)
        merged_events += events

    if save:
        print(f"Saving at: {stored_name}")
        os.makedirs(stored_name, exist_ok=True)
        merged_ticks.to_feather(stored_name+'/merged_ticks')
        with open(stored_name+'/merged_events.pkl', 'wb') as file:
            pickle.dump(merged_events,  file)
        with open(stored_name+'/info.txt', 'w') as file:
            file.write(f"""Created on: {strftime("%Y-%m-%d_%H-%M-%S", localtime())}
Tick props: {str(tick_props)}
Players of interest: {str(players_of_interest)}
""")
  
    return merged_ticks, merged_events