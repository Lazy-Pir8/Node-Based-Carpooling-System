from collections import deque
from .models import Edge


def bfs_path(start_node, end_node):
    """BFS shortest path from start_node to end_node. Returns [] if unreachable."""
    if start_node == end_node:
        return [start_node]

    queue = deque([start_node])
    visited = {start_node}
    parent = {start_node: None}

    while queue:
        current = queue.popleft()
        if current == end_node:
            break
        for edge in Edge.objects.filter(from_node=current).select_related('to_node'):
            neighbor = edge.to_node
            if neighbor not in visited:
                visited.add(neighbor)
                parent[neighbor] = current
                queue.append(neighbor)

    if end_node not in parent:
        return []  # No path found

    path = []
    node = end_node
    while node is not None:
        path.append(node)
        node = parent[node]
    path.reverse()
    return path


def nodes_within_distance(center_node, max_distance=2):
    """Return set of nodes reachable within max_distance hops from center_node."""
    visited = {center_node: 0}
    queue = deque([center_node])
    while queue:
        current = queue.popleft()
        if visited[current] >= max_distance:
            continue
        for edge in Edge.objects.filter(from_node=current).select_related('to_node'):
            neighbor = edge.to_node
            if neighbor not in visited:
                visited[neighbor] = visited[current] + 1
                queue.append(neighbor)
    return set(visited.keys())
