import pygame
import numpy as np

# Расчет расстояния между двумя точками
def dist(A, B):
    return np.sqrt((A[0] - B[0]) ** 2 + (A[1] - B[1]) ** 2)

# Функция для поиска соседей точки
def region_query(points, point_idx, eps):
    neighbors = []
    for i in range(len(points)):
        if dist(points[point_idx], points[i]) <= eps:
            neighbors.append(i)
    return neighbors

# Расширение кластера с промежуточной классификацией
def expand_cluster(points, labels, colors, point_idx, cluster_id, eps, min_pts):
    neighbors = region_query(points, point_idx, eps)
    if len(neighbors) < min_pts:
        labels[point_idx] = -1  # Шумовая точка
        colors[point_idx] = "noise"  # Красный
        return False
    else:
        labels[point_idx] = cluster_id
        colors[point_idx] = "core"  # Зеленый (ключевая точка)
        for neighbor_idx in neighbors:
            if labels[neighbor_idx] == -1:  # Если ранее была шумовой точкой, обновляем
                labels[neighbor_idx] = cluster_id
                colors[neighbor_idx] = "border"  # Желтый
            elif labels[neighbor_idx] == 0:  # Если точка еще не обработана
                labels[neighbor_idx] = cluster_id
                colors[neighbor_idx] = "core"  # Зеленый
                new_neighbors = region_query(points, neighbor_idx, eps)
                if len(new_neighbors) >= min_pts:
                    neighbors.extend(new_neighbors)
        return True

# Алгоритм DBSCAN с промежуточной классификацией
def dbscan_with_classification(points, eps, min_pts):
    labels = [0] * len(points)  # 0 означает, что точка не обработана
    colors = ["unclassified"] * len(points)  # Цвета для точек
    cluster_id = 0
    for i in range(len(points)):
        if labels[i] == 0:  # Если точка не обработана
            if expand_cluster(points, labels, colors, i, cluster_id + 1, eps, min_pts):
                cluster_id += 1
    return labels, colors

# Функция для генерации дополнительных точек рядом с местом клика
def brush(pos):
    near_points = []
    for i in range(np.random.randint(1, 7)):
        x = pos[0] + np.random.randint(-20, 20)
        y = pos[1] + np.random.randint(-20, 20)
        near_points.append((x, y))
    return near_points

# Параметры
epsilon = 30
min_pts = 5
radius = 3
points = []
pygame.init()
screen = pygame.display.set_mode((600, 400), pygame.RESIZABLE)
screen.fill("#FFFFFF")
pygame.display.update()
is_pressed = False
labels = []
colors = []
point_colors = []  # Список цветов для точек (по индексу)

# Цветовая схема
color_mapping = {
    "core": (0, 255, 0),      # Зеленый
    "border": (255, 255, 0),  # Желтый
    "noise": (255, 0, 0),     # Красный
    "unclassified": (0, 0, 0)  # Черный
}

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        if event.type == pygame.WINDOWRESIZED:
            screen.fill("#FFFFFF")
            for i in range(len(points)):
                pygame.draw.circle(screen, point_colors[i], points[i], radius)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                is_pressed = True
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                is_pressed = False

        if event.type == pygame.MOUSEMOTION and is_pressed:
            pos = event.pos
            if len(points) == 0 or dist(pos, points[-1]) > 20:
                # Генерируем точки рядом с кликом
                near_points = brush(pos)
                for point in near_points:
                    points.append(point)
                    point_colors.append(color_mapping["unclassified"])
                    pygame.draw.circle(screen, color_mapping["unclassified"], point, radius)
                # Добавляем основную точку
                points.append(pos)
                point_colors.append(color_mapping["unclassified"])
                pygame.draw.circle(screen, color_mapping["unclassified"], pos, radius)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:  # Промежуточная классификация
                _, colors = dbscan_with_classification(points, epsilon, min_pts)
                for i in range(len(points)):
                    point_colors[i] = color_mapping[colors[i]]
                    pygame.draw.circle(screen, point_colors[i], points[i], radius)
            if event.key == pygame.K_SPACE:  # Окончательная кластеризация
                labels, colors = dbscan_with_classification(points, epsilon, min_pts)
                unique_clusters = set(labels) - {-1}
                cluster_colors = [(np.random.randint(0, 255), np.random.randint(0, 255), np.random.randint(0, 255)) for _ in unique_clusters]
                cluster_colors.append((255, 0, 0))  # Красный для шума
                cluster_color_map = {cluster_id: cluster_colors[i] for i, cluster_id in enumerate(unique_clusters)}
                for i in range(len(points)):
                    if labels[i] == -1:  # Шумовая точка
                        point_colors[i] = color_mapping["noise"]
                    else:
                        point_colors[i] = cluster_color_map[labels[i]]
                    pygame.draw.circle(screen, point_colors[i], points[i], radius)
            if event.key == pygame.K_ESCAPE:  # Очистка экрана
                points = []
                point_colors = []
                labels = []
                colors = []
                screen.fill("#FFFFFF")
        pygame.display.flip()
