import os
import merge_demo_files as merger
import argparse
import util
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import seaborn as sns
import pandas as pd
from progress.bar import Bar

def main():
    parser = argparse.ArgumentParser(description='Generate heatmaps of player locations')
    parser.add_argument('folder', type=util.dir_path, help='Path to the folder containing .dem files')
    parser.add_argument('--players', type=str, nargs='*', default=[], help='List of player usernames to filter (empty for all players)')
    parser.add_argument('--show', action='store_true', help="Show the plots in an interactive window")
    parser.add_argument('--save', action='store_true', help="Save the plots to disk")
    parser.add_argument('--map', type=str, help="Only create heatmaps for this map")

    args = parser.parse_args()

    ticks, _ = merger.merge_demo_files(args.folder, ['X', 'Y', 'Z'], True)
    players = util.parse_players_from_ticks(ticks)
    maps = util.parse_maps_from_ticks(ticks)

    with Bar("Generating heatmaps", max=(len(players) * len(maps)), ) as bar:
        for _, data in maps.iterrows():
            map_name = data['map']

            if args.map and map_name != args.map:
                bar.next()
                continue

            for _, data in players.iterrows():
                name= data['name']
                if len(args.players) > 0 and name not in args.players:
                    bar.next()
                    continue
                generate_heatmap(name, map_name, ticks)
                bar.next()

def generate_heatmap(player_name: str, map_name: str, df: pd.DataFrame, show = False, store = True):
    # Filter data for the given map and player
    map_df = df[df["map"] == map_name]
    player_df = map_df[map_df["name"] == player_name]

    # Create figure and axis
    plt.figure(figsize=(10, 8))
    ax = plt.gca()

    # Plot the heatmap
    sns.kdeplot(
        x=player_df["X"], 
        y=player_df["Y"], 
        fill=True, 
        cmap="magma", 
        thresh=0.05, 
        levels=100,
        ax=ax,
        zorder=1
    )

    map_path = f'./maps/{map_name}.jpg'
    if os.path.exists(map_path):
        grid_x_min, grid_x_max = ax.get_xlim()
        grid_y_min, grid_y_max = ax.get_ylim()
        background = mpimg.imread(map_path)
        ax.imshow(background, extent=[grid_x_min, grid_x_max, grid_y_min, grid_y_max], aspect="auto", alpha=0.5, zorder=0)
    else:
        print(f"No map image found for {map_name}")

    

    # Titles and labels
    plt.title(f"Heatmap of {player_name}'s Positions", fontsize=14)
    plt.xlabel("X Coordinate")
    plt.ylabel("Y Coordinate")
    plt.grid(True)

    # Save the plot
    if show:
        plt.show()
    if store:
        os.makedirs(f"heatmaps/{map_name}", exist_ok=True)
        plt.savefig(f"heatmaps/{map_name}/{player_name}.png")




if __name__ == '__main__':
    main()