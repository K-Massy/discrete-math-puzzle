import math
import random
import sys
import networkx as nx
import pygame

# --- 1. ゲーム設定と初期化 ---
pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 700, 520
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Eulerian Path Puzzle - Procedural Generation")
font_ui = pygame.font.SysFont(None, 30)
font_node = pygame.font.SysFont(None, 26)


def normalize_edge(u, v):
    return tuple(sorted((u, v)))


def point_to_segment_dist(px, py, ax, ay, bx, by):
    """点P と 線分AB の最短距離を計算する"""
    dx, dy = bx - ax, by - ay
    len_sq = dx * dx + dy * dy
    if len_sq == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / len_sq))
    proj_x = ax + t * dx
    proj_y = ay + t * dy
    return math.hypot(px - proj_x, py - proj_y)


def is_layout_clean(nodes_pos, edges_set):
    """頂点が無関係な辺の上に重なっていないか検証する"""
    node_ids = list(nodes_pos.keys())
    for w in node_ids:
        wx, wy = nodes_pos[w]
        for u, v in edges_set:
            if w == u or w == v:
                continue
            ux, uy = nodes_pos[u]
            vx, vy = nodes_pos[v]
            if point_to_segment_dist(wx, wy, ux, uy, vx, vy) < 32:
                return False
    return True


def build_polygon_layout(num_nodes, edges_set):
    """多角形（円周）ベースで見やすく重なりのない座標を高速生成する"""
    cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 15
    rx, ry = 230, 175  # 画面比率に合わせた楕円半径

    # 頂点数が6以上のときは「外周(N-1個) + 中心(1個)」のホイール配置も候補にする
    use_center = num_nodes >= 6 and (num_nodes % 2 == 0)

    for _ in range(30):
        nodes_pos = {}
        order = list(range(num_nodes))
        random.shuffle(order)

        if use_center:
            outer_nodes = order[:-1]
            center_node = order[-1]
            # 中心点はわずかにずらして対称線上の重なりを防ぐ
            nodes_pos[center_node] = (
                cx + random.randint(-18, 18),
                cy + random.randint(-15, 15),
            )
            step = (2 * math.pi) / len(outer_nodes)
            start_angle = random.uniform(0, 2 * math.pi)
            for i, node_id in enumerate(outer_nodes):
                angle = start_angle + i * step
                jitter = random.uniform(0.88, 1.02)
                x = cx + math.cos(angle) * rx * jitter
                y = cy + math.sin(angle) * ry * jitter
                nodes_pos[node_id] = (int(x), int(y))
        else:
            step = (2 * math.pi) / num_nodes
            start_angle = random.uniform(0, 2 * math.pi)
            for i, node_id in enumerate(order):
                angle = start_angle + i * step
                jitter = random.uniform(0.85, 1.02)
                x = cx + math.cos(angle) * rx * jitter
                y = cy + math.sin(angle) * ry * jitter
                nodes_pos[node_id] = (int(x), int(y))

        if is_layout_clean(nodes_pos, edges_set):
            return nodes_pos

    # 万が一すべての試行で重なった場合は、完全な正多角形で配置（100%重なりなし）
    nodes_pos = {}
    step = (2 * math.pi) / num_nodes
    for i in range(num_nodes):
        angle = -math.pi / 2 + i * step
        nodes_pos[i] = (
            int(cx + math.cos(angle) * rx),
            int(cy + math.sin(angle) * ry),
        )
    return nodes_pos


