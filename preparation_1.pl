#Copyright (c) 2025. RIKEN All rights reserved.
#This is for academic and non-commercial research use only.
#The technology is currently under patent application.
#Commercial use is prohibited without a separate license agreement.
#E-mail: akihiro.ezoe@riken.jp

#!/usr/bin/env python3

import sys
import os
import argparse
import re
import numpy as np
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import pdist, squareform


def apply_log2_transform(data, min_value=1e-10):
    data = np.array(data, dtype=float)
    data = np.where(data <= 0, min_value, data)
    return np.log2(data), 0


def filter_non_positive_for_log2(data):
    mask = (data[:, 0] > 0) & (data[:, 1] > 0)
    filtered_count = len(data) - np.sum(mask)
    return data[mask], filtered_count


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
                if delimiter:
                    print(f"Detected delimiter: {'comma' if delimiter == ',' else 'tab'}")
                else:
                    print("Detected delimiter: whitespace")

            if not header_skipped:
                if is_header_line(line, delimiter):
                    print(f"Skipping header line: {line[:50]}{'...' if len(line) > 50 else ''}")
                    header_skipped = True
                    continue
                header_skipped = True

            result = parse_line(line, delimiter)
            if result:
                data.append(list(result))
            else:
                print(f"Warning: Could not parse line {line_num}: {line[:50]}{'...' if len(line) > 50 else ''}")

    return np.array(data) if data else np.array([])


def split_by_direction(data):
    pos_indices = []
    neg_indices = []

    for i, (x, y) in enumerate(data):
        diff = y - x
        if diff >= 0:
            pos_indices.append(i)
        else:
            neg_indices.append(i)

    return pos_indices, neg_indices


def find_optimal_k_elbow(data, max_k=7):
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
        angle1 = np.arctan2(wss_list[i-1] - wss_list[i], 1)
        angle2 = np.arctan2(wss_list[i] - wss_list[i+1], 1)
        angles.append(abs(angle1 - angle2))

    if not angles:
        return 2

    optimal_k = np.argmax(angles) + 2
    return optimal_k


def hierarchical_clustering(data, max_k=7, method='ward'):
    n = len(data)
    if n == 0:
        return np.array([]), 0
    if n == 1:
        return np.array([0]), 1

    optimal_k = find_optimal_k_elbow(data, max_k)

    Z = linkage(data, method=method)

    clusters = fcluster(Z, t=optimal_k, criterion='maxclust') - 1

    return clusters, optimal_k


def compute_core_distances(distance_matrix, min_samples):
    n = distance_matrix.shape[0]
    core_distances = np.zeros(n)

    for i in range(n):
        sorted_distances = np.sort(distance_matrix[i])
        if min_samples < len(sorted_distances):
            core_distances[i] = sorted_distances[min_samples]
        else:
            core_distances[i] = sorted_distances[-1]

    return core_distances


def compute_mutual_reachability_distance(distance_matrix, core_distances):
    n = distance_matrix.shape[0]
    mutual_reach = np.zeros((n, n))

    for i in range(n):
        for j in range(n):
            mutual_reach[i, j] = max(core_distances[i], core_distances[j], distance_matrix[i, j])

    return mutual_reach


def minimum_spanning_tree_prim(distance_matrix):
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


class UnionFind:
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


def build_condensed_tree(mst_edges, n_points, min_cluster_size):
    sorted_edges = sorted(mst_edges, key=lambda x: x[2])

    uf = UnionFind(n_points)

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


def extract_clusters_eom(tree, cluster_sizes, cluster_birth, n_clusters, n_points, min_cluster_size):
    if not tree:
        return np.zeros(n_points, dtype=int)

    all_clusters = set()
    cluster_children = {}
    cluster_lambda_max = {}

    for entry in tree:
        parent = entry['parent']
        child = entry['child']
        lambda_val = entry['lambda_val']

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

    distances = squareform(pdist(data, metric='euclidean'))

    core_distances = compute_core_distances(distances, min_samples)

    mutual_reach = compute_mutual_reachability_distance(distances, core_distances)

    mst_edges = minimum_spanning_tree_prim(mutual_reach)

    tree, cluster_sizes, cluster_birth, n_clusters = build_condensed_tree(
        mst_edges, n, min_cluster_size
    )

    labels = extract_clusters_eom(
        tree, cluster_sizes, cluster_birth, n_clusters, n, min_cluster_size
    )

    unique_labels = np.unique(labels[labels >= 0])
    n_found = len(unique_labels)

    if n_found == 0:
        return np.zeros(n, dtype=int), 1

    label_map = {old: new for new, old in enumerate(unique_labels)}
    labels = np.array([label_map.get(l, 0) for l in labels])

    return labels, n_found


