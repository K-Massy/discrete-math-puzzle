import math
import pygame
import sys

# --- 1. グラフデータの定義（離散数学のモデル部分） ---
# 頂点(ノード)の座標 {頂点ID: (x, y)}
NODES = {
    0: (200, 150),
    1: (400, 150),
    2: (400, 350),
    3: (200, 350),
    4: (300, 80),  # 屋根の頂点（家の形をしたグラフ）
}

# 辺(エッジ)のリスト [(始点, 終点), ...] ※無向グラフとして扱う
EDGES = [(0, 1), (1, 2), (2, 3), (3, 0), (0, 2), (1, 3), (0, 4), (1, 4)]

# --- 2. ゲームの初期化 ---
pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 600, 450
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Eulerian Path Puzzle (一筆書きパズル)")
font = pygame.font.SysFont(None, 36)


def reset_game():
    return None, set(), False  # 現在地, 通過済みの辺の集合, クリアフラグ


current_node, visited_edges, is_cleared = reset_game()


# 辺を正規化（(0, 1) と (1, 0) を同じ無向辺として扱うため）
def normalize_edge(u, v):
    return tuple(sorted((u, v)))


# --- 3. メインループ（描画と入力処理） ---
clock = pygame.time.Clock()
while True:
    screen.fill((30, 30, 40))  # 背景色（ダークグレー）

    # イベント処理（クリックや終了など）
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        # Rキーでリセット
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            current_node, visited_edges, is_cleared = reset_game()

        # マウスクリック処理
        if event.type == pygame.MOUSEBUTTONDOWN and not is_cleared:
            mx, my = event.pos
            # どの頂点がクリックされたか判定
            for node_id, (nx, ny) in NODES.items():
                if math.hypot(mx - nx, my - ny) <= 20:  # 半径20px以内ならヒット
                    if current_node is None:
                        # 最初の頂点を選択
                        current_node = node_id
                    elif node_id != current_node:
                        edge = normalize_edge(current_node, node_id)
                        # 辺が存在し、かつまだ通っていない場合のみ移動可能
                        if edge in [
                            normalize_edge(u, v) for u, v in EDGES
                        ] and edge not in visited_edges:
                            visited_edges.add(edge)
                            current_node = node_id
                            # すべての辺を通過したらクリア！
                            if len(visited_edges) == len(EDGES):
                                is_cleared = True
                    break

    # 辺（エッジ）の描画
    for u, v in EDGES:
        edge = normalize_edge(u, v)
        color = (50, 220, 100) if edge in visited_edges else (120, 120, 140)
        width = 6 if edge in visited_edges else 3
        pygame.draw.line(screen, color, NODES[u], NODES[v], width)

    # 頂点（ノード）の描画
    for node_id, pos in NODES.items():
        # 現在地の頂点はオレンジ、それ以外は水色
        color = (255, 165, 0) if node_id == current_node else (70, 180, 255)
        pygame.draw.circle(screen, color, pos, 18)

    # UIテキストの描画
    if is_cleared:
        text = font.render("CLEAR! Press 'R' to Reset", True, (255, 255, 100))
    else:
        text = font.render(
            f"Edges: {len(visited_edges)}/{len(EDGES)} (Press 'R' to Reset)",
            True,
            (255, 255, 255),
        )
    screen.blit(text, (20, 20))

    pygame.display.flip()
    clock.tick(60)
