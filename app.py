from flask import Flask, jsonify, render_template, request
from algorithms.routing import dijkstra, distance_vector, broadcast_tree, graph_from_topology
import json
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
TOPOLOGY_PATH = BASE_DIR / "data" / "network.json"

app = Flask(__name__)

# Explicit educational assumptions for estimated one-way transmission time.
DEFAULT_BANDWIDTH_MBPS = 100.0
DEFAULT_PROPAGATION_MS_PER_LINK = 2.0
DEFAULT_PROCESSING_MS_PER_LINK = 0.2
DEFAULT_PACKET_SIZE_BYTES = 1500


def estimate_transmission(path, payload_size_bytes=DEFAULT_PACKET_SIZE_BYTES):
    """Estimate one-way delay; this is a model, not a live network measurement."""
    if not path or len(path) < 2:
        hops = 0
    else:
        hops = len(path) - 1
    serialization_ms_per_link = (payload_size_bytes * 8 / (DEFAULT_BANDWIDTH_MBPS * 1_000_000)) * 1000
    total_ms = hops * (serialization_ms_per_link + DEFAULT_PROPAGATION_MS_PER_LINK + DEFAULT_PROCESSING_MS_PER_LINK)
    return {
        "payload_size_bytes": payload_size_bytes,
        "hop_count": hops,
        "assumptions": {
            "bandwidth_mbps_per_link": DEFAULT_BANDWIDTH_MBPS,
            "propagation_ms_per_link": DEFAULT_PROPAGATION_MS_PER_LINK,
            "processing_ms_per_link": DEFAULT_PROCESSING_MS_PER_LINK,
            "direction": "one-way",
            "note": "Estimated from fixed assumptions; not measured latency or a real packet transmission. Queueing, congestion, and protocol overhead are excluded."
        },
        "serialization_ms_per_link": round(serialization_ms_per_link, 6),
        "estimated_total_ms": round(total_ms, 6)
    }


def valid_payload_size(value):
    try:
        size = int(value)
    except (TypeError, ValueError):
        return DEFAULT_PACKET_SIZE_BYTES
    return min(max(size, 1), 10_000_000)


def load_topology():
    with TOPOLOGY_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)

@app.get("/")
def index():
    return render_template("index.html")

@app.get("/api/topology")
def topology():
    return jsonify(load_topology())

@app.post("/api/dijkstra")
def run_dijkstra():
    payload = request.get_json(silent=True) or {}
    topology_data = load_topology()
    graph = graph_from_topology(topology_data, payload.get("disabled_links", []))
    source = payload.get("source", "CORE")
    destination = payload.get("destination", "SERVER")
    try:
        started = time.perf_counter()
        result = dijkstra(graph, source, destination)
        result["algorithm_execution_time_ms"] = round((time.perf_counter() - started) * 1000, 6)
        result["execution_time_note"] = "Measured on this computer for this run; values vary by machine and system load."
        result["transmission_estimate"] = estimate_transmission(result["path"], valid_payload_size(payload.get("payload_size_bytes", DEFAULT_PACKET_SIZE_BYTES)))
        return jsonify(result)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

@app.post("/api/distance-vector")
def run_distance_vector():
    payload = request.get_json(silent=True) or {}
    topology_data = load_topology()
    graph = graph_from_topology(topology_data, payload.get("disabled_links", []))
    try:
        started = time.perf_counter()
        result = distance_vector(graph, payload.get("source"))
        result["algorithm_execution_time_ms"] = round((time.perf_counter() - started) * 1000, 6)
        result["execution_time_note"] = "Measured on this computer for this run; values vary by machine and system load."
        source = payload.get("source")
        if source and payload.get("destination"):
            route = (result.get("selected_table") or {}).get(payload["destination"], {})
            path_result = dijkstra(graph, source, payload["destination"])
            result["transmission_estimate"] = estimate_transmission(path_result["path"], valid_payload_size(payload.get("payload_size_bytes", DEFAULT_PACKET_SIZE_BYTES)))
        return jsonify(result)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

@app.post("/api/broadcast-tree")
def run_broadcast_tree():
    payload = request.get_json(silent=True) or {}
    topology_data = load_topology()
    graph = graph_from_topology(topology_data, payload.get("disabled_links", []))
    try:
        started = time.perf_counter()
        result = broadcast_tree(graph, payload.get("source", "CORE"))
        result["algorithm_execution_time_ms"] = round((time.perf_counter() - started) * 1000, 6)
        result["execution_time_note"] = "Measured on this computer for this run; values vary by machine and system load."
        return jsonify(result)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

@app.post("/api/simulate-failure")
def simulate_failure():
    payload = request.get_json(silent=True) or {}
    link = payload.get("link")
    topology_data = load_topology()
    valid_links = {tuple(sorted((item["source"], item["target"]))) for item in topology_data["links"]}
    if not isinstance(link, list) or len(link) != 2:
        return jsonify({"error": "Choose a valid link."}), 400
    normalized = tuple(sorted(link))
    if normalized not in valid_links:
        return jsonify({"error": "That link is not in the topology."}), 400
    graph = graph_from_topology(topology_data, [list(normalized)])
    source = payload.get("source", "CORE")
    destination = payload.get("destination", "SERVER")
    started = time.perf_counter()
    dijkstra_result = dijkstra(graph, source, destination)
    dijkstra_result["algorithm_execution_time_ms"] = round((time.perf_counter() - started) * 1000, 6)
    dijkstra_result["transmission_estimate"] = estimate_transmission(dijkstra_result["path"], valid_payload_size(payload.get("payload_size_bytes", DEFAULT_PACKET_SIZE_BYTES)))
    started = time.perf_counter()
    dv_result = distance_vector(graph, source)
    dv_result["algorithm_execution_time_ms"] = round((time.perf_counter() - started) * 1000, 6)
    return jsonify({
        "disabled_link": list(normalized),
        "dijkstra": dijkstra_result,
        "distance_vector": dv_result
    })

@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "project": "Smart College Network"})

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
