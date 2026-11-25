import math
import random
import networkx as nx


def normalize_edge(u, v):
    return tuple(sorted((u, v)))


def point_to_segment_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    len_sq = dx * dx + dy * dy
    if len_sq == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / len_sq))
    proj_x = ax + t * dx
    proj_y = ay + t * dy
    return math.hypot(px - proj_x, py - proj_y)


class EulerGraph:
    def __init__(self, level: int, width: int = 700, height: int = 520):
        self.level = level
        self.width = width
        self.height = height
        self.nodes_pos, self.edges_set, self.solution_path = self._generate_stage()

    def _is_layout_clean(self, nodes_pos, edges_set) -> bool:
        for w, (wx, wy) in nodes_pos.items():
            for u, v in edges_set:
                if w == u or w == v:
                    continue
                ux, uy = nodes_pos[u]
                vx, vy = nodes_pos[v]
                if point_to_segment_dist(wx, wy, ux, uy, vx, vy) < 32:
                    return False
        return True

    def _build_polygon_layout(self, num_nodes: int, edges_set: set) -> dict:
        cx, cy = self.width // 2, self.height // 2 + 20
        rx, ry = 230, 170
        use_center = num_nodes >= 6 and (num_nodes % 2 == 0)

        for _ in range(30):
            nodes_pos = {}
            order = list(range(num_nodes))
            random.shuffle(order)

            if use_center:
                outer_nodes = order[:-1]
                center_node = order[-1]
                nodes_pos[center_node] = (
                    cx + random.randint(-18, 18),
                    cy + random.randint(-15, 15),
                )
                step = (2 * math.pi) / len(outer_nodes)
                start_angle = random.uniform(0, 2 * math.pi)
                for i, node_id in enumerate(outer_nodes):
                    angle = start_angle + i * step
                    jitter = random.uniform(0.88, 1.02)
                    nodes_pos[node_id] = (
                        int(cx + math.cos(angle) * rx * jitter),
                        int(cy + math.sin(angle) * ry * jitter),
                    )
            else:
                step = (2 * math.pi) / num_nodes
                start_angle = random.uniform(0, 2 * math.pi)
                for i, node_id in enumerate(order):
                    angle = start_angle + i * step
                    jitter = random.uniform(0.85, 1.02)
                    nodes_pos[node_id] = (
                        int(cx + math.cos(angle) * rx * jitter),
                        int(cy + math.sin(angle) * ry * jitter),
                    )

            if self._is_layout_clean(nodes_pos, edges_set):
                return nodes_pos

        nodes_pos = {}
        step = (2 * math.pi) / num_nodes
        for i in range(num_nodes):
            angle = -math.pi / 2 + i * step
            nodes_pos[i] = (
                int(cx + math.cos(angle) * rx),
                int(cy + math.sin(angle) * ry),
            )
        return nodes_pos

    def _generate_stage(self):
        num_nodes = min(5 + (self.level - 1) // 3, 8)
        prob = min(0.50 + (self.level * 0.015), 0.65)

        attempts = 0
        while True:
            attempts += 1
            G = nx.erdos_renyi_graph(num_nodes, prob)
            if not nx.is_connected(G):
                continue

            odd_nodes = [v for v, d in G.degree() if d % 2 == 1]
            random.shuffle(odd_nodes)
            while len(odd_nodes) > 2:
                u = odd_nodes.pop()
                v = odd_nodes.pop()
                if G.has_edge(u, v):
                    G.remove_edge(u, v)
                else:
                    G.add_edge(u, v)

            if not (nx.is_connected(G) and nx.has_eulerian_path(G)):
                continue

            degrees = [d for _, d in G.degree()]
            if min(degrees) < 2:
                continue

            max_deg2 = 1 if attempts < 200 else 2
            if sum(1 for d in degrees if d == 2) > max_deg2:
                continue

            edges_set = {normalize_edge(u, v) for u, v in G.edges()}
            nodes_pos = self._build_polygon_layout(num_nodes, edges_set)

            start_node = odd_nodes[0] if odd_nodes else 0
            solution_path = list(nx.eulerian_path(G, source=start_node))

            return nodes_pos, edges_set, solution_path

    def get_remaining_degree(self, node_id: int, visited_edges: set) -> int:
        return sum(
            1
            for u, v in self.edges_set
            if node_id in (u, v) and (u, v) not in visited_edges
        )

    def compute_hint(self, current_node, visited_edges: set):
        remaining_edges = [e for e in self.edges_set if e not in visited_edges]
        if not remaining_edges:
            return None, None, True

        rem_G = nx.Graph()
        rem_G.add_edges_from(remaining_edges)

        if not nx.is_connected(rem_G):
            return None, None, False

        odd_nodes = [v for v, d in rem_G.degree() if d % 2 == 1]

        if current_node is None:
            start_node = odd_nodes[0] if odd_nodes else next(iter(rem_G.nodes()))
            path = list(nx.eulerian_path(rem_G, source=start_node))
            first_u, first_v = path[0]
            return first_u, normalize_edge(first_u, first_v), True
        else:
            if current_node not in rem_G:
                return None, None, False
            if len(odd_nodes) == 0 or (
                    len(odd_nodes) == 2 and current_node in odd_nodes
            ):
                path = list(nx.eulerian_path(rem_G, source=current_node))
                next_u, next_v = path[0]
                return next_v, normalize_edge(next_u, next_v), True
            return None, None, False
