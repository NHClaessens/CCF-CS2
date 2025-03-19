import pickle
from time import strftime, localtime
from typing import List
import util
import pandas as pd
from progress.bar import Bar
import os
import hashlib

def merge_demo_files(folder_path : str, tick_props : List[str], save = True):
    # 6eb9ecd9559f291023f8d80ed4545eefc1f51ac8
    input_hash = hashlib.sha1((folder_path + str(tick_props)).encode('utf-8')).hexdigest()
    stored_name = f'./stored_dfs/{input_hash}'
    if os.path.exists(stored_name):
        print("Found stored data")
        merged_ticks = pd.read_feather(stored_name+'/merged_ticks')
        with open(stored_name+'/merged_events.pkl', 'rb') as file:
            merged_events = pickle.load(file)
            
        
        return merged_ticks, merged_events

    # Parse all demo files in the folder
    parsers = util.parse_demos_from_folder(folder_path)

    # Merge the demo files
    merged_ticks = pd.DataFrame()
    merged_events = []

    with Bar("Merging demo files", max=len(parsers)) as bar:
      for name, parser in parsers:
          info = parser.parse_header()
          ticks = parser.parse_ticks(wanted_props=tick_props)
          ticks['match'] = name
          ticks['map'] = info['map_name']

          events = parser.parse_events(event_name=['all'])

          merged_ticks = pd.concat([merged_ticks, ticks], ignore_index=True)
          merged_events += events
          bar.next()

    if save:
        print(f"Saving at: {stored_name}")
        os.makedirs(stored_name, exist_ok=True)
        merged_ticks.to_feather(stored_name+'/merged_ticks')
        with open(stored_name+'/merged_events.pkl', 'wb') as file:
            pickle.dump(merged_events,  file)
        with open(stored_name+'/info.txt', 'w') as file:
            file.write(f"""Created on: {strftime("%Y-%m-%d_%H-%M-%S", localtime())}
Tick props: {str(tick_props)}
""")
  
    return merged_ticks, merged_events