# Copyright (c) 2025. RIKEN All rights reserved.
# This is for academic and non-commercial research use only.
# The technology is currently under patent application.
# Commercial use is prohibited without a separate license agreement.
# E-mail: akihiro.ezoe@riken.jp

"""Data preparation: clustering and statistics computation for paired data."""

import numpy as np
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import pdist, squareform


def load_data(input_file):
    """Load paired X,Y data from a file with automatic delimiter detection."""
    data = []
    delimiter = None
    header_skipped = False

    with open(input_file, "r") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            if delimiter is None and line_num == 1:
                if "," in line:
                    delimiter = ","
                elif "\t" in line:
                    delimiter = "\t"

            if not header_skipped:
                parts = (
                    [p.strip() for p in line.split(delimiter)]
                    if delimiter
                    else line.split()
                )
                if len(parts) >= 2:
                    try:
                        float(parts[0])
                        float(parts[1])
                    except ValueError:
                        header_skipped = True
                        continue
                header_skipped = True

            parts = (
                [p.strip() for p in line.split(delimiter)]
                if delimiter
                else line.split()
            )
            if len(parts) >= 2:
                try:
                    data.append([float(parts[0]), float(parts[1])])
                except ValueError:
                    pass

    return np.array(data) if data else np.array([])


def split_by_direction(data):
    """Split paired data into ascending (Y >= X) and descending (Y < X) groups."""
    diffs = data[:, 1] - data[:, 0]
    pos_indices = np.where(diffs >= 0)[0]
    neg_indices = np.where(diffs < 0)[0]
    return pos_indices.tolist(), neg_indices.tolist()


def find_optimal_k_elbow(data, max_k=7):
    """Determine optimal number of clusters using elbow method."""
    n = len(data)
    if n <= 3:
        return 1

    max_k = min(max_k, n)
    Z = linkage(data, method="ward")

    wss_list = []
    for k in range(1, max_k + 1):
        if k == 1:
            centroid = np.mean(data, axis=0)
            wss = np.sum((data - centroid) ** 2)
        else:
            clusters = fcluster(Z, t=k, criterion="maxclust")
            wss = 0
            for cluster_id in range(1, k + 1):
                cluster_points = data[clusters == cluster_id]
                if len(cluster_points) > 0:
                    centroid = np.mean(cluster_points, axis=0)
                    wss += np.sum((cluster_points - centroid) ** 2)
        wss_list.append(wss)

    if len(wss_list) < 3:
        return min(2, n)

    angles = []
    for i in range(1, len(wss_list) - 1):
        angle1 = np.arctan2(wss_list[i - 1] - wss_list[i], 1)
        angle2 = np.arctan2(wss_list[i] - wss_list[i + 1], 1)
        angles.append(abs(angle1 - angle2))

    if not angles:
        return 2

    return np.argmax(angles) + 2


def hierarchical_clustering(data, max_k=7, method="ward"):
    """Perform hierarchical clustering with automatic k selection."""
    n = len(data)
    if n == 0:
        return np.array([]), 0
    if n == 1:
        return np.array([0]), 1

    optimal_k = find_optimal_k_elbow(data, max_k)
    Z = linkage(data, method=method)
    clusters = fcluster(Z, t=optimal_k, criterion="maxclust") - 1
    return clusters, optimal_k


# ---- HDBSCAN implementation (native, no external dependency) ----

class _UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n
        self.size = [1] * n

    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x, y):
        px, py = self.find(x), self.find(y)
        if px == py:
            return False
        if self.rank[px] < self.rank[py]:
            px, py = py, px
        self.parent[py] = px
        self.size[px] += self.size[py]
        if self.rank[px] == self.rank[py]:
            self.rank[px] += 1
        return True

    def get_size(self, x):
        return self.size[self.find(x)]


def _compute_core_distances(distance_matrix, min_samples):
    n = distance_matrix.shape[0]
    core_distances = np.zeros(n)
    for i in range(n):
        sorted_distances = np.sort(distance_matrix[i])
        if min_samples < len(sorted_distances):
            core_distances[i] = sorted_distances[min_samples]
        else:
            core_distances[i] = sorted_distances[-1]
    return core_distances


