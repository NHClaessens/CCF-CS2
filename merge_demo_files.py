import util
import pandas as pd
from progress.bar import Bar
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import seaborn as sns

def merge_demo_files(folder_path, tick_props):
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
  
    return merged_ticks, merged_events

def generate_heatmap(player_name: str, map_name: str, df: pd.DataFrame):
    # Filter data for the given map and player
    map_df = df[df["map"] == map_name]
    player_df = map_df[map_df["name"] == player_name]

    # Load background image
    background = mpimg.imread(f'./maps/{map_name}.jpg')

    # Create figure and axis
    plt.figure(figsize=(10, 8))
    ax = plt.gca()

    # Set the limits to match the grid size
    grid_x_min, grid_x_max = player_df["X"].min(), player_df["X"].max()
    grid_y_min, grid_y_max = player_df["Y"].min(), player_df["Y"].max()

    # Display the background image inside the grid only
    ax.imshow(background, extent=[grid_x_min, grid_x_max, grid_y_min, grid_y_max], aspect="auto", alpha=0.5, zorder=0)

    # Plot the heatmap
    print("Generating heatmap...")
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

    # Titles and labels
    plt.title(f"Heatmap of {player_name}'s Positions", fontsize=14)
    plt.xlabel("X Coordinate")
    plt.ylabel("Y Coordinate")
    plt.grid(True)

    # Save the plot
    plt.savefig(f"{player_name}_heatmap.png")

        
ticks, events = merge_demo_files("./replays_2025-03-16_13-26-16\\esl-pro-league-season-21-vitality-vs-3dmax-bo3-SFueR4Yd1u5-bIhh5XKwOq", ['X', 'Y', 'Z'])
generate_heatmap("ZywOo", "de_dust2", ticks)