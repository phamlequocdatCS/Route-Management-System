import numpy as np
from sklearn.neighbors import BallTree

EARTH_RADIUS_METER = 6371000


def calculate_ball_tree(location_coords):
    tree = BallTree(location_coords, leaf_size=15, metric="haversine")
    return tree


def nearest_loc_index(distances: np.ndarray, indices: np.ndarray, max_distance_meters):
    if max_distance_meters is not None:
        max_distance_rad = max_distance_meters / EARTH_RADIUS_METER
        close_enough = distances[0] < max_distance_rad

        if not np.any(close_enough):
            return None  # No locations are close enough

        nearest_index = indices[0][np.argmin(distances[0][close_enough])]
    else:
        nearest_index = indices[0][np.argmin(distances)]

    return nearest_index