def _compute_mutual_reachability_distance(distance_matrix, core_distances):
    n = distance_matrix.shape[0]
    mutual_reach = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            mutual_reach[i, j] = max(
                core_distances[i], core_distances[j], distance_matrix[i, j]
            )
    return mutual_reach


def _minimum_spanning_tree_prim(distance_matrix):
    n = distance_matrix.shape[0]
    in_tree = np.zeros(n, dtype=bool)
    min_dist = np.full(n, np.inf)
    min_dist[0] = 0
    parent = np.full(n, -1, dtype=int)
    edges = []

    for _ in range(n):
        u = -1
        for i in range(n):
            if not in_tree[i] and (u == -1 or min_dist[i] < min_dist[u]):
                u = i
        in_tree[u] = True
        if parent[u] != -1:
            edges.append((parent[u], u, min_dist[u]))
        for v in range(n):
            if not in_tree[v] and distance_matrix[u, v] < min_dist[v]:
                min_dist[v] = distance_matrix[u, v]
                parent[v] = u
    return edges


def _build_condensed_tree(mst_edges, n_points, min_cluster_size):
    sorted_edges = sorted(mst_edges, key=lambda x: x[2])
    uf = _UnionFind(n_points)
    cluster_labels = np.arange(n_points)
    next_cluster_id = n_points
    tree = []
    cluster_sizes = {i: 1 for i in range(n_points)}
    cluster_birth = {i: 0.0 for i in range(n_points)}

    for u, v, dist in sorted_edges:
        cu, cv = uf.find(u), uf.find(v)
        if cu != cv:
            size_u = uf.get_size(u)
            size_v = uf.get_size(v)
            lambda_val = 1.0 / dist if dist > 0 else np.inf
            new_cluster = next_cluster_id
            next_cluster_id += 1
            tree.append({"parent": new_cluster, "child": cluster_labels[cu], "child_size": size_u, "lambda_val": lambda_val})
            tree.append({"parent": new_cluster, "child": cluster_labels[cv], "child_size": size_v, "lambda_val": lambda_val})
            cluster_sizes[new_cluster] = size_u + size_v
            cluster_birth[new_cluster] = lambda_val
            uf.union(u, v)
            root = uf.find(u)
            cluster_labels[root] = new_cluster

    n_clusters = next_cluster_id - n_points
    return tree, cluster_sizes, cluster_birth, n_clusters


def _extract_clusters_eom(tree, cluster_sizes, cluster_birth, n_clusters, n_points, min_cluster_size):
    if not tree:
        return np.zeros(n_points, dtype=int)

    all_clusters = set()
    cluster_children = {}
    cluster_lambda_max = {}

    for entry in tree:
        parent = entry["parent"]
        child = entry["child"]
        lambda_val = entry["lambda_val"]
        all_clusters.add(parent)
        all_clusters.add(child)
        if parent not in cluster_children:
            cluster_children[parent] = []
        cluster_children[parent].append(child)
        if child not in cluster_lambda_max:
            cluster_lambda_max[child] = lambda_val
        else:
            cluster_lambda_max[child] = max(cluster_lambda_max[child], lambda_val)

    cluster_stability = {}
    for cluster in all_clusters:
        if cluster < n_points:
            cluster_stability[cluster] = 0
        else:
            birth = cluster_birth.get(cluster, 0)
            death = cluster_lambda_max.get(cluster, birth)
            size = cluster_sizes.get(cluster, 0)
            cluster_stability[cluster] = (death - birth) * size

    selected_clusters = set()

    def select_clusters(cluster):
        children = cluster_children.get(cluster, [])
        if not children:
            return cluster_stability.get(cluster, 0)
        children_stability = sum(select_clusters(c) for c in children)
        own_stability = cluster_stability.get(cluster, 0)
        if own_stability > children_stability:
            for c in children:
                selected_clusters.discard(c)
            if cluster_sizes.get(cluster, 0) >= min_cluster_size:
                selected_clusters.add(cluster)
            return own_stability
        else:
            return children_stability

    root_cluster = max(all_clusters)
    select_clusters(root_cluster)

    if not selected_clusters:
        return np.zeros(n_points, dtype=int)

    labels = np.full(n_points, -1, dtype=int)

    def get_points_in_cluster(cluster):
        if cluster < n_points:
            return {cluster}
        points = set()
        children = cluster_children.get(cluster, [])
        for child in children:
            points.update(get_points_in_cluster(child))
        return points

    for cluster_idx, cluster in enumerate(sorted(selected_clusters)):
        points = get_points_in_cluster(cluster)
        for p in points:
            if labels[p] == -1:
                labels[p] = cluster_idx

    labels[labels == -1] = 0
    return labels


