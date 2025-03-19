import argparse
from typing import Callable, List
from tqdm import tqdm
import util
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import merge_demo_files as merger

def main():
    parser = argparse.ArgumentParser(description='Generate heatmaps of player locations')
    parser.add_argument('folder', type=util.dir_path, help='Path to the folder containing .dem files')
    parser.add_argument('--players', type=str, nargs='*', default=[], help='List of player usernames to filter (empty for all players)')

    args = parser.parse_args()

    ticks, _ = merger.merge_demo_files(args.folder, ['aim_punch_angle', 'aim_punch_angle_vel'])

    ticks = filter_xyz_values(
                ticks, 
                'aim_punch_angle', 
                x=lambda x: x < -0.5 or x > 0.5,
                y=lambda y: y < -0.05 or y > 0.05,
                z=lambda z: z < -0.5 or z > 0.5,
            )
    
    ticks = filter_xyz_values(
                ticks, 
                'aim_punch_angle_vel', 
                x=lambda x: x != 0,
                y=lambda y: y != 0,
                z=lambda z: False
            )
    
    ticks = util.split_list_columns(ticks)

    # plot_distribution_by_player(ticks, ['aim_punch_angle_X', 'aim_punch_angle_Y', 'aim_punch_angle_Z'])
    plot_distribution_by_player(ticks, ['aim_punch_angle_vel_X', 'aim_punch_angle_vel_Y'])

def filter_xyz_values(df, column, x : Callable[[int], bool], y : Callable[[int], bool], z : Callable[[int], bool]):
    # Check if all XYZ values in 'aim_punch_angle_vel' and 'aim_punch_angle' are smaller than 10
    condition = df[column].apply(lambda e: x(e[0]) and y(e[1]) and z(e[2]))

    # Filter out rows where condition holds
    filtered_df = df[~condition]

    return filtered_df

def plot_distribution_by_player(df : pd.DataFrame, fields_of_interest : List[str]):
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
            # Get data for the current player and field of interest
            player_data = df[df['name'] == player][field]
            
            # Plot the distribution for the current player
            sns.kdeplot(player_data, label=player, fill=True)
        
        # Set the title for the subplot
        plt.title(f'Distribution of {field}')
        plt.xlabel(field)
        plt.ylabel('Density')

    # Add a legend
    plt.legend(title='Players', bbox_to_anchor=[1.05, -0.5], loc='center left')

    # Display the plot
    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    main()