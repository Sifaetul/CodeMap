from typing import List, Dict, Set, Tuple, Any, Optional
from collections import defaultdict

def detect_cycles(edges: List[Tuple[str, str]]) -> List[List[str]]:
    """
    Implements Tarjan's Strongly Connected Components algorithm.
    Edges is a list of tuples (source_id, target_id).
    Returns a list of cycles (where a cycle is a list of node IDs > 1).
    """
    graph: Dict[str, List[str]] = defaultdict(list)
    for u, v in edges:
        graph[u].append(v)
        
    index = 0
    stack: List[str] = []
    indices: Dict[str, int] = {}
    lowlinks: Dict[str, int] = {}
    on_stack: Set[str] = set()
    sccs: List[List[str]] = []
    
    def strongconnect(v: str):
        nonlocal index
        indices[v] = index
        lowlinks[v] = index
        index += 1
        stack.append(v)
        on_stack.add(v)
        
        for w in graph.get(v, []):
            if w not in indices:
                strongconnect(w)
                lowlinks[v] = min(lowlinks[v], lowlinks[w])
            elif w in on_stack:
                lowlinks[v] = min(lowlinks[v], indices[w])
                
        if lowlinks[v] == indices[v]:
            scc = []
            while True:
                w = stack.pop()
                on_stack.remove(w)
                scc.append(w)
                if w == v:
                    break
            if len(scc) > 1:
                sccs.append(scc)
                
    for node in list(graph.keys()):
        if node not in indices:
            strongconnect(node)
            
    return sccs

def compute_pagerank(
    nodes: List[str],
    edges: List[Tuple[str, str]],
    d: float = 0.85,
    max_iter: int = 100,
    tol: float = 1e-6
) -> Dict[str, float]:
    """
    Computes PageRank centrality for architectural components.
    Higher PageRank indicates highly depended-upon core components.
    """
    if not nodes:
        return {}

    n = len(nodes)
    node_set = set(nodes)
    
    # Inbound and outbound adjacency
    in_edges: Dict[str, List[str]] = defaultdict(list)
    out_degree: Dict[str, int] = defaultdict(int)
    
    for u, v in edges:
        if u in node_set and v in node_set:
            in_edges[v].append(u)
            out_degree[u] += 1
            
    # Initial uniform probability
    ranks = {node: 1.0 / n for node in nodes}
    base_prob = (1.0 - d) / n

    for _ in range(max_iter):
        new_ranks = {}
        # Distribute rank from dangling nodes (out_degree == 0)
        dangling_sum = sum(ranks[node] for node in nodes if out_degree[node] == 0)
        dangling_contrib = d * (dangling_sum / n)
        
        diff = 0.0
        for node in nodes:
            incoming_sum = sum(ranks[u] / out_degree[u] for u in in_edges[node])
            rank = base_prob + dangling_contrib + d * incoming_sum
            diff += abs(rank - ranks[node])
            new_ranks[node] = rank
            
        ranks = new_ranks
        if diff < tol:
            break

    # Normalize to 0-1 range for convenient visualization
    max_r = max(ranks.values()) if ranks else 1.0
    min_r = min(ranks.values()) if ranks else 0.0
    spread = (max_r - min_r) if (max_r - min_r) > 0 else 1.0
    
    normalized = {
        node: round((val - min_r) / spread, 4)
        for node, val in ranks.items()
    }
    return normalized

def compute_coupling_metrics(
    nodes: List[str],
    edges: List[Tuple[str, str]]
) -> Dict[str, Dict[str, Any]]:
    """
    Computes Afferent (Ca), Efferent (Ce) coupling and Instability index (I) for each node.
    I = Ce / (Ca + Ce)
    I = 0.0 -> Maximally Stable (many depend on it, it depends on few)
    I = 1.0 -> Maximally Unstable (it depends on many, few depend on it)
    """
    node_set = set(nodes)
    ca_counts: Dict[str, Set[str]] = defaultdict(set) # incoming callers
    ce_counts: Dict[str, Set[str]] = defaultdict(set) # outgoing callees

    for u, v in edges:
        if u in node_set and v in node_set and u != v:
            ce_counts[u].add(v)
            ca_counts[v].add(u)

    metrics = {}
    for node in nodes:
        ca = len(ca_counts[node])
        ce = len(ce_counts[node])
        total = ca + ce
        instability = round(ce / total, 3) if total > 0 else 0.0
        
        metrics[node] = {
            "ca": ca,
            "ce": ce,
            "instability": instability,
            "stability_status": "STABLE" if instability <= 0.3 else ("UNSTABLE" if instability >= 0.7 else "BALANCED")
        }
    return metrics

def detect_dead_code(
    nodes: List[str],
    edges: List[Tuple[str, str]],
    entrypoints: Optional[Set[str]] = None
) -> List[str]:
    """
    Detects potential dead/orphan code: nodes with in-degree 0 that are not known entrypoints.
    """
    if entrypoints is None:
        entrypoints = set()

    has_incoming: Set[str] = set()
    for u, v in edges:
        if u != v:
            has_incoming.add(v)

    dead_nodes = [
        node for node in nodes
        if node not in has_incoming and node not in entrypoints
    ]
    return dead_nodes

def detect_god_components(
    nodes: List[str],
    edges: List[Tuple[str, str]],
    threshold: int = 8
) -> List[Dict[str, Any]]:
    """
    Detects 'God Components' - entities/modules that are overly coupled and violate Single Responsibility.
    """
    coupling = compute_coupling_metrics(nodes, edges)
    god_components = []
    
    for node, data in coupling.items():
        total_connections = data["ca"] + data["ce"]
        if total_connections >= threshold:
            god_components.append({
                "node_id": node,
                "total_connections": total_connections,
                "ca": data["ca"],
                "ce": data["ce"],
                "instability": data["instability"]
            })
            
    god_components.sort(key=lambda x: x["total_connections"], reverse=True)
    return god_components
