import os
import numpy as np
import pandas as pd
from scipy.spatial.distance import cosine, euclidean, mahalanobis
from scipy.stats import entropy
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from tqdm import tqdm
import util
import merge_demo_files as merger
import argparse
from scipy.spatial.distance import jensenshannon
from cursor_movement import compute_derivatives
from scipy.stats import wasserstein_distance
from scipy.stats import ks_2samp
import matplotlib
matplotlib.use('wxAgg')
import matplotlib.pyplot as plt

tick_props = [
    'pitch',
    'yaw',
    'X',
    'Y',
    'ducking',
    'is_airborne',
]

players_of_interest = [
    "ZywOo",
    "ropz",
    "flameZ",
    "mezii",
    "apEX",
]

def filter_player_and_map(ticks: pd.DataFrame, player_name: str, map_name: str) -> pd.DataFrame:
    """
    Filter df to only include rows where `name == <player_name>` and `map == <map_name>`.
    """
    player_ticks = ticks[(ticks['name'] == player_name) & (ticks['map'] == map_name if map_name else True)]
    return player_ticks

def compute_similarity(new_features: pd.DataFrame, known_features: pd.DataFrame) -> float:
    """
    Computes a confidence score based on multiple similarity metrics.
    """
    return (
        compute_cursor_similarity_jensenshannon(new_features, known_features)
        # TODO: add more metrics here
        # such as heatmap, crouching/jumping, weapon usage, etc.
    ) / 1
    

def compute_cursor_similarity_jensenshannon(new_features: pd.DataFrame, known_features: pd.DataFrame) -> float:
    """
    Computes a confidence score based on multiple similarity metrics.
    """
    new_features = compute_derivatives(new_features, ['yaw', 'pitch'])
    known_features = compute_derivatives(known_features, ['yaw', 'pitch'])

    pitch_speed_1, _ = np.histogram(new_features['pitch_speed'], bins=50, density=True)
    pitch_speed_2, _ = np.histogram(known_features['pitch_speed'], bins=50, density=True)

    pitch_speed_jsd = jensenshannon(pitch_speed_1, pitch_speed_2)

    pitch_acceleration_1, _ = np.histogram(new_features['pitch_acceleration'], bins=50, density=True)
    pitch_acceleration_2, _ = np.histogram(known_features['pitch_acceleration'], bins=50, density=True)

    pitch_acceleration_jsd = jensenshannon(pitch_acceleration_1, pitch_acceleration_2)

    pitch_smoothness_1, _ = np.histogram(new_features['pitch_smoothness'], bins=50, density=True)
    pitch_smoothness_2, _ = np.histogram(known_features['pitch_smoothness'], bins=50, density=True)

    pitch_smoothness_jsd = jensenshannon(pitch_smoothness_1, pitch_smoothness_2)

    yaw_speed_1, _ = np.histogram(new_features['yaw_speed'], bins=50, density=True)
    yaw_speed_2, _ = np.histogram(known_features['yaw_speed'], bins=50, density=True)

    yaw_speed_jsd = jensenshannon(yaw_speed_1, yaw_speed_2)

    yaw_acceleration_1, _ = np.histogram(new_features['yaw_acceleration'], bins=50, density=True)
    yaw_acceleration_2, _ = np.histogram(known_features['yaw_acceleration'], bins=50, density=True)

    yaw_acceleration_jsd = jensenshannon(yaw_acceleration_1, yaw_acceleration_2)

    yaw_smoothness_1, _ = np.histogram(new_features['yaw_smoothness'], bins=50, density=True)
    yaw_smoothness_2, _ = np.histogram(known_features['yaw_smoothness'], bins=50, density=True)

    yaw_smoothness_jsd = jensenshannon(yaw_smoothness_1, yaw_smoothness_2)

    return 1 - (pitch_speed_jsd + pitch_acceleration_jsd + pitch_smoothness_jsd + yaw_speed_jsd + yaw_acceleration_jsd + yaw_smoothness_jsd) / 6

