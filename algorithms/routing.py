"""Routing algorithms for the Smart College Network demo."""
from collections import deque
import heapq
import math

def graph_from_topology(topology, disabled_links=None):
    """Build an undirected weighted graph, omitting links marked as failed."""
    disabled = {
        tuple(sorted((str(link[0]), str(link[1]))))
        for link in (disabled_links or [])
        if isinstance(link, (list, tuple)) and len(link) == 2
    }
    graph = {node["id"]: {} for node in topology["nodes"]}
    for link in topology["links"]:
        source, target = link["source"], link["target"]
        if tuple(sorted((source, target))) in disabled:
            continue
        weight = float(link["cost"])
        graph[source][target] = weight
        graph[target][source] = weight
    return graph

def _validate(graph, node):
    if node not in graph:
        raise ValueError(f"Unknown router: {node}")

def dijkstra(graph, source, destination):
    """Return shortest path, path cost, and per-node distances."""
    _validate(graph, source)
    _validate(graph, destination)
    distances = {node: math.inf for node in graph}
    previous = {node: None for node in graph}
    distances[source] = 0
    queue = [(0, source)]
    while queue:
        current_cost, current = heapq.heappop(queue)
        if current_cost != distances[current]:
            continue
        if current == destination:
            break
        for neighbor, weight in graph[current].items():
            candidate = current_cost + weight
            if candidate < distances[neighbor]:
                distances[neighbor] = candidate
                previous[neighbor] = current
                heapq.heappush(queue, (candidate, neighbor))
    if math.isinf(distances[destination]):
        path = []
        cost = None
        reachable = False
    else:
        path = []
        current = destination
        while current is not None:
            path.append(current)
            current = previous[current]
        path.reverse()
        cost = distances[destination]
        reachable = True
    return {
        "algorithm": "Dijkstra",
        "source": source,
        "destination": destination,
        "path": path,
        "cost": cost,
        "reachable": reachable,
        "distances": {node: (None if math.isinf(value) else value) for node, value in distances.items()}
    }

def distance_vector(graph, source=None):
    """Bellman-Ford-style distance-vector updates until stable."""
    if source is not None:
        _validate(graph, source)
    nodes = list(graph)
    tables = {}
    iterations = 0
    # Each router starts knowing itself and its directly connected neighbors.
    for router in nodes:
        tables[router] = {}
        for destination in nodes:
            if destination == router:
                tables[router][destination] = {"distance": 0, "next_hop": "-"}
            elif destination in graph[router]:
                tables[router][destination] = {
                    "distance": graph[router][destination],
                    "next_hop": destination
                }
            else:
                tables[router][destination] = {"distance": math.inf, "next_hop": None}
    # Synchronous rounds avoid update-order bias and make convergence count reproducible.
    max_rounds = max(1, len(nodes) - 1)
    for _ in range(max_rounds):
        changed = False
        old = {
            router: {dest: dict(entry) for dest, entry in table.items()}
            for router, table in tables.items()
        }
        for router in nodes:
            for neighbor, link_cost in graph[router].items():
                for destination in nodes:
                    neighbor_distance = old[neighbor][destination]["distance"]
                    if math.isinf(neighbor_distance):
                        continue
                    candidate = link_cost + neighbor_distance
                    if candidate < tables[router][destination]["distance"]:
                        tables[router][destination] = {
                            "distance": candidate,
                            "next_hop": neighbor
                        }
                        changed = True
            # The route to self must remain zero.
            tables[router][router] = {"distance": 0, "next_hop": "-"}
        iterations += 1
        if not changed:
            break
    formatted = {}
    for router, table in tables.items():
        formatted[router] = {
            destination: {
                "distance": None if math.isinf(entry["distance"]) else entry["distance"],
                "next_hop": entry["next_hop"]
            }
            for destination, entry in table.items()
        }
    selected = formatted.get(source) if source else None
    return {
        "algorithm": "Distance Vector",
        "iterations": iterations,
        "converged": True,
        "source": source,
        "routing_tables": formatted,
        "selected_table": selected
    }

def broadcast_tree(graph, source="CORE"):
    """Build a breadth-first spanning tree (minimum hop count, not minimum cost)."""
    _validate(graph, source)
    visited = {source}
    parent = {source: None}
    queue = deque([source])
    tree_edges = []
    while queue:
        current = queue.popleft()
        for neighbor in sorted(graph[current]):
            if neighbor not in visited:
                visited.add(neighbor)
                parent[neighbor] = current
                tree_edges.append({"source": current, "target": neighbor})
                queue.append(neighbor)
    unreachable = [node for node in graph if node not in visited]
    return {
        "algorithm": "Broadcast Tree (BFS spanning tree)",
        "source": source,
        "tree_edges": tree_edges,
        "visited": list(parent.keys()),
        "unreachable": unreachable,
        "transmissions": len(tree_edges),
        "note": "This tree minimizes hop count from the source; it is not necessarily a minimum-cost tree."
    }
