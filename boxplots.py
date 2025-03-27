import os
import merge_demo_files as merger
import argparse
import util
import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams['figure.max_open_warning'] = 0  # Prevents max figure warnings
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

players_of_interest = [
    "ZywOo",
    "ropz",
    "flameZ",
    "mezii",
    "apEX",
]

def compute_boolean_fractions(ticks: pd.DataFrame, field: str) -> pd.DataFrame:
    """
    Computes the fraction of time each player spends in a specific boolean state (e.g., ducked, jumping).
    
    :param ticks: DataFrame containing 'match', 'name', and the specified boolean field
    :param field: The boolean field to analyze
    :return: DataFrame with 'name', 'match', and 'fraction_active' for the given field
    """
    if field not in ticks.columns:
        raise ValueError(f"Field '{field}' not found in DataFrame")

    # Group by player and match, then calculate fraction of time active
    stats = ticks.groupby(['name', 'match']).agg(
        total_ticks=(field, 'count'),  # Total recorded ticks
        active_ticks=(field, 'sum')    # Sum of active ticks (assuming 1 = active, 0 = not)
    ).reset_index()

    # Compute fraction of time spent active
    stats['fraction_active'] = stats.apply(
        lambda row: row['active_ticks'] / row['total_ticks'] if row['total_ticks'] > 0 else 0, axis=1
    )
    
    return stats

def plot_boolean_boxplot(data, field):
    """
    Creates a boxplot showing the fraction of time spent in a given boolean state (e.g., ducking, jumping).
    
    :param data: DataFrame with 'name', 'match', and 'fraction_active'
    :param field: The boolean field being analyzed
    """
    plt.figure(figsize=(12, 6))
    sns.boxplot(x='name', y='fraction_active', data=data, color='#ff7f0e')
    
    # Labels and title
    plt.xlabel("Player Name")
    plt.ylabel(f"Fraction of Time Spent {field.capitalize()}")
    plt.title(f"{field.capitalize()} Fraction Across Matches")
    
    plt.tight_layout()
    
    # Save the figure
    output_file = f'./figures/{field}_boxplot.png'
    plt.savefig(output_file)
    plt.close()
    print(f"Saved plot to {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Analyze player behavior based on boolean fields')
    parser.add_argument('folder', type=util.dir_path, help='Path to the folder containing .dem files')
    parser.add_argument('field', type=str, help='Boolean field to analyze (e.g., ducking, jumping)')
    parser.add_argument('--limit', type=int, default=None, help='Limit the number of demo files to process')
    
    args = parser.parse_args()

    # Merge demo files and extract required data
    ticks, _ = merger.merge_demo_files(
      folder_path=args.folder, 
      tick_props=[args.field, 'match', 'name'], 
      save=True, 
      players_of_interest=players_of_interest,
      limit=args.limit
    )

    # Compute fractions for the given field
    boolean_data = compute_boolean_fractions(ticks, args.field)

    # Plot boxplot
    plot_boolean_boxplot(boolean_data, args.field)

if __name__ == '__main__':
    main()
