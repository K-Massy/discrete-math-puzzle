import math
import sys
import pygame

# --- 1. グラフデータの定義 ---
NODES = {
    0: (200, 160),
    1: (400, 160),
    2: (400, 360),
    3: (200, 360),
    4: (300, 90),
}

EDGES = [(0, 1), (1, 2), (2, 3), (3, 0), (0, 2), (1, 3), (0, 4), (1, 4)]

# --- 2. ゲームの初期化 ---
pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 600, 460
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Eulerian Path Puzzle - Enhanced")
font_ui = pygame.font.SysFont(None, 32)
font_node = pygame.font.SysFont(None, 26)


def normalize_edge(u, v):
    return tuple(sorted((u, v)))


# 全辺の正規化済みセットをあらかじめ作っておく
ALL_EDGES_SET = {normalize_edge(u, v) for u, v in EDGES}


def reset_game():
    # path_history: 訪れた頂点の履歴リスト（スタックとして使う）
    return [], set(), "PLAYING"


path_history, visited_edges, game_state = reset_game()


# --- 離散数学ロジックのヘルパー関数 ---
def get_remaining_degree(node_id, visited):
    """指定した頂点に接続している『未通過の辺』の本数（残次数）を返す"""
    count = 0
    for u, v in ALL_EDGES_SET:
        if node_id in (u, v) and (u, v) not in visited:
            count += 1
    return count


def check_game_state(current_node, visited):
    """現在の盤面が『クリア』『手詰まり』『プレイ中』のどれかを判定"""
    if len(visited) == len(ALL_EDGES_SET):
        return "CLEAR"
    if current_node is not None and get_remaining_degree(current_node, visited) == 0:
        return "STUCK"
    return "PLAYING"


# --- 3. メインループ ---
clock = pygame.time.Clock()
while True:
    screen.fill((30, 30, 40))
    current_node = path_history[-1] if path_history else None

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        # キーボード操作（R: リセット / Z: 1手戻る）
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                path_history, visited_edges, game_state = reset_game()

            elif event.key == pygame.K_z and path_history:
                # 履歴から最新の頂点を取り除く（ポップ）
                last_node = path_history.pop()
                if path_history:
                    # 1つ前の頂点との間の辺を未通過に戻す
                    prev_node = path_history[-1]
                    visited_edges.remove(normalize_edge(prev_node, last_node))
                # 状態を再判定（STUCKから復帰できるようにする）
                new_current = path_history[-1] if path_history else None
                game_state = check_game_state(new_current, visited_edges)

        # マウスクリック操作（プレイ中のみ有効）
        if event.type == pygame.MOUSEBUTTONDOWN and game_state == "PLAYING":
            mx, my = event.pos
            for node_id, (nx, ny) in NODES.items():
                if math.hypot(mx - nx, my - ny) <= 22:
                    if current_node is None:
                        # 最初の頂点を選択
                        path_history.append(node_id)
                    elif node_id != current_node:
                        edge = normalize_edge(current_node, node_id)
                        if edge in ALL_EDGES_SET and edge not in visited_edges:
                            visited_edges.add(edge)
                            path_history.append(node_id)
                            game_state = check_game_state(node_id, visited_edges)
                    break

    # --- 描画処理 ---
    # 1. 辺（エッジ）の描画
    for u, v in ALL_EDGES_SET:
        edge = (u, v)
        if edge in visited_edges:
            color, width = (50, 220, 100), 6
        elif current_node in edge and game_state == "PLAYING":
            # 現在地から次に移動できる辺を少し明るくハイライト
            color, width = (180, 180, 210), 4
        else:
            color, width = (90, 90, 110), 3
        pygame.draw.line(screen, color, NODES[u], NODES[v], width)

    # 2. 頂点（ノード）と「残次数」の描画
    for node_id, pos in NODES.items():
        rem_deg = get_remaining_degree(node_id, visited_edges)

        if node_id == current_node:
            color = (220, 60, 60) if game_state == "STUCK" else (255, 165, 0)
        elif rem_deg == 0:
            color = (80, 80, 95)  # すべての辺を使い切った頂点は暗くする
        else:
            color = (70, 180, 255)

        pygame.draw.circle(screen, color, pos, 20)

        # 頂点の中央に「残次数」を表示
        deg_text = font_node.render(str(rem_deg), True, (255, 255, 255))
        text_rect = deg_text.get_rect(center=pos)
        screen.blit(deg_text, text_rect)

    # 3. ステータスUIの描画
    if game_state == "CLEAR":
        msg, msg_color = "CLEAR! Press 'R' to Reset", (255, 255, 100)
    elif game_state == "STUCK":
        msg, msg_color = "STUCK! Press 'Z' to Undo or 'R' to Reset", (255, 100, 100)
    else:
        msg = (
            f"Edges: {len(visited_edges)}/{len(ALL_EDGES_SET)}  |  [Z]: Undo  [R]:"
            " Reset"
        )
        msg_color = (230, 230, 230)

    screen.blit(font_ui.render(msg, True, msg_color), (20, 20))

    pygame.display.flip()
    clock.tick(60)
