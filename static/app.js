const $ = (id) => document.getElementById(id);
let topology = null;
let highlightedEdges = [];
let highlightedNodes = [];
let failedEdges = [];

async function api(path, payload = {}) {
  const response = await fetch(path, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(payload)
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Request failed");
  return data;
}

function edgeKey(a, b) { return [a, b].sort().join("|"); }
function nodeById(id) { return topology.nodes.find(n => n.id === id); }

function renderMap() {
  const svg = $("network-map");
  const pieces = [];
  const edgeSet = new Set(highlightedEdges.map(e => edgeKey(e.source, e.target)));
  const failedSet = new Set(failedEdges.map(e => edgeKey(e[0], e[1])));
  for (const link of topology.links) {
    const a = nodeById(link.source), b = nodeById(link.target);
    const x1 = a.x, y1 = a.y, x2 = b.x, y2 = b.y;
    const key = edgeKey(link.source, link.target);
    const isFailed = failedSet.has(key);
    const cls = isFailed ? "failed" : (edgeSet.has(key) ? (window.treeMode ? "tree" : "route") : "");
    pieces.push(`<line class="link-line ${cls}" x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}"/>`);
    const mx = (x1+x2)/2, my = (y1+y2)/2;
    pieces.push(`<text class="link-cost" x="${mx}" y="${my-7}" text-anchor="middle">${link.cost}</text>`);
  }
  for (const node of topology.nodes) {
    const selected = highlightedNodes.includes(node.id);
    const isSource = node.id === $("source").value;
    const cls = isSource ? "source-node" : (selected ? "route-node" : "");
    pieces.push(`<g>
      <circle class="node-circle ${cls}" cx="${node.x}" cy="${node.y}" r="27"/>
      <text class="node-label" x="${node.x}" y="${node.y+4}">${node.id}</text>
      <text class="node-label" x="${node.x}" y="${node.y+48}" style="font-size:11px">${node.label}</text>
    </g>`);
  }
  svg.innerHTML = pieces.join("");
}

function fillControls() {
  const options = topology.nodes.map(n => `<option value="${n.id}">${n.id} — ${n.label}</option>`).join("");
  $("source").innerHTML = options;
  $("destination").innerHTML = options;
  $("source").value = "CORE";
  $("destination").value = "SERVER";
  $("failed-link").innerHTML = '<option value="">No failed link</option>' +
    topology.links.map(l => `<option value="${l.source}|${l.target}">${l.source} ↔ ${l.target} (cost ${l.cost})</option>`).join("");
  $("router-count").textContent = topology.nodes.length;
  $("link-count").textContent = topology.links.length;
  $("subnet-count").textContent = topology.departments.length;
  $("subnet-table").innerHTML = topology.departments.map(d =>
    `<tr><td>${d.name}</td><td>${d.network}</td><td>${d.gateway}</td></tr>`).join("");
}

function showResult(title, pill, html, success = true) {
  $("result-title").textContent = title;
  $("result-pill").textContent = pill;
  $("result-pill").className = "pill" + (success ? " success" : "");
  $("result-content").className = "result-content";
  $("result-content").innerHTML = html;
}

function metric(label, value) {
  return `<div class="metric"><strong>${value}</strong><span>${label}</span></div>`;
}
function fmt(value) { return value === null || value === undefined ? "Unreachable" : Number.isInteger(value) ? value : value.toFixed(2); }
function packetSizeBytes() {
  const value = Number.parseInt($("packet-size").value, 10);
  return Number.isFinite(value) ? Math.min(Math.max(value, 1), 10000000) : 1500;
}
function timeMetrics(result) {
  const rows = [metric("Algorithm execution", `${Number(result.algorithm_execution_time_ms || 0).toFixed(4)} ms`)];
  const estimate = result.transmission_estimate;
  if (estimate) {
    rows.push(metric("Estimated one-way transmission", `${Number(estimate.estimated_total_ms).toFixed(4)} ms`));
    rows.push(metric("Packet size / hops", `${estimate.payload_size_bytes} B / ${estimate.hop_count}`));
  }
  return rows.join("");
}
function selectedFailure() {
  const value = $("failed-link").value;
  return value ? [value.split("|")] : [];
}
function resetHighlights() {
  highlightedEdges = []; highlightedNodes = []; window.treeMode = false;
}

async function runDijkstra() {
  try {
    resetHighlights();
    const result = await api("/api/dijkstra", {
      source: $("source").value, destination: $("destination").value, disabled_links: selectedFailure(), payload_size_bytes: packetSizeBytes()
    });
    if (result.reachable) {
      highlightedNodes = result.path;
      highlightedEdges = result.path.slice(1).map((node, i) => ({source: result.path[i], target: node}));
      const path = result.path.map((n, i) => `${i ? '<span class="path-arrow">→</span>' : ""}<span class="path-node">${n}</span>`).join("");
      showResult("Dijkstra shortest path", "Path found", `<div class="path-flow">${path}</div><div class="metric-row">${metric("Total path cost", fmt(result.cost))}${metric("Routers in path", result.path.length)}${metric("Reachable", "Yes")}${timeMetrics(result)}</div><p class="hint">Execution time is measured for this algorithm run. Transmission time is estimated using the assumptions listed below.</p>`);
    } else {
      showResult("Dijkstra shortest path", "No route", `<div class="notice">No available route from ${result.source} to ${result.destination} with the selected link state.</div>`, false);
    }
    failedEdges = selectedFailure(); renderMap();
  } catch (error) { showError(error); }
}

async function runDistanceVector() {
  try {
    resetHighlights();
    const result = await api("/api/distance-vector", {source: $("source").value, destination: $("destination").value, disabled_links: selectedFailure(), payload_size_bytes: packetSizeBytes()});
    const rows = Object.entries(result.selected_table || {}).map(([dest, route]) =>
      `<tr><td>${dest}</td><td>${fmt(route.distance)}</td><td>${route.next_hop || "—"}</td></tr>`).join("");
    const allTables = Object.entries(result.routing_tables).map(([router, table]) => {
      const body = Object.entries(table).map(([dest, route]) => `<tr><td>${dest}</td><td>${fmt(route.distance)}</td><td>${route.next_hop || "—"}</td></tr>`).join("");
      return `<details class="router-table" ${router === result.source ? "open" : ""}><summary>${router} routing table</summary><div class="subtle-table"><table><thead><tr><th>Destination</th><th>Distance</th><th>Next hop</th></tr></thead><tbody>${body}</tbody></table></div></details>`;
    }).join("");
    showResult("Distance Vector routing", "Converged", `<div class="metric-row">${metric("Update rounds", result.iterations)}${metric("Routers", Object.keys(result.routing_tables).length)}${metric("Converged", result.converged ? "Yes" : "No")}${timeMetrics(result)}</div><p class="hint">Transmission estimate uses the selected source-to-destination shortest path, not a live packet capture.</p><h4 class="table-subhead">${result.source} routing table</h4><div class="table-scroll"><table><thead><tr><th>Destination</th><th>Distance</th><th>Next hop</th></tr></thead><tbody>${rows}</tbody></table></div><h4 class="table-subhead">All router tables</h4>${allTables}`);
    failedEdges = selectedFailure(); renderMap();
  } catch (error) { showError(error); }
}

async function runBroadcast() {
  try {
    resetHighlights();
    const result = await api("/api/broadcast-tree", {source: $("source").value, disabled_links: selectedFailure()});
    highlightedEdges = result.tree_edges;
    highlightedNodes = result.visited;
    window.treeMode = true;
    const edges = result.tree_edges.map(e => `<tr><td>${e.source}</td><td>${e.target}</td></tr>`).join("");
    const warning = result.unreachable.length ? `<div class="notice">Unreachable routers: ${result.unreachable.join(", ")}</div>` : "";
    showResult("Broadcast spanning tree", "Tree built", `<div class="metric-row">${metric("Tree links", result.transmissions)}${metric("Routers reached", result.visited.length)}${metric("Unreachable", result.unreachable.length)}${metric("Algorithm execution", `${Number(result.algorithm_execution_time_ms || 0).toFixed(4)} ms`)}</div><h4 class="table-subhead">Tree edges</h4><div class="table-scroll"><table><thead><tr><th>Parent</th><th>Child</th></tr></thead><tbody>${edges || '<tr><td colspan="2">No edges</td></tr>'}</tbody></table></div><p class="hint">${result.note}</p>${warning}`);
    failedEdges = selectedFailure(); renderMap();
  } catch (error) { showError(error); }
}

async function runFailure() {
  const value = $("failed-link").value;
  if (!value) {
    showResult("Link failure test", "Choose a link", '<div class="notice">Select a link first, then run the failure simulation.</div>', false);
    return;
  }
  try {
    resetHighlights();
    const link = value.split("|");
    const result = await api("/api/simulate-failure", {link, source: $("source").value, destination: $("destination").value, payload_size_bytes: packetSizeBytes()});
    failedEdges = [result.disabled_link];
    const d = result.dijkstra;
    if (d.reachable) {
      highlightedNodes = d.path;
      highlightedEdges = d.path.slice(1).map((node, i) => ({source: d.path[i], target: node}));
    }
    const pathText = d.reachable ? d.path.join(" → ") : "No route available";
    const sourceTable = result.distance_vector.selected_table || {};
    const destRoute = sourceTable[$("destination").value];
    showResult("Link failure simulation", "Failure applied", `<div class="notice">Disabled link: <strong>${link[0]} ↔ ${link[1]}</strong>. This is a simulated failure; the original topology file is unchanged.</div><div class="metric-row">${metric("New route cost", d.reachable ? fmt(d.cost) : "No route")}${metric("DV update rounds", result.distance_vector.iterations)}${metric("Destination reachable", d.reachable ? "Yes" : "No")}${timeMetrics(d)}</div><h4 class="table-subhead">Updated shortest path</h4><p>${pathText}</p><h4 class="table-subhead">Distance Vector view from ${$("source").value}</h4><p>Next hop to ${$("destination").value}: <strong>${destRoute?.next_hop || "—"}</strong> · Cost: <strong>${fmt(destRoute?.distance)}</strong></p>`, d.reachable);
    renderMap();
  } catch (error) { showError(error); }
}

function showError(error) {
  showResult("Could not run algorithm", "Error", `<div class="notice">${error.message}</div>`, false);
}
async function init() {
  try {
    const response = await fetch("/api/topology");
    topology = await response.json();
    fillControls();
    renderMap();
    $("dijkstra-btn").addEventListener("click", runDijkstra);
    $("dv-btn").addEventListener("click", runDistanceVector);
    $("broadcast-btn").addEventListener("click", runBroadcast);
    $("failure-btn").addEventListener("click", runFailure);
    $("reset-btn").addEventListener("click", () => {
      $("failed-link").value = ""; $("source").value = "CORE"; $("destination").value = "SERVER";
      resetHighlights(); failedEdges = []; renderMap();
      $("result-title").textContent = "Ready when you are";
      $("result-pill").textContent = "Idle"; $("result-pill").className = "pill";
      $("result-content").className = "result-content empty-state";
      $("result-content").textContent = "Choose an algorithm to see its output here.";
    });
    $("source").addEventListener("change", renderMap);
    $("failed-link").addEventListener("change", () => {
      failedEdges = selectedFailure(); renderMap();
    });
  } catch (error) { showError(error); }
}
document.addEventListener("DOMContentLoaded", init);
