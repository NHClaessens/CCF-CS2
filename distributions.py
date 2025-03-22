import argparse
from typing import Callable, List, Mapping
from tqdm import tqdm
import util
import pandas as pd
import matplotlib
matplotlib.use('wxAgg')

import matplotlib.pyplot as plt
import seaborn as sns
import merge_demo_files as merger

players_of_interest = [
    "ZywOo",
    "ropz",
    "flameZ",
    "mezii",
    "apEX",
]

tick_props = [
    'aim_punch_angle', 
    'aim_punch_angle_vel',
    'duck_amount',
]

def main():
    parser = argparse.ArgumentParser(description='Generate heatmaps of player locations')
    parser.add_argument('folder', type=util.dir_path, help='Path to the folder containing .dem files')
    parser.add_argument('--players', type=str, nargs='*', default=[], help='List of player usernames to filter (empty for all players)')
    parser.add_argument('--show', action='store_true', help='Show interactive plot instead of saving to file')

    args = parser.parse_args()

    ticks = util.load_cache([args.folder, tick_props])

    if ticks is None:
        ticks, _ = merger.merge_demo_files(
            folder_path=args.folder, 
            tick_props=tick_props,
            players_of_interest=players_of_interest
        )
    
        ticks = util.split_list_columns(ticks)

        util.store_cache(ticks, [args.folder, tick_props])

    print(f"Loaded {len(ticks)} ticks")
    print(ticks.head())

    plot_distribution_by_player(
        ticks, 
        fields_of_interest=['aim_punch_angle_X', 'aim_punch_angle_Y'], 
        name="aiming_position",
        filters={
            'aim_punch_angle_X': lambda x: (x < -2) | (x > 2),
            'aim_punch_angle_Y': lambda x: (x < -0.05) | (x > 0.05),
        },
        args=args,
    )

    plot_distribution_by_player(
        ticks, 
        fields_of_interest=['aim_punch_angle_vel_X', 'aim_punch_angle_vel_Y'], 
        name="aiming_velocity",
        filters={
            'aim_punch_angle_vel_X': lambda x: (x < -5 ) | (x > 5),
            'aim_punch_angle_vel_Y': lambda x: (x < -20) | (x > 20),
        },
        args=args,
    )

    plot_distribution_by_player(
        ticks, 
        fields_of_interest=['duck_amount'], 
        name="duck_amount",
        filters={
            'duck_amount': lambda x: x > 0.1
        },
        args=args,
    )

def plot_distribution_by_player(
        df : pd.DataFrame, 
        fields_of_interest : List[str], 
        name: str,
        args: argparse.Namespace,
        filters: Mapping[str, Callable[[any], bool]] = {}
    ):
    """
    Plots the distribution of given fields of interest, where each player gets a unique color.
    
    Args:
    - df (pd.DataFrame): The dataframe containing the game ticks data.
    - fields_of_interest (list or str): The columns to plot distributions for.
    """

    # Ensure the specified fields exist in the dataframe
    missing_fields = [field for field in fields_of_interest if field not in df.columns]
    if missing_fields:
        print(f"Warning: The following fields are missing from the dataframe: {', '.join(missing_fields)}")
        return
    
    for column, condition in filters.items():
        if column in df.columns:  # Only apply if the column exists in the DataFrame
            df = df[condition(df[column])]
    
    # Set the plot style for better visualization
    sns.set_theme(style="whitegrid")

    # Split the data by player (assuming a column 'player' exists)
    players = df['name'].unique()

    # Set up the plotting figure
    plt.figure(figsize=(10, 6))
    
    # Loop through each field of interest and plot
    for field in tqdm(fields_of_interest, desc="Columns", total=len(fields_of_interest)):
        plt.subplot(len(fields_of_interest), 1, fields_of_interest.index(field) + 1)
        for player in tqdm(players, desc="Players", total=len(players)):
            if player not in players_of_interest:
                continue
            # Get data for the current player and field of interest
            player_data = df[df['name'] == player][field]
            
            # Plot the distribution for the current player
            sns.kdeplot(player_data, label=player, fill=True)
        
        # Set the title for the subplot
        plt.title(f'Distribution of {field}')
        plt.xlabel(field)
        plt.ylabel('Density')
        
        plt.legend(title='Players', bbox_to_anchor=[1.05, 0.5], loc='center left')

    # Add a legend
    plt.subplots_adjust(left=0.1, right=0.8, hspace=0.5)

    if args.show:
        plt.show()
    else:
        plt.savefig(f"./figures/{name}.png")


if __name__ == '__main__':
    main()