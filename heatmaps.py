import os
import merge_demo_files as merger
import argparse
import util
import matplotlib
matplotlib.use('Agg')
# Silence warning related to max amount of figures open at once
matplotlib.rcParams['figure.max_open_warning'] = 0 
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import seaborn as sns
import pandas as pd
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

players_of_interest = [
    "ZywOo",
    "ropz",
    "flameZ",
    "mezii",
    "apEX",
]

def main():
    parser = argparse.ArgumentParser(description='Generate heatmaps of player locations')
    parser.add_argument('folder', type=util.dir_path, help='Path to the folder containing .dem files')
    parser.add_argument('--min_vel', type=float, help="The minimum velocity to show in the heatmap. Ticks with velocity lower than this will not be shown")

    args = parser.parse_args()

    ticks, _ = merger.merge_demo_files(args.folder, ['X', 'Y', 'Z', 'velocity'], True, limit=10, players_of_interest=players_of_interest)
    matches = util.parse_matches_from_ticks(ticks)

    print("Generating heatmaps")
    # Generate heatmaps per round
    for _, data in tqdm(matches.iterrows(), desc="Matches", total=len(matches)):
        match = data['match']
        
        match_df = ticks[ticks['match'] == match]
        players = util.parse_players_from_ticks(match_df)
        maps = util.parse_maps_from_ticks(match_df)
        map_name = maps['map'].tolist()[0]

        print(f"\nMatch: {match}, map: {map_name}, players: {players['name'].tolist()}")
        
        # Generate per player
        for _, data in tqdm(players.iterrows(), desc="Players", total=len(players),):
            player_name = data['name']

            map_df = match_df[match_df["map"] == map_name]
            player_df = map_df[map_df["name"] == player_name]

            if args.min_vel:
                player_df = player_df[player_df['velocity'] > args.min_vel]

            generate_heatmap(
                df=player_df, 
                map_name= map_name,
                title=f"Heatmap of {player_name}'s Positions",
                save_path=match,
                save_filename=player_name,
            )
        
        # # Generate average heatmap for match
        # generate_heatmap(
        #     df=match_df, 
        #     map_name= map_name,
        #     title="Heatmap of everyone's Positions",
        #     save_path=match,
        #     save_filename="average",
        # )


def generate_heatmap(df: pd.DataFrame, map_name: str, title: str, save_path: str, save_filename: str):
    # Create figure and axis
    plt.figure(figsize=(10, 8))
    ax = plt.gca()

    # Plot the heatmap
    sns.kdeplot(
        x=df["X"], 
        y=df["Y"], 
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
    plt.title(title, fontsize=14)
    plt.xlabel("X Coordinate")
    plt.ylabel("Y Coordinate")
    plt.grid(True)

    # plt.show()
    if save_path and save_filename:
        os.makedirs(f"heatmaps/{save_path}", exist_ok=True)
        plt.savefig(f"heatmaps/{save_path}/{save_filename}.png")
    plt.close()




if __name__ == '__main__':
    main()