def main():
    parser = argparse.ArgumentParser(
        description='Clustering analysis for paired data.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python preparation_1.py input.txt 4
  python preparation_1.py input.txt 4 --method hierarchical
  python preparation_1.py input.txt --method hdbscan --min_cluster_size 3
  python preparation_1.py input.txt 5 --method hierarchical --linkage ward
        '''
    )

    parser.add_argument('input_file', help='Input data file (comma/tab/space-separated X Y values)')
    parser.add_argument('max_k', nargs='?', type=int, default=7,
                        help='Maximum number of clusters (default: 7)')
    parser.add_argument('--method', '-m', choices=['hierarchical', 'hdbscan'],
                        default='hierarchical',
                        help='Clustering method (default: hierarchical)')
    parser.add_argument('--linkage', '-l', choices=['ward', 'complete', 'average', 'single'],
                        default='ward',
                        help='Linkage method for hierarchical clustering (default: ward)')
    parser.add_argument('--min_cluster_size', type=int, default=5,
                        help='Minimum cluster size for HDBSCAN (default: 5)')
    parser.add_argument('--min_samples', type=int, default=None,
                        help='Minimum samples for HDBSCAN core points (default: None)')
    parser.add_argument('--output_dir', '-o', default='output_EZ',
                        help='Output directory (default: output_EZ)')
    parser.add_argument('--log2', action='store_true',
                        help='Apply log2 transformation to values before clustering')

    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    output_file = os.path.join(args.output_dir, 'clustered_data.txt')
    marker_file = os.path.join(args.output_dir, '.log2_transformed')

    data = load_data(args.input_file)
    if len(data) == 0:
        print("Error: No valid data found in input file.", file=sys.stderr)
        sys.exit(1)

    print(f"Loaded {len(data)} data points from {args.input_file}")

    use_log2 = args.log2
    if use_log2:
        data, filtered_count = filter_non_positive_for_log2(data)
        if filtered_count > 0:
            print(f"Excluded {filtered_count} data points with non-positive values for log2 transformation")
        print(f"Applying log2 transformation to {len(data)} data points...")
        data[:, 0] = np.log2(data[:, 0])
        data[:, 1] = np.log2(data[:, 1])
        with open(marker_file, 'w') as f:
            f.write('log2_transformed=true\n')
    else:
        if os.path.exists(marker_file):
            os.remove(marker_file)

    print(f"Clustering method: {args.method}")

    pos_indices, neg_indices = split_by_direction(data)
    pos_data = data[pos_indices] if pos_indices else np.array([])
    neg_data = data[neg_indices] if neg_indices else np.array([])

    print(f"Positive changes (Y >= X): {len(pos_indices)} points")
    print(f"Negative changes (Y < X): {len(neg_indices)} points")

    all_clusters = np.zeros(len(data), dtype=int)
    cluster_offset = 0

    if len(pos_data) > 0:
        if args.method == 'hierarchical':
            pos_clusters, pos_k = hierarchical_clustering(
                pos_data,
                max_k=args.max_k,
                method=args.linkage
            )
        else:
            pos_clusters, pos_k = hdbscan_clustering(
                pos_data,
                min_cluster_size=args.min_cluster_size,
                min_samples=args.min_samples
            )

        for i, idx in enumerate(pos_indices):
            all_clusters[idx] = pos_clusters[i]

        cluster_offset = pos_clusters.max() + 1 if len(pos_clusters) > 0 else 0
        print(f"Positive group: {pos_k} clusters")

    if len(neg_data) > 0:
        if args.method == 'hierarchical':
            neg_clusters, neg_k = hierarchical_clustering(
                neg_data,
                max_k=args.max_k,
                method=args.linkage
            )
        else:
            neg_clusters, neg_k = hdbscan_clustering(
                neg_data,
                min_cluster_size=args.min_cluster_size,
                min_samples=args.min_samples
            )

        for i, idx in enumerate(neg_indices):
            all_clusters[idx] = neg_clusters[i] + cluster_offset

        print(f"Negative group: {neg_k} clusters")

    with open(output_file, 'w') as f:
        f.write("X Y Cluster\n")
        for i, (x, y) in enumerate(data):
            f.write(f"{x} {y} {all_clusters[i]}\n")

    print(f"Results saved to {output_file}")

    total_clusters = len(set(all_clusters))
    print(f"\nSummary:")
    print(f"  Total clusters: {total_clusters}")
    print(f"  Method: {args.method}")
    print(f"  Log2 transformation: {use_log2}")
    if args.method == 'hierarchical':
        print(f"  Linkage: {args.linkage}")
        print(f"  Max k: {args.max_k}")
    else:
        print(f"  Min cluster size: {args.min_cluster_size}")


if __name__ == '__main__':
    main()