def compute_cursor_similarity_wasserstein(new_features: pd.DataFrame, known_features: pd.DataFrame) -> float:
    """
    Computes a confidence score based on multiple similarity metrics.
    """
    new_features = compute_derivatives(new_features, ['yaw', 'pitch'])
    known_features = compute_derivatives(known_features, ['yaw', 'pitch'])

    y1 = wasserstein_distance(new_features['yaw_speed'], known_features['yaw_speed'])
    y2 = wasserstein_distance(new_features['yaw_acceleration'], known_features['yaw_acceleration'])
    y3 = wasserstein_distance(new_features['yaw_smoothness'], known_features['yaw_smoothness'])

    p1 = wasserstein_distance(new_features['pitch_speed'], known_features['pitch_speed'])
    p2 = wasserstein_distance(new_features['pitch_acceleration'], known_features['pitch_acceleration'])
    p3 = wasserstein_distance(new_features['pitch_smoothness'], known_features['pitch_smoothness'])
    return 1 - (y1 + y2 + y3 + p1 + p2 + p3) / 6

def evaluate_players(new_ticks: pd.DataFrame, known_ticks: pd.DataFrame, players: list, map_name: str):
    """
    Evaluate the similarity scores for players of interest.
    """
    self_similarities = []
    other_similarities = []
    all_players = known_ticks['name'].unique()

    for player in tqdm(players, desc="Evaluating players"):
        # Filter features for the current player
        new_features = filter_player_and_map(new_ticks, player, map_name)
        known_features = filter_player_and_map(known_ticks, player, map_name)

        # Compute self-similarity
        if not new_features.empty and not known_features.empty:
            self_similarity = compute_similarity(new_features, known_features)
            self_similarities.append(self_similarity)
        
        # Compute similarity with other players
        for other_player in [p for p in all_players if p != player]:
            other_features = filter_player_and_map(known_ticks, other_player, map_name)
            if not new_features.empty and not other_features.empty:
                other_similarity = compute_similarity(new_features, other_features)
                other_similarities.append(other_similarity)

    # Calculate averages
    avg_self_similarity = np.mean(self_similarities) if self_similarities else 0
    min_self_similarity = np.min(self_similarities) if self_similarities else 0
    max_self_similarity = np.max(self_similarities) if self_similarities else 0
    avg_other_similarity = np.mean(other_similarities) if other_similarities else 0
    min_other_similarity = np.min(other_similarities) if other_similarities else 0
    max_other_similarity = np.max(other_similarities) if other_similarities else 0


    # Display results
    print("\nEvaluation Results:")
    print(f"Average self-similarity: {avg_self_similarity:.4f}")
    print(f"Min. self-similarity: {min_self_similarity:.4f}")
    print(f"Max. self-similarity: {max_self_similarity:.4f}")
    print('-' * 40)
    print(f"Average similarity with other players: {avg_other_similarity:.4f}")
    print(f"Min. similarity with other players: {min_other_similarity:.4f}")
    print(f"Max. similarity with other players: {max_other_similarity:.4f}")

