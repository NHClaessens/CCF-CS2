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
    'pitch', 
    'yaw', 
]

import merge_demo_files as merger


def main():
    parser = argparse.ArgumentParser(description='Generate heatmaps of player locations')
    parser.add_argument('folder', type=util.dir_path, help='Path to the folder containing .dem files')
    parser.add_argument('--players', type=str, nargs='*', default=[], help='List of player usernames to filter (empty for all players)')
    parser.add_argument('--show', action='store_true', help='Show interactive plot instead of saving to file')
    parser.add_argument('--limit', type=int, default=None, help='Limit the number of demo files to process')


    args = parser.parse_args()

    ticks = util.load_cache([args.folder, args.limit, tick_props])

    if ticks is None:
        ticks, _ = merger.merge_demo_files(
            folder_path=args.folder, 
            tick_props=tick_props,
            players_of_interest=players_of_interest,
            limit=args.limit
        )
    
        # ticks = util.split_list_columns(ticks)

        util.store_cache(ticks, [args.folder, args.limit, tick_props])

    maps = util.parse_maps_from_ticks(ticks)

    for map_name in tqdm(maps['map'], desc="Making scatter plots for maps"):
      map_ticks = ticks[ticks['map'] == map_name]
      for player in tqdm(players_of_interest, desc="Making scatter plots for players"):
          plot_scatter(
              df=map_ticks, 
              player_name=player, 
              figure_name=f"{player}_{map_name}_aim_scatter",
              x='yaw',
              y='pitch',
              title=f"Aiming Scatter Plot for {player} on {map_name}",
              xlim=(-50, 10),
          )

def plot_scatter(
        df: pd.DataFrame, 
        player_name: str, 
        figure_name: str, 
        x: str, 
        y: str, 
        title: str,
        xlim: tuple[float, float] = None
    ):
    """
    Plots a scatter plot of aim positions (aim_X, aim_Y) for a given player,
    with different colors for each match.
    
    :param df: Pandas DataFrame with columns ['name', 'match', 'aim_X', 'aim_Y']
    :param player_name: Name of the player to filter data
    """
    # Filter data for the given player
    player_data = df[df['name'] == player_name]
    
    # Get unique matches
    matches = player_data['match'].unique()

    # Create scatter plot
    plt.figure(figsize=(10, 6))
    
    for match in matches:
        match_data = player_data[player_data['match'] == match]
        plt.scatter(match_data[x], match_data[y], label=f'Match {match}', alpha=0.7)
    
    # Labels and title
    plt.xlabel(x)
    plt.ylabel(y)
    plt.title(title)
    if(xlim):
        plt.xlim(xlim)

    # plt.legend()
    # plt.show()
    plt.savefig(f"./figures/{figure_name}.png")

if __name__ == '__main__':
    main()