# --- 2. 離散数学による「美しい一筆書きグラフ」の高速自動生成 ---
def generate_eulerian_stage(level):
    # 頂点数は 5〜8 の範囲で段階的に増加（パズルとして見やすい上限に設定）
    num_nodes = min(5 + (level - 1) // 3, 8)
    prob = min(0.50 + (level * 0.015), 0.65)

    attempts = 0
    while True:
        attempts += 1
        G = nx.erdos_renyi_graph(num_nodes, prob)
        if not nx.is_connected(G):
            continue

        # 奇数次数の頂点をペアにして辺を調整し、オイラー路の条件を満たす
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
        min_deg = min(degrees)
        deg2_count = sum(1 for d in degrees if d == 2)

        # 条件1: 次数1（行き止まりの一本道）を禁止
        if min_deg < 2:
            continue

        # 条件2: 次数2（単なる折れ線）を最大1個までに制限（試行回数が多い場合は緩和）
        max_deg2 = 1 if attempts < 200 else 2
        if deg2_count > max_deg2:
            continue

        edges_set = {normalize_edge(u, v) for u, v in G.edges()}
        nodes_pos = build_polygon_layout(num_nodes, edges_set)
        return nodes_pos, edges_set


# --- 3. ゲーム状態管理 ---
level = 1
NODES, ALL_EDGES_SET = generate_eulerian_stage(level)


def reset_play_state():
    return [], set(), "PLAYING"


path_history, visited_edges, game_state = reset_play_state()


def get_remaining_degree(node_id, visited):
    return sum(
        1
        for u, v in ALL_EDGES_SET
        if node_id in (u, v) and (u, v) not in visited
    )


def check_game_state(current_node, visited):
    if len(visited) == len(ALL_EDGES_SET):
        return "CLEAR"
    if current_node is not None and get_remaining_degree(current_node, visited) == 0:
        return "STUCK"
    return "PLAYING"


# --- 4. メインループ ---
clock = pygame.time.Clock()
while True:
    screen.fill((30, 30, 40))
    current_node = path_history[-1] if path_history else None

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                path_history, visited_edges, game_state = reset_play_state()

            elif event.key == pygame.K_z and path_history:
                last_node = path_history.pop()
                if path_history:
                    prev_node = path_history[-1]
                    visited_edges.remove(normalize_edge(prev_node, last_node))
                new_current = path_history[-1] if path_history else None
                game_state = check_game_state(new_current, visited_edges)

            elif (event.key == pygame.K_SPACE and game_state == "CLEAR") or (
                    event.key == pygame.K_n
            ):
                if game_state == "CLEAR":
                    level += 1
                NODES, ALL_EDGES_SET = generate_eulerian_stage(level)
                path_history, visited_edges, game_state = reset_play_state()

        if event.type == pygame.MOUSEBUTTONDOWN and game_state == "PLAYING":
            mx, my = event.pos
            for node_id, (nx_pos, ny_pos) in NODES.items():
                if math.hypot(mx - nx_pos, my - ny_pos) <= 22:
                    if current_node is None:
                        path_history.append(node_id)
                    elif node_id != current_node:
                        edge = normalize_edge(current_node, node_id)
                        if edge in ALL_EDGES_SET and edge not in visited_edges:
                            visited_edges.add(edge)
                            path_history.append(node_id)
                            game_state = check_game_state(node_id, visited_edges)
                    break

    # --- 描画処理 ---
    for u, v in ALL_EDGES_SET:
        edge = (u, v)
        if edge in visited_edges:
            color, width = (50, 220, 100), 6
        elif current_node in edge and game_state == "PLAYING":
            color, width = (180, 180, 210), 4
        else:
            color, width = (90, 90, 110), 3
        pygame.draw.line(screen, color, NODES[u], NODES[v], width)

    for node_id, pos in NODES.items():
        rem_deg = get_remaining_degree(node_id, visited_edges)
        if node_id == current_node:
            color = (220, 60, 60) if game_state == "STUCK" else (255, 165, 0)
        elif rem_deg == 0:
            color = (80, 80, 95)
        else:
            color = (70, 180, 255)

        pygame.draw.circle(screen, color, pos, 20)
        deg_text = font_node.render(str(rem_deg), True, (255, 255, 255))
        screen.blit(deg_text, deg_text.get_rect(center=pos))

    if game_state == "CLEAR":
        msg = f"LEVEL {level} CLEAR!  Press [SPACE] for Next Stage"
        msg_color = (255, 255, 100)
    elif game_state == "STUCK":
        msg = f"STUCK!  [Z]: Undo  |  [R]: Retry Level {level}"
        msg_color = (255, 100, 100)
    else:
        msg = (
            f"LV.{level} | Edges: {len(visited_edges)}/{len(ALL_EDGES_SET)} | [Z]:"
            " Undo  [R]: Retry  [N]: New Map"
        )
        msg_color = (230, 230, 230)

    screen.blit(font_ui.render(msg, True, msg_color), (20, 20))

    pygame.display.flip()
    clock.tick(60)
