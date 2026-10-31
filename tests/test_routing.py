import json
import unittest
from pathlib import Path
from algorithms.routing import graph_from_topology, dijkstra, distance_vector, broadcast_tree

ROOT = Path(__file__).resolve().parents[1]

class RoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.topology = json.loads((ROOT / "data" / "network.json").read_text(encoding="utf-8"))
        cls.graph = graph_from_topology(cls.topology)

    def test_dijkstra_core_server(self):
        result = dijkstra(self.graph, "CORE", "SERVER")
        self.assertTrue(result["reachable"])
        self.assertEqual(result["cost"], 1)
        self.assertEqual(result["path"], ["CORE", "SERVER"])

    def test_distance_vector_matches_dijkstra_cost(self):
        dv = distance_vector(self.graph, "CORE")
        for destination in self.graph:
            shortest = dijkstra(self.graph, "CORE", destination)
            self.assertEqual(dv["selected_table"][destination]["distance"], shortest["cost"])

    def test_broadcast_tree_reaches_all_nodes(self):
        tree = broadcast_tree(self.graph, "CORE")
        self.assertEqual(set(tree["visited"]), set(self.graph))
        self.assertEqual(tree["transmissions"], len(self.graph) - 1)

    def test_failed_core_server_link_uses_alternative(self):
        failed = graph_from_topology(self.topology, [["CORE", "SERVER"]])
        result = dijkstra(failed, "CORE", "SERVER")
        self.assertTrue(result["reachable"])
        self.assertGreater(result["cost"], 1)

if __name__ == "__main__":
    unittest.main()
