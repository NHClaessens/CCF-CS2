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


tick_props = [
    'pitch',
    'yaw',
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
        compute_cursor_similarity(new_features, known_features)
        # TODO: add more metrics here
        # such as heatmap, crouching/jumping, weapon usage, etc.
    ) / 1
    

def compute_cursor_similarity(new_features: pd.DataFrame, known_features: pd.DataFrame) -> float:
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