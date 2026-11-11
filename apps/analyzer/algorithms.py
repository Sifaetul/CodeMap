from typing import List, Dict, Set

def detect_cycles(edges: List[tuple]) -> List[List[str]]:
    """
    Implements Tarjan's Strongly Connected Components algorithm.
    Edges is a list of tuples (source_id, target_id).
    Returns a list of cycles (where a cycle is a list of node IDs > 1).
    """
    graph = {}
    for u, v in edges:
        if u not in graph:
            graph[u] = []
        graph[u].append(v)
        
    index = 0
    stack = []
    indices = {}
    lowlinks = {}
    on_stack = set()
    sccs = []
    
    def strongconnect(v):
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
                
    for node in graph:
        if node not in indices:
            strongconnect(node)
            
    return sccs
