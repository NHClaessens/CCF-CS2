import argparse
from typing import List
import pandas as pd
import matplotlib
matplotlib.use('wxAgg')
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from tqdm import tqdm

import util
import merge_demo_files as merger
from scipy.stats import zscore

players_of_interest = [
    "ZywOo",
    "ropz",
    "flameZ",
    "mezii",
    "apEX",
]

tick_props = [
    'pitch',
    'yaw',
    'name',
]

def compute_derivatives(df: pd.DataFrame, props: List[str]) -> pd.DataFrame:
    """
    Computes speed (first derivative), acceleration (second derivative), and smoothness (jerk).
    
    :param df: DataFrame containing yaw and pitch columns.
    :param props: List of properties (like 'yaw', 'pitch') to calculate derivatives for.
    :return: DataFrame with speed, acceleration, and smoothness columns.
    """
    # Split by player to compute derivatives independently
    player_groups = df.groupby('name')
    
    for player, player_data in tqdm(player_groups, desc="Computing Derivatives", total=len(player_groups)):
        for prop in props:
            player_data[f'{prop}_speed'] = player_data[prop].diff()  # First derivative - speed
            player_data[f'{prop}_acceleration'] = player_data[f'{prop}_speed'].diff()  # Second derivative - acceleration
            player_data[f'{prop}_smoothness'] = player_data[f'{prop}_acceleration'].diff()  # Third derivative - jerk

            player_data.fillna({f'{prop}_speed': 0, f'{prop}_acceleration': 0, f'{prop}_smoothness': 0}, inplace=True)

        # Reassign back to the original dataframe
        df.loc[player_data.index, [f'{prop}_speed' for prop in props]] = player_data[[f'{prop}_speed' for prop in props]]
        df.loc[player_data.index, [f'{prop}_acceleration' for prop in props]] = player_data[[f'{prop}_acceleration' for prop in props]]
        df.loc[player_data.index, [f'{prop}_smoothness' for prop in props]] = player_data[[f'{prop}_smoothness' for prop in props]]
    
    return df


def plot_distribution(df: pd.DataFrame, player_name: str, prop: str, map_name: str, metric: str, bins: int = 30):
    """
    Plots a distribution of speed, acceleration, or smoothness for a player.
    
    :param df: DataFrame with player data.
    :param player_name: Name of the player to filter data.
    :param prop: 'yaw' or 'pitch'.
    :param map_name: The map name to filter data.
    :param metric: 'speed', 'acceleration', or 'smoothness'.
    :param bins: Number of bins for the histogram.
    """

    # Filter the data for the specific player and map
    player_data : pd.DataFrame = df[(df['name'] == player_name) & (df['map'] == map_name)]

    # z_scores = zscore(player_data[f'{prop}_{metric}'])
    # player_data = player_data[abs(z_scores) > 1]

    if prop == 'yaw':
        player_data = player_data[(player_data[f'{prop}_{metric}'].abs() > 50) & (player_data[f'{prop}_{metric}'].abs() < 300)]
    elif prop == 'pitch':
        player_data = player_data[(player_data[f'{prop}_{metric}'].abs() > 5) & (player_data[f'{prop}_{metric}'].abs() < 40)]

    # Plot the distribution of the specified metric
    plt.figure(figsize=(10, 6))
    sns.histplot(player_data[f'{prop}_{metric}'].dropna(), kde=True, bins=bins, color='blue', stat='density')
    plt.title(f'{metric.capitalize()} Distribution for {player_name} on {map_name} ({prop})')
    plt.xlabel(f'{metric.capitalize()}')
    plt.ylabel('Density')
    plt.grid(True)
    plt.savefig(f"./figures/cursor_movement/{player_name}_{map_name}_{prop}_{metric}_distribution.png")
    # plt.show()
    plt.close()


def main():
    parser = argparse.ArgumentParser(description='Generate aiming statistics for players')
    parser.add_argument('folder', type=util.dir_path, help='Path to the folder containing .dem files')
    parser.add_argument('--players', type=str, nargs='*', default=[], help='List of player usernames to filter (empty for all players)')
    parser.add_argument('--show', action='store_true', help='Show interactive plot instead of saving to file')
    parser.add_argument('--limit', type=int, default=None, help='Limit the number of demo files to process')
    parser.add_argument('--map', type=str, default=None, help='Filter results by a specific map')
    
    args = parser.parse_args()

    # Load the ticks data
    ticks = util.load_cache([args.folder, args.limit, tick_props])
    
    if ticks is None:
        ticks, _ = merger.merge_demo_files(
            folder_path=args.folder, 
            tick_props=tick_props,
            players_of_interest=players_of_interest,
            limit=args.limit
        )

        util.store_cache(ticks, [args.folder, args.limit, tick_props])

    # Compute speed, acceleration, and smoothness for each player
    ticks = compute_derivatives(ticks, ['yaw', 'pitch'])

    # If a map is specified, filter the ticks by that map
    if args.map:
        ticks = ticks[ticks['map'] == args.map]

    # Generate distribution plots for each player
    for player in tqdm(players_of_interest, desc="Processing Players"):
        for map_name in ticks['map'].unique():
            for prop in ['yaw', 'pitch']:
                for metric in ['speed', 'acceleration', 'smoothness']:
                    plot_distribution(ticks, player, prop, map_name, metric)


if __name__ == '__main__':
    main()