def hdbscan_clustering(data, min_cluster_size=5, min_samples=None):
    """Perform HDBSCAN clustering (native implementation)."""
    n = len(data)
    if n == 0:
        return np.array([]), 0
    if n == 1:
        return np.array([0]), 1
    if n == 2:
        return np.array([0, 0]), 1

    if min_samples is None:
        min_samples = min_cluster_size

    min_cluster_size = max(2, min(min_cluster_size, n // 2))
    min_samples = max(1, min(min_samples, n - 1))

    distances = squareform(pdist(data, metric="euclidean"))
    core_distances = _compute_core_distances(distances, min_samples)
    mutual_reach = _compute_mutual_reachability_distance(distances, core_distances)
    mst_edges = _minimum_spanning_tree_prim(mutual_reach)
    tree, cluster_sizes, cluster_birth, n_clusters = _build_condensed_tree(
        mst_edges, n, min_cluster_size
    )
    labels = _extract_clusters_eom(
        tree, cluster_sizes, cluster_birth, n_clusters, n, min_cluster_size
    )

    unique_labels = np.unique(labels[labels >= 0])
    n_found = len(unique_labels)

    if n_found == 0:
        return np.zeros(n, dtype=int), 1

    label_map = {old: new for new, old in enumerate(unique_labels)}
    labels = np.array([label_map.get(l, 0) for l in labels])
    return labels, n_found


def cluster_data(x, y, method="hierarchical", max_k=7, linkage_method="ward",
                 min_cluster_size=5, min_samples=None, log2=False):
    """
    Cluster paired data by direction and spatial proximity.

    Parameters
    ----------
    x : array-like
        Values for group A (first measurement).
    y : array-like
        Values for group B (second measurement).
    method : str
        Clustering method: 'hierarchical' or 'hdbscan'.
    max_k : int
        Maximum number of clusters for hierarchical method.
    linkage_method : str
        Linkage method: 'ward', 'complete', 'average', 'single'.
    min_cluster_size : int
        Minimum cluster size for HDBSCAN.
    min_samples : int or None
        Minimum samples for HDBSCAN core points.
    log2 : bool
        Apply log2 transformation before clustering.

    Returns
    -------
    dict
        Dictionary with keys 'x', 'y', 'clusters', 'n_clusters'.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    if len(x) != len(y):
        raise ValueError("x and y must have the same length")

    if log2:
        mask = (x > 0) & (y > 0)
        x = np.log2(x[mask])
        y = np.log2(y[mask])

    data = np.column_stack([x, y])
    pos_indices, neg_indices = split_by_direction(data)
    pos_data = data[pos_indices] if pos_indices else np.array([])
    neg_data = data[neg_indices] if neg_indices else np.array([])

    all_clusters = np.zeros(len(data), dtype=int)
    cluster_offset = 0

    if len(pos_data) > 0:
        if method == "hierarchical":
            pos_clusters, _ = hierarchical_clustering(pos_data, max_k, linkage_method)
        else:
            pos_clusters, _ = hdbscan_clustering(pos_data, min_cluster_size, min_samples)
        for i, idx in enumerate(pos_indices):
            all_clusters[idx] = pos_clusters[i]
        cluster_offset = pos_clusters.max() + 1 if len(pos_clusters) > 0 else 0

    if len(neg_data) > 0:
        if method == "hierarchical":
            neg_clusters, _ = hierarchical_clustering(neg_data, max_k, linkage_method)
        else:
            neg_clusters, _ = hdbscan_clustering(neg_data, min_cluster_size, min_samples)
        for i, idx in enumerate(neg_indices):
            all_clusters[idx] = neg_clusters[i] + cluster_offset

    return {
        "x": data[:, 0],
        "y": data[:, 1],
        "clusters": all_clusters,
        "n_clusters": len(set(all_clusters)),
    }


def _calculate_quartile_indices(n):
    if n == 0:
        return None, None, None
    return int(n / 4), int(n / 2), int(n * 3 / 4)


def _calculate_stats(values):
    """Calculate mean and quartiles for values (matches preparation_2.py exactly)."""
    n = len(values)
    if n == 0:
        return 0, 0, 0, 0, 0

    sorted_values = sorted(values)
    mean = sum(sorted_values) / n

    q1_idx, q2_idx, q3_idx = _calculate_quartile_indices(n)

    q1 = sorted_values[q1_idx]
    q2 = sorted_values[q2_idx]
    q3 = sorted_values[q3_idx]

    return mean, q1, q2, q3, n


def compute_statistics(x, y, clusters):
    """
    Compute group statistics for clustered paired data (matches preparation_2.py exactly).

    Parameters
    ----------
    x : array-like
        Group A values.
    y : array-like
        Group B values.
    clusters : array-like
        Cluster assignments.

    Returns
    -------
    dict
        Per-cluster statistics including quartiles, calculated points, and group counts.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    clusters = np.asarray(clusters, dtype=int)

    groups = {}
    for i in range(len(x)):
        c = int(clusters[i])
        if c not in groups:
            groups[c] = []
        groups[c].append([x[i], y[i], y[i] - x[i]])

    results = {}
    for cluster in sorted(groups.keys()):
        group_data = groups[cluster]
        x_values = [p[0] for p in group_data]
        y_values = [p[1] for p in group_data]
        diff_values = [p[2] for p in group_data]

        m = len(group_data)

        x_mean, x_q1, x_q2, x_q3, _ = _calculate_stats(x_values)
        y_mean, y_q1, y_q2, y_q3, _ = _calculate_stats(y_values)

        sorted_by_x = sorted(group_data, key=lambda item: item[0], reverse=True)
        sorted_by_diff = sorted(group_data, key=lambda item: item[2], reverse=True)

        q1_idx, q2_idx, q3_idx = _calculate_quartile_indices(m)

        if q2_idx is not None:
            q2_start = sorted_by_x[q2_idx][0]
            q2_diff = sorted_by_diff[q2_idx][2]
            q1_start = sorted_by_x[q1_idx][0]
            q1_diff = sorted_by_diff[q1_idx][2]
            q3_start = sorted_by_x[q3_idx][0]
            q3_diff = sorted_by_diff[q3_idx][2]
        else:
            q2_start = x_q2
            q2_diff = y_q2 - x_q2
            calc_y_q2 = q2_start + q2_diff
            q1_start = x_q1
            q1_diff = y_q1 - x_q1
            q3_start = x_q3
            q3_diff = y_q3 - x_q3

        diff_mean, diff_q1, diff_q2, diff_q3, _ = _calculate_stats(diff_values)

        results[cluster] = {
            "x": {"mean": x_mean, "q1": x_q1, "q2": x_q2, "q3": x_q3},
            "y": {"mean": y_mean, "q1": y_q1, "q2": y_q2, "q3": y_q3},
            "diff": {
                "mean": diff_mean,
                "q1": diff_q1,
                "q2": diff_q2,
                "q3": diff_q3,
                "q1_trapezoid": q1_diff,
                "q2_trapezoid": q2_diff,
                "q3_trapezoid": q3_diff
            },
            "calculated": {
                "mean_point": [q2_start, q2_start + q2_diff],
                "median_point": [q2_start, q2_start + q2_diff],
                "n": m,
                "q2_start": q2_start,
                "q2_diff": q2_diff,
                "q2_end": q2_start + q2_diff,
                "q1_start": q1_start,
                "q1_diff": q1_diff,
                "q3_start": q3_start,
                "q3_diff": q3_diff,
            },
        }

    return results
