import os
import merge_demo_files as merger
import argparse
import util
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import seaborn as sns
import pandas as pd
from tqdm import tqdm

def main():
    parser = argparse.ArgumentParser(description='Generate heatmaps of player locations')
    parser.add_argument('folder', type=util.dir_path, help='Path to the folder containing .dem files')
    parser.add_argument('--players', type=str, nargs='*', default=[], help='List of player usernames to filter (empty for all players)')
    parser.add_argument('--show', action='store_true', help="Show the plots in an interactive window")
    parser.add_argument('--save', action='store_true', help="Save the plots to disk")
    parser.add_argument('--map', type=str, help="Only create heatmaps for this map")
    parser.add_argument('--min_vel', type=float, help="The minimum velocity to show in the heatmap. Ticks with velocity lower than this will not be shown")

    args = parser.parse_args()

    ticks, _ = merger.merge_demo_files(args.folder, ['X', 'Y', 'Z', 'velocity'], True)
    matches = util.parse_matches_from_ticks(ticks)

    # TODO: filter based on walking or standing still
    # TODO: Allow separating per match

    print("Generating heatmaps")
    for _, data in tqdm(matches.iterrows(), desc="Matches", total=len(matches)):
        match = data['match']
        
        match_df = ticks[ticks['match'] == match]
        players = util.parse_players_from_ticks(match_df)
        maps = util.parse_maps_from_ticks(match_df)
        map_name = maps['map'].tolist()[0]

        print(f"Match: {match}, map: {map_name}, players: {players['name'].tolist()}")
        
        for _, data in tqdm(players.iterrows(), desc="Players", total=len(players)):
            name= data['name']
            if len(args.players) > 0 and name not in args.players:
                continue

            generate_heatmap(
                player_name=name, 
                map_name=map_name, 
                match_name=match,
                df=match_df, 
                args=args, 
            )

def generate_heatmap(player_name: str, map_name: str, match_name: str, df: pd.DataFrame, args, override_filename = None):
    # Filter data for the given map and player
    map_df = df[df["map"] == map_name]
    player_df = map_df[map_df["name"] == player_name]
    if args.min_vel:
        player_df = player_df[player_df['velocity'] > args.min_vel]

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
    if args.show:
        plt.show()
    if args.save:
        os.makedirs(f"heatmaps/{match_name}", exist_ok=True)
        plt.savefig(f"heatmaps/{match_name}/{override_filename if override_filename else player_name}.png")
    plt.close()




if __name__ == '__main__':
    main()