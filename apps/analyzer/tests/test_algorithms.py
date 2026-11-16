import pytest
from apps.analyzer.algorithms import (
    detect_cycles, compute_pagerank, compute_coupling_metrics,
    detect_dead_code, detect_god_components
)

def test_detect_cycles():
    # Simple cycle: A -> B -> C -> A
    edges = [("A", "B"), ("B", "C"), ("C", "A"), ("D", "A")]
    cycles = detect_cycles(edges)
    assert len(cycles) == 1
    assert set(cycles[0]) == {"A", "B", "C"}

def test_compute_pagerank():
    nodes = ["A", "B", "C", "D"]
    # All nodes point to D
    edges = [("A", "D"), ("B", "D"), ("C", "D")]
    ranks = compute_pagerank(nodes, edges)
    
    assert len(ranks) == 4
    # D must have the highest rank
    assert ranks["D"] == max(ranks.values())

def test_compute_coupling_metrics():
    nodes = ["Core", "Service1", "Service2"]
    # Service1 and Service2 both depend on Core
    edges = [("Service1", "Core"), ("Service2", "Core")]
    metrics = compute_coupling_metrics(nodes, edges)

    # Core: Ca = 2 (two callers), Ce = 0 (calls none). Instability = 0.0 (Maximally Stable)
    assert metrics["Core"]["ca"] == 2
    assert metrics["Core"]["ce"] == 0
    assert metrics["Core"]["instability"] == 0.0
    assert metrics["Core"]["stability_status"] == "STABLE"

    # Service1: Ca = 0, Ce = 1. Instability = 1.0 (Maximally Unstable)
    assert metrics["Service1"]["ca"] == 0
    assert metrics["Service1"]["ce"] == 1
    assert metrics["Service1"]["instability"] == 1.0
    assert metrics["Service1"]["stability_status"] == "UNSTABLE"

def test_detect_dead_code():
    nodes = ["entrypoint", "used_helper", "orphan_func"]
    edges = [("entrypoint", "used_helper")]
    
    dead = detect_dead_code(nodes, edges, entrypoints={"entrypoint"})
    assert "orphan_func" in dead
    assert "used_helper" not in dead
    assert "entrypoint" not in dead

def test_detect_god_components():
    nodes = ["god"] + [f"client_{i}" for i in range(10)]
    edges = [(f"client_{i}", "god") for i in range(10)]
    
    gods = detect_god_components(nodes, edges, threshold=8)
    assert len(gods) == 1
    assert gods[0]["node_id"] == "god"
    assert gods[0]["total_connections"] == 10