def plot_similarity_results():
    """
    Plots a grouped bar chart of similarity evaluation results.
    
    Parameters:
        results (list of dicts): Each dict contains similarity metrics for a dataset.
            Example format:
            {
                "label": "Dataset 1",
                "avg_self": 0.85,
                "min_self": 0.70,
                "max_self": 0.95,
                "avg_other": 0.65,
                "min_other": 0.50,
                "max_other": 0.80
            }
    """
    results = [
        {
            "label": "Jensen-Shannon",
            "avg_self": 0.4534,
            "min_self": 0.3276,
            "max_self": 0.6264,
            "avg_other": 0.4927,
            "min_other": 0.2364,
            "max_other": 0.9702,
        },
        {
            "label": "Wasserstein",
            "avg_self": 0.9348,
            "min_self": 0.8272,
            "max_self": 0.9927,
            "avg_other": 0.8476,
            "min_other": 0.2843,
            "max_other": 0.9850,
        }
    ]
    categories = ["Avg Self", "Min Self", "Max Self", "Avg Other", "Min Other", "Max Other"]
    num_categories = len(categories)
    num_datasets = len(results)
    
    x = np.arange(num_categories)  # X-axis positions for each category
    bar_width = 0.8 / num_datasets  # Adjust width dynamically

    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#7f7f7f"]  # Blue, Orange, Green, Red, Purple, Gray

    fig, ax = plt.subplots(figsize=(10 + num_datasets, 6))

    for i, dataset in enumerate(results):
        shift = (i - (num_datasets - 1) / 2) * bar_width  # Center bars in each category
        ax.bar(x + shift, 
               [dataset["avg_self"], dataset["min_self"], dataset["max_self"], 
                dataset["avg_other"], dataset["min_other"], dataset["max_other"]], 
               width=bar_width, 
               color=colors[i % len(colors)],  # Use professional colors
               label=dataset["label"])

    # Formatting
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.set_ylabel("Similarity Score")
    ax.set_title("Self-Similarity vs. Similarity with Others")
    ax.legend()
    ax.set_ylim(0, 1)  # Assuming similarity scores are between 0 and 1

    # plt.show()
    plt.savefig("./figures/player_similarity_evaluation.png", dpi=300)

def main():
    parser = argparse.ArgumentParser(description='Compute player similarity between new and known demo files.')
    parser.add_argument('new_demo_folder', type=util.dir_path, help='Path to the folder containing the new demo file')
    parser.add_argument('known_demo_folder', type=util.dir_path, help='Path to the folder containing known demo files')
    parser.add_argument('--player', type=str, help='Player name to compare')
    parser.add_argument('--map', type=str, help='Map to filter comparisons')
    parser.add_argument('--limit', type=int, default=None, help='Limit the number of demo files to process')
    parser.add_argument('--limit_new', type=int, default=None, help='Limit the number of demo files to process')
    parser.add_argument('--evaluate', action='store_true', help='Evaluate players of interest')
    parser.add_argument('--plot', action='store_true', help='Plot similarity evaluation results')

    args = parser.parse_args()

    if args.plot:
        plot_similarity_results()
        return

    # Merge demo files for new and known demos
    new_ticks, _ = merger.merge_demo_files(args.new_demo_folder, tick_props, limit=args.limit_new)
    known_ticks, _ = merger.merge_demo_files(args.known_demo_folder, tick_props, limit=args.limit)

    # Ensure no duplicate matches, if sourcing from the same folder
    known_ticks = known_ticks[~known_ticks['match'].isin(new_ticks['match'])]

    new_ticks = util.split_list_columns(new_ticks)
    known_ticks = util.split_list_columns(known_ticks)

    if args.evaluate:
        # Evaluate players of interest
        evaluate_players(new_ticks, known_ticks, players_of_interest, args.map)
    else:
        if not args.player:
            print("Error: --player is required unless --evaluate is specified.")
            return

        # Extract features for the player in the new demo
        new_features = filter_player_and_map(new_ticks, args.player, args.map)

        # Compare against all players in the known demos
        known_players = known_ticks['name'].unique()
        similarities = []

        for known_player in tqdm(known_players, desc="Comparing against known players"):
            known_features = filter_player_and_map(known_ticks, known_player, args.map)
            similarity = compute_similarity(new_features, known_features)
            similarities.append((known_player, similarity))

        # Sort by similarity and display results
        similarities.sort(key=lambda x: x[1], reverse=True)
        print("\nPlayer Similarity Rankings:")
        for rank, (player, score) in enumerate(similarities, start=1):
            print(f"{rank}. {player}: {score:.4f}")

if __name__ == '__main__':
    main()