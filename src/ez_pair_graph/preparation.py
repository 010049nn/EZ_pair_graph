# Copyright (c) 2025. RIKEN All rights reserved.
# This is for academic and non-commercial research use only.
# The technology is currently under patent application.
# Commercial use is prohibited without a separate license agreement.
# E-mail: akihiro.ezoe@riken.jp

"""
Core data preparation: clustering and statistics computation.
Replicates the exact logic from preparation_1.py and preparation_2.py.
"""

import numpy as np
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import pdist, squareform


# ---------------------------------------------------------------------------
# Log2 helpers
# ---------------------------------------------------------------------------

def apply_log2_transform(data, min_value=1e-10):
    data = np.array(data, dtype=float)
    data = np.where(data <= 0, min_value, data)
    return np.log2(data)


def filter_non_positive_for_log2(x, y):
    """Remove pairs where either value is <= 0 (for log2)."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    mask = (x > 0) & (y > 0)
    return x[mask], y[mask], int(len(x) - mask.sum())


# ---------------------------------------------------------------------------
# Data loading helpers (for file-based workflow)
# ---------------------------------------------------------------------------

def detect_delimiter(line):
    if ',' in line:
        return ','
    elif '\t' in line:
        return '\t'
    else:
        return None


def is_header_line(line, delimiter):
    if delimiter:
        parts = [p.strip() for p in line.split(delimiter)]
    else:
        parts = line.split()
    if len(parts) < 2:
        return False
    try:
        float(parts[0])
        float(parts[1])
        return False
    except ValueError:
        return True


def parse_line(line, delimiter):
    if delimiter:
        parts = [p.strip() for p in line.split(delimiter)]
    else:
        parts = line.split()
    if len(parts) < 2:
        return None
    try:
        x = float(parts[0])
        y = float(parts[1])
        return (x, y)
    except ValueError:
        return None


def load_data(input_file):
    """Load paired data from a text/csv file.  Returns (x_array, y_array)."""
    data = []
    delimiter = None
    header_skipped = False

    with open(input_file, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            if delimiter is None and line_num == 1:
                delimiter = detect_delimiter(line)
            if not header_skipped:
                if is_header_line(line, delimiter):
                    header_skipped = True
                    continue
                header_skipped = True
            result = parse_line(line, delimiter)
            if result:
                data.append(result)

    if not data:
        return np.array([]), np.array([])
    arr = np.array(data)
    return arr[:, 0], arr[:, 1]


# ---------------------------------------------------------------------------
# Clustering — hierarchical
# ---------------------------------------------------------------------------

def _find_optimal_k_elbow(data, max_k=7):
    n = len(data)
    if n <= 3:
        return 1
    max_k = min(max_k, n)

    Z = linkage(data, method='ward')
    wss_list = []
    for k in range(1, max_k + 1):
        if k == 1:
            centroid = np.mean(data, axis=0)
            wss = np.sum((data - centroid) ** 2)
        else:
            clusters = fcluster(Z, t=k, criterion='maxclust')
            wss = 0
            for cid in range(1, k + 1):
                pts = data[clusters == cid]
                if len(pts) > 0:
                    c = np.mean(pts, axis=0)
                    wss += np.sum((pts - c) ** 2)
        wss_list.append(wss)

    if len(wss_list) < 3:
        return min(2, n)

    angles = []
    for i in range(1, len(wss_list) - 1):
        a1 = np.arctan2(wss_list[i - 1] - wss_list[i], 1)
        a2 = np.arctan2(wss_list[i] - wss_list[i + 1], 1)
        angles.append(abs(a1 - a2))
    if not angles:
        return 2
    return np.argmax(angles) + 2


def _hierarchical_clustering(data, max_k=7, method='ward'):
    n = len(data)
    if n == 0:
        return np.array([], dtype=int), 0
    if n == 1:
        return np.array([0]), 1
    optimal_k = _find_optimal_k_elbow(data, max_k)
    Z = linkage(data, method=method)
    clusters = fcluster(Z, t=optimal_k, criterion='maxclust') - 1
    return clusters, optimal_k


# ---------------------------------------------------------------------------
# Clustering — HDBSCAN (native implementation, identical to preparation_1.py)
# ---------------------------------------------------------------------------

def _compute_core_distances(distance_matrix, min_samples):
    n = distance_matrix.shape[0]
    core_distances = np.zeros(n)
    for i in range(n):
        sd = np.sort(distance_matrix[i])
        if min_samples < len(sd):
            core_distances[i] = sd[min_samples]
        else:
            core_distances[i] = sd[-1]
    return core_distances


def _compute_mutual_reachability_distance(distance_matrix, core_distances):
    n = distance_matrix.shape[0]
    mr = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            mr[i, j] = max(core_distances[i], core_distances[j], distance_matrix[i, j])
    return mr


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
            tree.append({
                'parent': new_cluster,
                'child': cluster_labels[cu],
                'child_size': size_u,
                'lambda_val': lambda_val
            })
            tree.append({
                'parent': new_cluster,
                'child': cluster_labels[cv],
                'child_size': size_v,
                'lambda_val': lambda_val
            })
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
        parent = entry['parent']
        child = entry['child']
        lv = entry['lambda_val']
        all_clusters.add(parent)
        all_clusters.add(child)
        if parent not in cluster_children:
            cluster_children[parent] = []
        cluster_children[parent].append(child)
        if child not in cluster_lambda_max:
            cluster_lambda_max[child] = lv
        else:
            cluster_lambda_max[child] = max(cluster_lambda_max[child], lv)

    cluster_stability = {}
    for c in all_clusters:
        if c < n_points:
            cluster_stability[c] = 0
        else:
            birth = cluster_birth.get(c, 0)
            death = cluster_lambda_max.get(c, birth)
            size = cluster_sizes.get(c, 0)
            cluster_stability[c] = (death - birth) * size

    selected_clusters = set()

    def select_clusters(cluster):
        children = cluster_children.get(cluster, [])
        if not children:
            return cluster_stability.get(cluster, 0)
        children_stab = sum(select_clusters(ch) for ch in children)
        own_stab = cluster_stability.get(cluster, 0)
        if own_stab > children_stab:
            for ch in children:
                selected_clusters.discard(ch)
            if cluster_sizes.get(cluster, 0) >= min_cluster_size:
                selected_clusters.add(cluster)
            return own_stab
        else:
            return children_stab

    root_cluster = max(all_clusters)
    select_clusters(root_cluster)

    if not selected_clusters:
        return np.zeros(n_points, dtype=int)

    labels = np.full(n_points, -1, dtype=int)

    def get_points_in_cluster(cluster):
        if cluster < n_points:
            return {cluster}
        pts = set()
        for ch in cluster_children.get(cluster, []):
            pts.update(get_points_in_cluster(ch))
        return pts

    for cidx, cluster in enumerate(sorted(selected_clusters)):
        for p in get_points_in_cluster(cluster):
            if labels[p] == -1:
                labels[p] = cidx
    labels[labels == -1] = 0
    return labels


def _hdbscan_clustering(data, min_cluster_size=5, min_samples=None):
    n = len(data)
    if n == 0:
        return np.array([], dtype=int), 0
    if n == 1:
        return np.array([0]), 1
    if n == 2:
        return np.array([0, 0]), 1
    if min_samples is None:
        min_samples = min_cluster_size
    min_cluster_size = max(2, min(min_cluster_size, n // 2))
    min_samples = max(1, min(min_samples, n - 1))

    distances = squareform(pdist(data, metric='euclidean'))
    core_dist = _compute_core_distances(distances, min_samples)
    mutual_reach = _compute_mutual_reachability_distance(distances, core_dist)
    mst_edges = _minimum_spanning_tree_prim(mutual_reach)
    tree, csizes, cbirth, nc = _build_condensed_tree(mst_edges, n, min_cluster_size)
    labels = _extract_clusters_eom(tree, csizes, cbirth, nc, n, min_cluster_size)

    unique_labels = np.unique(labels[labels >= 0])
    n_found = len(unique_labels)
    if n_found == 0:
        return np.zeros(n, dtype=int), 1
    label_map = {old: new for new, old in enumerate(unique_labels)}
    labels = np.array([label_map.get(l, 0) for l in labels])
    return labels, n_found


# ---------------------------------------------------------------------------
# Public API: cluster_data
# ---------------------------------------------------------------------------

def cluster_data(x, y, method='hierarchical', max_k=7, linkage_method='ward',
                 min_cluster_size=5, min_samples=None, log2=False):
    """
    Cluster paired data by direction and return cluster labels.

    Replicates the exact logic of preparation_1.py:
    1. Split data by direction (Y-X >= 0 vs < 0)
    2. Cluster each group independently
    3. Return combined cluster labels

    Parameters
    ----------
    x, y : array-like
        Paired data arrays.
    method : str
        'hierarchical' or 'hdbscan'
    max_k : int
        Max clusters for hierarchical method.
    linkage_method : str
        Linkage for hierarchical ('ward', 'complete', 'average', 'single').
    min_cluster_size : int
        Min cluster size for HDBSCAN.
    min_samples : int or None
        Min samples for HDBSCAN.
    log2 : bool
        Apply log2 transformation before clustering.

    Returns
    -------
    dict with keys:
        'clusters': np.array of cluster labels
        'n_clusters': int
        'x': np.array (possibly log2-transformed)
        'y': np.array (possibly log2-transformed)
        'log2_applied': bool
    """
    x = np.asarray(x, dtype=float).copy()
    y = np.asarray(y, dtype=float).copy()

    log2_applied = False
    if log2:
        x, y, filtered = filter_non_positive_for_log2(x, y)
        x = np.log2(x)
        y = np.log2(y)
        log2_applied = True

    n = len(x)
    data = np.column_stack([x, y])

    # Split by direction (same as preparation_1.py)
    pos_indices = []
    neg_indices = []
    for i in range(n):
        diff = y[i] - x[i]
        if diff >= 0:
            pos_indices.append(i)
        else:
            neg_indices.append(i)

    all_clusters = np.zeros(n, dtype=int)
    cluster_offset = 0

    pos_data = data[pos_indices] if pos_indices else np.array([])
    neg_data = data[neg_indices] if neg_indices else np.array([])

    if len(pos_data) > 0:
        if method == 'hierarchical':
            pc, pk = _hierarchical_clustering(pos_data, max_k=max_k, method=linkage_method)
        else:
            pc, pk = _hdbscan_clustering(pos_data, min_cluster_size=min_cluster_size,
                                          min_samples=min_samples)
        for i, idx in enumerate(pos_indices):
            all_clusters[idx] = pc[i]
        cluster_offset = pc.max() + 1 if len(pc) > 0 else 0

    if len(neg_data) > 0:
        if method == 'hierarchical':
            nc, nk = _hierarchical_clustering(neg_data, max_k=max_k, method=linkage_method)
        else:
            nc, nk = _hdbscan_clustering(neg_data, min_cluster_size=min_cluster_size,
                                          min_samples=min_samples)
        for i, idx in enumerate(neg_indices):
            all_clusters[idx] = nc[i] + cluster_offset

    return {
        'clusters': all_clusters,
        'n_clusters': len(set(all_clusters)),
        'x': x,
        'y': y,
        'log2_applied': log2_applied,
    }


# ---------------------------------------------------------------------------
# Public API: compute_statistics
# ---------------------------------------------------------------------------

def _calculate_quartile_indices(n):
    if n == 0:
        return None, None, None
    q1_idx = int(n / 4)
    q2_idx = int(n / 2)
    q3_idx = int(n * 3 / 4)
    return q1_idx, q2_idx, q3_idx


def _calculate_stats(values):
    n = len(values)
    if n == 0:
        return 0, 0, 0, 0, 0
    sv = sorted(values)
    mean = sum(sv) / n
    q1i, q2i, q3i = _calculate_quartile_indices(n)
    return mean, sv[q1i], sv[q2i], sv[q3i], n


def compute_statistics(x, y, clusters):
    """
    Compute per-cluster statistics. Replicates preparation_2.py exactly.

    Parameters
    ----------
    x, y : array-like
    clusters : array-like of int

    Returns
    -------
    dict : cluster_id -> statistics dict
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    clusters = np.asarray(clusters, dtype=int)

    groups = {}
    for i in range(len(x)):
        c = int(clusters[i])
        if c not in groups:
            groups[c] = []
        diff = float(y[i] - x[i])
        groups[c].append([float(x[i]), float(y[i]), diff])

    stats_results = {}
    for cluster in sorted(groups.keys()):
        gd = groups[cluster]
        xv = [p[0] for p in gd]
        yv = [p[1] for p in gd]
        dv = [p[2] for p in gd]
        m = len(gd)

        x_mean, x_q1, x_q2, x_q3, _ = _calculate_stats(xv)
        y_mean, y_q1, y_q2, y_q3, _ = _calculate_stats(yv)

        sorted_by_x = sorted(gd, key=lambda item: item[0], reverse=True)
        sorted_by_diff = sorted(gd, key=lambda item: item[2], reverse=True)

        q1_idx, q2_idx, q3_idx = _calculate_quartile_indices(m)

        if q2_idx is not None:
            q2_start = sorted_by_x[q2_idx][0]
            q2_diff = sorted_by_diff[q2_idx][2]
            calc_y_q2 = q2_start + q2_diff
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

        diff_mean, diff_q1, diff_q2, diff_q3, _ = _calculate_stats(dv)

        stats_results[cluster] = {
            'x': {'mean': x_mean, 'q1': x_q1, 'q2': x_q2, 'q3': x_q3},
            'y': {'mean': y_mean, 'q1': y_q1, 'q2': y_q2, 'q3': y_q3},
            'diff': {
                'mean': diff_mean,
                'q1': diff_q1,
                'q2': diff_q2,
                'q3': diff_q3,
                'q1_trapezoid': q1_diff,
                'q2_trapezoid': q2_diff,
                'q3_trapezoid': q3_diff,
            },
            'calculated': {
                # Round to 4 decimal places to match Docker pipeline
                # (preparation_2.py writes %.4f to calculated_points.txt,
                #  then plotting scripts read back the rounded values).
                'mean_point': [round(q2_start, 4), round(calc_y_q2, 4)],
                'median_point': [round(q2_start, 4), round(calc_y_q2, 4)],
                'n': m,
                'q2_start': q2_start,
                'q2_diff': q2_diff,
            }
        }

    return stats_results
