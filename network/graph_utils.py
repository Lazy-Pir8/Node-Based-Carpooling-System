from .models import Node, Edge
from collections import defaultdict, deque

def bfs_path(start_node, end_node):

    queue = deque([start_node])
    visited = {start_node }
    parent = {start_node: None}

    while queue:
        current = queue.popleft()

        if current == end_node:
            break

        neighbors = Edge.objects.filter(from_node=current)

        for edge in neighbors:
            neighbor = edge.to_node
            
            if neighbor not in visited:
                visited.add(neighbor)
                parent[neighbor] = current
                queue.append(neighbor)

    path = []
    node = end_node

    while node is not None:
        path.append(node)
        node = parent[node]

    path.reverse()
    return path