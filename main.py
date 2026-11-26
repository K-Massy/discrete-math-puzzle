import math
import sys
import pygame
from game_logic import PuzzleGame, SCORE_CLEAR_BASE
from graph_model import EulerGraph

SCREEN_WIDTH, SCREEN_HEIGHT = 700, 520
FPS = 60

COLOR_BG = (30, 30, 40)
COLOR_EDGE_DEFAULT = (90, 90, 110)
COLOR_EDGE_ACTIVE = (180, 180, 210)
COLOR_EDGE_VISITED = (50, 220, 100)
COLOR_EDGE_HINT = (0, 240, 255)
COLOR_NODE_DEFAULT = (70, 180, 255)
COLOR_NODE_CURRENT = (255, 165, 0)
COLOR_NODE_STUCK = (220, 60, 60)
COLOR_NODE_DONE = (80, 80, 95)
COLOR_GOLD = (255, 215, 0)


class PuzzleRenderer:
    """PuzzleGameの状態を受け取り、Pygameの画面へ描画するクラス。"""

    def __init__(self, screen: pygame.Surface):
        """描画用のスクリーンと各種フォントを初期化する。"""
        self.screen = screen
        self.font_ui = pygame.font.SysFont(None, 26)
        self.font_score = pygame.font.SysFont(None, 30)
        self.font_node = pygame.font.SysFont(None, 26)
        self.font_step = pygame.font.SysFont(None, 20)

    def draw(self, game: PuzzleGame):
        """背景・辺・正解ルート・頂点・UIテキストの順に画面全体を描画する。"""
        self.screen.fill(COLOR_BG)
        self._draw_edges(game)
        if game.state == "STUCK":
            self._draw_solution_overlay(game.graph)
        self._draw_nodes(game)
        self._draw_ui(game)

    def _draw_edges(self, game: PuzzleGame):
        """すべての辺を状態（ヒント・訪問済み・移動可能・未訪問）に応じた色と太さで描画する。"""
        curr = game.current_node
        for u, v in game.graph.edges_set:
            edge = (u, v)
            if edge == game.hint_edge:
                color, width = COLOR_EDGE_HINT, 7
            elif edge in game.visited_edges:
                color, width = COLOR_EDGE_VISITED, 6
            elif curr in edge and game.state == "PLAYING":
                color, width = COLOR_EDGE_ACTIVE, 4
            else:
                color, width = COLOR_EDGE_DEFAULT, 3
            pygame.draw.line(
                self.screen,
                color,
                game.graph.nodes_pos[u],
                game.graph.nodes_pos[v],
                width,
            )

    def _draw_solution_overlay(self, graph: EulerGraph):
        """手詰まり時に、正解ルートの進行方向を示す矢印と手順番号を描画する。"""
        for step_idx, (u, v) in enumerate(graph.solution_path, start=1):
            x1, y1 = graph.nodes_pos[u]
            x2, y2 = graph.nodes_pos[v]

            # 辺の終点手前に進行方向の矢印を描画する
            angle = math.atan2(y2 - y1, x2 - x1)
            arrow_x = x2 - math.cos(angle) * 28
            arrow_y = y2 - math.sin(angle) * 28
            arrow_size = 10
            p1 = (
                arrow_x - arrow_size * math.cos(angle - math.pi / 6),
                arrow_y - arrow_size * math.sin(angle - math.pi / 6),
            )
            p2 = (
                arrow_x - arrow_size * math.cos(angle + math.pi / 6),
                arrow_y - arrow_size * math.sin(angle + math.pi / 6),
            )
            pygame.draw.polygon(self.screen, COLOR_GOLD, [(arrow_x, arrow_y), p1, p2])

            # 辺の中点に手順番号バッジを描画する
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            pygame.draw.circle(self.screen, (40, 40, 55), (int(mx), int(my)), 11)
            pygame.draw.circle(self.screen, COLOR_GOLD, (int(mx), int(my)), 11, 2)
            num_surf = self.font_step.render(str(step_idx), True, (255, 230, 100))
            self.screen.blit(num_surf, num_surf.get_rect(center=(int(mx), int(my))))

    def _draw_nodes(self, game: PuzzleGame):
        """各頂点の円・外周ハイライト（ヒント／正解始点）・残り次数の数字を描画する。"""
        curr = game.current_node
        sol_start_node = (
            game.graph.solution_path[0][0] if game.graph.solution_path else None
        )

        for node_id, pos in game.graph.nodes_pos.items():
            rem_deg = game.graph.get_remaining_degree(node_id, game.visited_edges)
            if node_id == curr:
                color = COLOR_NODE_STUCK if game.state == "STUCK" else COLOR_NODE_CURRENT
            elif rem_deg == 0:
                color = COLOR_NODE_DONE
            else:
                color = COLOR_NODE_DEFAULT

            if game.state == "STUCK" and node_id == sol_start_node:
                pygame.draw.circle(self.screen, COLOR_GOLD, pos, 25)
            elif node_id == game.hint_node:
                pygame.draw.circle(self.screen, COLOR_EDGE_HINT, pos, 25)

            pygame.draw.circle(self.screen, color, pos, 20)
            deg_text = self.font_node.render(str(rem_deg), True, (255, 255, 255))
            self.screen.blit(deg_text, deg_text.get_rect(center=pos))

    def _draw_ui(self, game: PuzzleGame):
        """画面上部のステータス・スコア表示、および画面下部のヒントメッセージを描画する。"""
        if game.state == "CLEAR":
            bonus = SCORE_CLEAR_BASE * game.level
            msg = f"LEVEL {game.level} CLEAR! (+{bonus}pt)  Press [SPACE] for Next"
            msg_color = (255, 255, 100)
        elif game.state == "STUCK":
            msg = f"STUCK! Solution shown (Start: Gold) | [R]: Retry LV.{game.level}"
            msg_color = (255, 120, 120)
        else:
            msg = (
                f"LV.{game.level} | Edges: {len(game.visited_edges)}/{len(game.graph.edges_set)} | "
                "[H]: Hint  [Z]: Undo  [R]: Retry  [N]: New"
            )
            msg_color = (230, 230, 230)

        self.screen.blit(self.font_ui.render(msg, True, msg_color), (20, 16))

        score_surf = self.font_score.render(f"SCORE: {game.score}", True, (120, 255, 180))
        self.screen.blit(score_surf, (20, 44))

        if game.hint_msg and game.state == "PLAYING":
            hint_surf = self.font_ui.render(game.hint_msg, True, COLOR_EDGE_HINT)
            self.screen.blit(hint_surf, (20, SCREEN_HEIGHT - 36))


def main():
    """Pygameの初期化とメインゲームループ（入力処理・更新・描画）を実行する。"""
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Eulerian Path Puzzle")
    clock = pygame.time.Clock()

    game = PuzzleGame(SCREEN_WIDTH, SCREEN_HEIGHT)
    renderer = PuzzleRenderer(screen)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    game.reset_stage_state()
                elif event.key == pygame.K_z:
                    game.undo()
                elif event.key == pygame.K_h:
                    game.request_hint()
                elif event.key == pygame.K_SPACE and game.state == "CLEAR":
                    game.next_stage(advance_level=True)
                elif event.key == pygame.K_n and game.state == "PLAYING":
                    game.next_stage(advance_level=False)

            if event.type == pygame.MOUSEBUTTONDOWN and game.state == "PLAYING":
                mx, my = event.pos
                for node_id, (nx_pos, ny_pos) in game.graph.nodes_pos.items():
                    if math.hypot(mx - nx_pos, my - ny_pos) <= 22:
                        game.select_node(node_id)
                        break

        renderer.draw(game)
        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()
