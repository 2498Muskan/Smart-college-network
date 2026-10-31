# Smart College Network Design and Routing Algorithms

A local educational project combining:
- A Flask web dashboard with a visual campus-router topology
- Dijkstra shortest-path routing
- Distance Vector routing-table updates
- Breadth-first broadcast spanning tree
- Simulated link failure
- Measured algorithm execution time (milliseconds) for Dijkstra, Distance Vector, and broadcast-tree runs
- Estimated one-way transmission time for a selected packet size and route
- Sample subnet plan and Cisco Packet Tracer build instructions

## Requirements

- Python 3.10 or newer
- A modern browser
- Cisco Packet Tracer (for the separate network-design demonstration)

## Run the web dashboard

### Windows
1. Extract the ZIP.
2. Open the extracted `Smart-College-Network` folder.
3. Open Command Prompt in that folder.
4. Create a virtual environment:
   ```bat
   py -m venv .venv
   .venv\Scripts\activate
   ```
5. Install dependencies:
   ```bat
   python -m pip install -r requirements.txt
   ```
6. Start the app:
   ```bat
   python app.py
   ```
7. Open `http://127.0.0.1:5000` in your browser.

### macOS / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```
Then open `http://127.0.0.1:5000`.

Stop the server with `Ctrl+C` in the terminal.

## Dashboard features

- **Find shortest path:** Dijkstra's algorithm using the weights in `data/network.json`.
- **Run Distance Vector:** displays the selected source router's table and all routers' tables.
- **Build broadcast tree:** uses BFS to build a spanning tree by hop count.
- **Simulate link failure:** disables a selected link for that request only and calculates routes again.
- **Reset topology:** clears dashboard selections and highlights.

The sample weights are abstract costs, not actual milliseconds or bandwidth values. The dashboard measures the time spent executing each algorithm on the current computer using a high-resolution performance timer; these measurements vary by machine and system load.

### Transmission-time estimate assumptions

The Dijkstra and link-failure results include an estimated one-way transmission time based on the selected route and packet size (default 1500 bytes, editable in the dashboard). For this educational estimate, each link is assumed to provide 100 Mbps bandwidth, 2 ms propagation delay, and 0.2 ms processing delay. The estimate is calculated per hop as serialization time + propagation delay + processing delay. It excludes queueing, congestion, retransmissions, protocol overhead, and actual hardware delays. This is a calculation based on assumptions, not a live measurement of real network traffic. A route with zero hops has an estimated transmission time of zero.

The web simulator is separate from Packet Tracer and does not automatically configure physical or simulated Cisco devices.

## Project structure

```text
Smart-College-Network/
├── app.py
├── algorithms/
│   ├── __init__.py
│   └── routing.py
├── data/
│   └── network.json
├── templates/
│   └── index.html
├── static/
│   ├── app.js
│   └── style.css
├── docs/
│   └── PacketTracer_Guide.md
├── requirements.txt
└── README.md
```

## API endpoints

- `GET /api/health`
- `GET /api/topology`
- `POST /api/dijkstra` — JSON: `{"source":"CORE","destination":"SERVER","disabled_links":[],"payload_size_bytes":1500}` (returns `algorithm_execution_time_ms` and `transmission_estimate`)
- `POST /api/distance-vector` — JSON: `{"source":"CORE","destination":"SERVER","disabled_links":[],"payload_size_bytes":1500}` (returns `algorithm_execution_time_ms`; also returns a transmission estimate when destination is supplied)
- `POST /api/broadcast-tree` — JSON: `{"source":"CORE","disabled_links":[]}`
- `POST /api/simulate-failure` — JSON: `{"link":["CORE","SERVER"],"source":"CORE","destination":"SERVER"}`

## Important algorithm notes

- Dijkstra assumes non-negative link costs; all sample costs are positive.
- Distance Vector uses synchronous Bellman-Ford-style table updates until stable.
- The broadcast tree is a BFS spanning tree, which minimizes hop count, not total weighted cost.
- A link failure is request-scoped: `network.json` is never modified.

## Suggested demo sequence

1. Run Dijkstra from `CORE` to `SERVER`.
2. Change the destination to `LIB` and run Dijkstra.
3. Run Distance Vector from `CORE`; expand the other router tables.
4. Build the broadcast tree from `CORE`.
5. Select `CORE ↔ SERVER` as the failed link and run the failure simulation.
6. Reset and show the department subnet table.
7. In Packet Tracer, demonstrate connectivity with `ping` and a routing table command.

See `docs/PacketTracer_Guide.md` for the simulator build plan.

## Run the algorithm tests

From the project folder, run:
```bash
python -m unittest discover -s tests -v
```
