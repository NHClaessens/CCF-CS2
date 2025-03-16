import json
import os
import argparse
import numpy as np
import pandas as pd
from typing import List
from demoparser2 import DemoParser
import util

all_fields = [
    'X',
    'Y',
    'Z',
    'health',
    'score',
    'balance',
    'aim_punch_angle',
    'aim_punch_angle_vel',
]

# Define functions for statistics calculations
def calculate_min(values : pd.Series):
    if values.dtype != np.dtype('int32'): 
        return None
    return min(values) if values is not None else None

def calculate_max(values):
    if values.dtype != np.dtype('int32'): 
        return None
    return max(values) if values is not None else None

def calculate_variance(values: pd.Series):
    print('variance', type(values), values.dtype, "\n", values.head())
    value = pd.Series(values).var() if len(values) > 1 else None
    print('variance', type(values), value)
    if type(value) is np.float32 or type(value) is np.float64:
        return float(value)
    return value

def calculate_average(values):
    value =  pd.Series(values).mean() if len(values) > 1 else None
    if type(value) is np.float32 or type(value) is np.float64:
        return float(value)
    return value

def get_statistics(name, values, all_stats = False):
    stats = {}

    if len(values) == 0:
        return {}

    stats['min'] = calculate_min(values)
    stats['max'] = calculate_max(values)
    stats['variance'] = calculate_variance(values)
    stats['average'] = calculate_average(values)
    
    return stats
    

# Function to recursively search for .dem files
# def find_dem_files(folder_path):
#     replays = []
#     filenames = []
#     for root, dirs, files in os.walk(folder_path):
#         for file in files:
#             if file.endswith('.dem'):
#                 replays.append(os.path.join(root, file))
#                 filenames.append(file)

#     print(f"Found {len(filenames)} replays: {filenames}")
#     return replays

# Parse the demo and extract the requested statistics
def parse_replays(replays, player_usernames, field_names: List[str], event_names: List[str], voice: bool):
    # Initialize a dictionary to store the statistics for each player
    player_data = {}

    for replay_path in replays:
        print(f"\n\nParsing {replay_path}")
        parser = DemoParser(replay_path)

        players = parser.parse_player_info()

        # Parse ticks and events from the demo file
        ticks = parser.parse_ticks(wanted_props=field_names)
        events = parser.parse_events(event_name=event_names, player=['name']) if event_names else None

        if players.empty:
            players = ticks.drop_duplicates(subset=['steamid', 'name'])[['steamid', 'name']]
        print(f"Players:\n{players}")


        if voice:
            steamid_bytes_dict = parser.parse_voice()
            print(f"Voice data: {steamid_bytes_dict.keys()}")

            if not steamid_bytes_dict:
                print(f"No voice data for {replay_path}")
            
            for steamid, raw_bytes in steamid_bytes_dict.items():    
                with open(f"{replay_path.replace('.dem',f'_{steamid}')}.wav", "wb") as f:
                    f.write(raw_bytes)

        # Convert ticks and events DataFrames to dictionaries keyed by player names
        for player_name in players['name']:
            print(f'parsing for {player_name}')
            if player_usernames and player_name not in player_usernames:
                continue

            if player_name not in player_data:
                player_data[player_name] = {'fields': {}, 'events': {}}

            player_tick_data = ticks[ticks['name'] == player_name] if ticks is not None else None
            
            for field in field_names:
                field_data = player_tick_data.get(field, pd.Series())
                player_data[player_name]['fields'][field] = field_data

            if events is not None:
                for event_name, event_data in events:
                    player_event_data = event_data[event_data['user_name'] == player_name]
                    player_data[player_name]['events'][event_name] = player_event_data


    return player_data

def dir_path(path):
    if os.path.isdir(path):
        return path
    else:
        raise argparse.ArgumentTypeError(f"{path} is not a valid directory")

def convert_stat_data(input_data):
    output_data = {}
    
    # Iterate over each character (Hyde, Jekyll, etc.)
    for character, fields in input_data.items():
        for field, stats in fields.items():
            # If the field doesn't exist in the output data, initialize it
            if field not in output_data:
                output_data[field] = {}

            # Iterate over each statistic (min, max, variance, average, etc.)
            for stat_type, value in stats.items():
                # If this statistic type doesn't exist for the field, initialize it as a list
                if stat_type not in output_data[field]:
                    output_data[field][stat_type] = []

                # Append the value to the corresponding statistic list for this field
                output_data[field][stat_type].append(value)
    
    return output_data

def rank_fields_by_variance_and_mean_difference(data):
    field_stats = []
    
    # Iterate through each field and calculate the required statistics
    for field, stats in data.items():
        # Calculate average variance (mean of the variance values for the field)
        avg_variance = sum(stats['variance']) / len(stats['variance'])
        
        # Calculate mean difference (absolute difference between max and min of the averages)
        mean_difference = abs(max(stats['average']) - min(stats['average']))
        
        # Store the field name, average variance, and mean difference
        field_stats.append({
            'field': field,
            'avg_variance': avg_variance,
            'mean_difference': mean_difference
        })
    
    # Sort first by average variance (ascending), and then by mean difference (descending)
    field_stats.sort(key=lambda x: (x['avg_variance'], -x['mean_difference']))

    print("Field Rankings by Average Variance and Mean Difference:")
    for index, field_stat in enumerate(field_stats, start=1):
        print(f"{index}. Field: {field_stat['field']}")
        print(f"   - Average Variance:\t{field_stat['avg_variance']:.6f}\t\tVariance values: {data[field_stat['field']]['variance']}")
        print(f"   - Mean Difference:\t{field_stat['mean_difference']:.6f}\t\tAverage values: {data[field_stat['field']]['average']}")
        print("-" * 40)
    
    # Return the list of field names, ranked
    return [field_stat['field'] for field_stat in field_stats]

# Main function to set up argument parsing and execute the script
def main():
    parser = argparse.ArgumentParser(description='Analyze CS2 replays using demoparser')
    parser.add_argument('folder', type=dir_path, help='Path to the folder containing .dem files')
    parser.add_argument('--players', type=str, nargs='*', default=[], help='List of player usernames to filter (empty for all players)')
    parser.add_argument('--fields', type=str, nargs='*', default=[], help='List of fields to analyze')
    parser.add_argument('--events', type=str, nargs='*', default=[], help='List of events to analyze')
    parser.add_argument('--voice', action='store_true', help='Extract voice data')
    
    args = parser.parse_args()

    if args.fields == ['all']:
        args.fields = all_fields

    # Find all .dem files
    replays = util.get_files_with_extension(args.folder, 'dem')

    # Parse replays and extract requested statistics
    player_data = parse_replays(replays, args.players, args.fields, args.events, args.voice)

    player_stats = {}
    # Calculate min, max, and variance for each field and event
    for player, data in player_data.items():
        # print(f"Results for player: {player}")
        
        player_field_stats = {}
        # For fields
        for field, field_values in data['fields'].items():
            stats = get_statistics(field, field_values)
            # print(f"  Field {field}:\n{json.dumps(stats, indent=4)}")
            player_field_stats[field] = stats
        player_stats[player] = player_field_stats

        # For events
        for event, event_values in data['events'].items():
            stats = get_statistics(event, event_values)
            # print(f"  Event {event}:\n{json.dumps(stats, indent=4)}")

        print()

    # Calculate and print average variances for each statistic
    # calculate_average_variance(player_stats)
    converted = convert_stat_data(player_stats)

    ranked = rank_fields_by_variance_and_mean_difference(converted)
    print(ranked)

if __name__ == '__main__':
    main()
