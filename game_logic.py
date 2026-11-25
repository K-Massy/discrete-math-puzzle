from graph_model import EulerGraph, normalize_edge

SCORE_EDGE_DRAW = 100
SCORE_CLEAR_BASE = 300
PENALTY_UNDO = 50
PENALTY_HINT = 150


class PuzzleGame:
    def __init__(self, width: int = 700, height: int = 520):
        self.width = width
        self.height = height
        self.level = 1
        self.score = 0
        self.stage_start_score = 0
        self.graph = EulerGraph(self.level, self.width, self.height)
        self.reset_stage_state()

    @property
    def current_node(self):
        return self.path_history[-1] if self.path_history else None

    def reset_stage_state(self):
        self.path_history = []
        self.visited_edges = set()
        self.state = "PLAYING"
        self.hint_node = None
        self.hint_edge = None
        self.hint_msg = ""
        self.score = self.stage_start_score

    def next_stage(self, advance_level: bool = True):
        if advance_level:
            self.level += 1
        self.stage_start_score = self.score
        self.graph = EulerGraph(self.level, self.width, self.height)
        self.reset_stage_state()

    def _clear_hint(self):
        self.hint_node = None
        self.hint_edge = None
        self.hint_msg = ""

    def select_node(self, node_id: int):
        if self.state != "PLAYING":
            return

        curr = self.current_node
        if curr is None:
            self.path_history.append(node_id)
            self._clear_hint()
        elif node_id != curr:
            edge = normalize_edge(curr, node_id)
            if edge in self.graph.edges_set and edge not in self.visited_edges:
                self.visited_edges.add(edge)
                self.path_history.append(node_id)
                self.score += SCORE_EDGE_DRAW
                self._clear_hint()
                self._update_game_state(node_id)

    def _update_game_state(self, current_node: int):
        if len(self.visited_edges) == len(self.graph.edges_set):
            self.state = "CLEAR"
            self.score += SCORE_CLEAR_BASE * self.level
        elif self.graph.get_remaining_degree(current_node, self.visited_edges) == 0:
            self.state = "STUCK"

    def undo(self):
        if self.state != "PLAYING" or not self.path_history:
            return

        last_node = self.path_history.pop()
        if self.path_history:
            prev_node = self.path_history[-1]
            self.visited_edges.remove(normalize_edge(prev_node, last_node))
            self.score = max(0, self.score - PENALTY_UNDO)
        self._clear_hint()

    def request_hint(self):
        if self.state != "PLAYING":
            return

        if self.hint_msg == "":
            self.score = max(0, self.score - PENALTY_HINT)

        h_node, h_edge, solvable = self.graph.compute_hint(
            self.current_node, self.visited_edges
        )
        if solvable:
            self.hint_node, self.hint_edge = h_node, h_edge
            self.hint_msg = (
                f"HINT (-{PENALTY_HINT}pt): Start from the highlighted node!"
                if self.current_node is None
                else f"HINT (-{PENALTY_HINT}pt): Follow the cyan edge!"
            )
        else:
            self.hint_node, self.hint_edge = None, None
            self.hint_msg = "HINT: Dead end ahead! Press [Z] to Undo."
