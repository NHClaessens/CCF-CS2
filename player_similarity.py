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

def extract_features(ticks: pd.DataFrame, player_name: str, map_name: str) -> dict:
    """
    Extracts features for a given player, including movement, aim, and behavior patterns.
    """
    player_ticks = ticks[(ticks['name'] == player_name) & (ticks['map'] == map_name if map_name else True)]

    # Movement heatmap (2D histogram of X, Y positions)
    heatmap, _, _ = np.histogram2d(player_ticks['X'], player_ticks['Y'], bins=50)

    # Aim variance (variance of aim punch angles)
    aim_variance = player_ticks[['aim_punch_angle_X', 'aim_punch_angle_Y', 'aim_punch_angle_Z']].var().to_numpy()

    # Ducking and airborne fractions
    ducking_fraction = player_ticks['duck_amount'].mean() if 'duck_amount' in player_ticks.columns else 0
    airborne_fraction = player_ticks['is_airborne'].mean() if 'is_airborne' in player_ticks.columns else 0

    # Movement patterns
    standing_still = (player_ticks['velocity'] < 5).mean()
    moving_forward = (player_ticks['velocity'] > 5).mean()

    return {
        'heatmap': heatmap,
        'aim_variance': aim_variance,
        'ducking_fraction': ducking_fraction,
        'airborne_fraction': airborne_fraction,
        'standing_still': standing_still,
        'moving_forward': moving_forward
    }

def compute_similarity(new_features: dict, known_features: dict, map_weight: float = 0.8) -> float:
    """
    Computes a confidence score based on multiple similarity metrics.
    """
    # Heatmap similarity (Jensen-Shannon divergence)
    heatmap_similarity = compute_heatmap_similarity(new_features['heatmap'], known_features['heatmap'])
    assert np.isscalar(heatmap_similarity), "Heatmap similarity must be a scalar."

    # Aim variance similarity (Mahalanobis distance)
    try:
        aim_similarity = 1 / (1 + mahalanobis(new_features['aim_variance'], known_features['aim_variance'], np.eye(len(new_features['aim_variance']))))
    except ValueError:
        aim_similarity = 0  # Handle cases where Mahalanobis distance fails
    assert np.isscalar(aim_similarity), "Aim similarity must be a scalar."

    # Ducking and airborne fractions (absolute difference normalized to similarity)
    ducking_similarity = 1 - abs(new_features['ducking_fraction'] - known_features['ducking_fraction'])
    airborne_similarity = 1 - abs(new_features['airborne_fraction'] - known_features['airborne_fraction'])
    assert np.isscalar(ducking_similarity), "Ducking similarity must be a scalar."
    assert np.isscalar(airborne_similarity), "Airborne similarity must be a scalar."

    # Movement patterns (Cosine similarity)
    movement_similarity = 1 - cosine(
        [new_features['standing_still'], new_features['moving_forward']],
        [known_features['standing_still'], known_features['moving_forward']]
    )
    assert np.isscalar(movement_similarity), "Movement similarity must be a scalar."

    # Weighted confidence score
    confidence_score = (
        map_weight * heatmap_similarity +
        0.2 * aim_similarity +
        0.2 * ducking_similarity +
        0.2 * airborne_similarity +
        0.2 * movement_similarity
    )

    return confidence_score

def main():
    parser = argparse.ArgumentParser(description='Compute player similarity between new and known demo files.')
    parser.add_argument('new_demo_folder', type=util.dir_path, help='Path to the folder containing the new demo file')
    parser.add_argument('known_demo_folder', type=util.dir_path, help='Path to the folder containing known demo files')
    parser.add_argument('--player', type=str, required=True, help='Player name to compare')
    parser.add_argument('--map', type=str, help='Map to filter comparisons')
    parser.add_argument('--limit', type=int, default=None, help='Limit the number of demo files to process')

    args = parser.parse_args()

    # Merge demo files for new and known demos
    new_ticks, _ = merger.merge_demo_files(args.new_demo_folder, ['X', 'Y', 'velocity', 'aim_punch_angle', 'duck_amount', 'is_airborne'], limit=args.limit)
    known_ticks, _ = merger.merge_demo_files(args.known_demo_folder, ['X', 'Y', 'velocity', 'aim_punch_angle', 'duck_amount', 'is_airborne'], limit=args.limit)

    new_ticks = util.split_list_columns(new_ticks)
    known_ticks = util.split_list_columns(known_ticks)

    # Extract features for the player in the new demo
    new_features = extract_features(new_ticks, args.player, args.map)

    # Compare against all players in the known demos
    known_players = known_ticks['name'].unique()
    similarities = []

    for known_player in tqdm(known_players, desc="Comparing against known players"):
        known_features = extract_features(known_ticks, known_player, args.map)
        similarity = compute_similarity(new_features, known_features)
        similarities.append((known_player, similarity))

    print(similarities)
    # Sort by similarity and display results
    similarities.sort(key=lambda x: x[1], reverse=True)
    print("\nPlayer Similarity Rankings:")
    for rank, (player, score) in enumerate(similarities, start=1):
        print(f"{rank}. {player}: {score:.4f}")

if __name__ == '__main__':
    main()