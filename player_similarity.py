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

tick_props = [
    'pitch',
    'yaw',
]

def normalize_features(features: pd.DataFrame, method: str = 'zscore') -> pd.DataFrame:
    """
    Normalizes features using the specified method (Min-Max or Z-score).
    """
    if method == 'minmax':
        scaler = MinMaxScaler()
    elif method == 'zscore':
        scaler = StandardScaler()
    else:
        raise ValueError("Unsupported normalization method. Use 'minmax' or 'zscore'.")
    
    return pd.DataFrame(scaler.fit_transform(features), columns=features.columns)

def compute_heatmap_similarity(new_heatmap: np.ndarray, known_heatmap: np.ndarray) -> float:
    """
    Computes similarity between two heatmaps using Jensen-Shannon divergence.
    """
    # Flatten the heatmaps to 1-D arrays
    new_heatmap = new_heatmap.flatten()
    known_heatmap = known_heatmap.flatten()

    # Normalize the heatmaps to sum to 1
    if np.sum(new_heatmap) == 0 or np.sum(known_heatmap) == 0:
        return 0  # Return 0 similarity if either heatmap is empty
    new_heatmap = new_heatmap / np.sum(new_heatmap)
    known_heatmap = known_heatmap / np.sum(known_heatmap)

    # Compute Jensen-Shannon divergence
    m = (new_heatmap + known_heatmap) / 2
    js_divergence = 0.5 * (entropy(new_heatmap, m, base=2) + entropy(known_heatmap, m, base=2))

    # Convert divergence to similarity
    return 1 - js_divergence

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
    new_features = compute_derivatives(new_features, ['yaw', 'pitch'])
    known_features = compute_derivatives(known_features, ['yaw', 'pitch'])

    yaw_speed_1, _ = np.histogram(new_features['yaw_speed'], bins=50, density=True)
    yaw_speed_2, _ = np.histogram(known_features['yaw_speed'], bins=50, density=True)

    yaw_speed_jsd = jensenshannon(yaw_speed_1, yaw_speed_2)

    yaw_acceleration_1, _ = np.histogram(new_features['yaw_acceleration'], bins=50, density=True)
    yaw_acceleration_2, _ = np.histogram(known_features['yaw_acceleration'], bins=50, density=True)

    yaw_acceleration_jsd = jensenshannon(yaw_acceleration_1, yaw_acceleration_2)

    yaw_smoothness_1, _ = np.histogram(new_features['yaw_smoothness'], bins=50, density=True)
    yaw_smoothness_2, _ = np.histogram(known_features['yaw_smoothness'], bins=50, density=True)

    yaw_smoothness_jsd = jensenshannon(yaw_smoothness_1, yaw_smoothness_2)
    return (yaw_speed_jsd + yaw_acceleration_jsd + yaw_smoothness_jsd) / 3



def main():
    parser = argparse.ArgumentParser(description='Compute player similarity between new and known demo files.')
    parser.add_argument('new_demo_folder', type=util.dir_path, help='Path to the folder containing the new demo file')
    parser.add_argument('known_demo_folder', type=util.dir_path, help='Path to the folder containing known demo files')
    parser.add_argument('--player', type=str, required=True, help='Player name to compare')
    parser.add_argument('--map', type=str, help='Map to filter comparisons')
    parser.add_argument('--limit', type=int, default=None, help='Limit the number of demo files to process')

    args = parser.parse_args()

    # Merge demo files for new and known demos
    new_ticks, _ = merger.merge_demo_files(args.new_demo_folder, tick_props, limit=args.limit)
    known_ticks, _ = merger.merge_demo_files(args.known_demo_folder, tick_props, limit=args.limit)

    new_ticks = util.split_list_columns(new_ticks)
    known_ticks = util.split_list_columns(known_ticks)

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