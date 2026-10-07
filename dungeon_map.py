"""Seeded, orthogonal dungeon layouts with branches, loops and terminal rooms."""

from collections import deque


# Screen coordinates: north decreases y. This order also defines door indices.
CARDINAL_DIRECTIONS = ((0, -1), (1, 0), (0, 1), (-1, 0))


def neighbors(key):
    x, y = key
    return [(x + dx, y + dy) for dx, dy in CARDINAL_DIRECTIONS]


def distances(connections, start=(0, 0)):
    """Shortest door count from the entrance, independent of insertion order."""
    result = {start: 0}
    queue = deque([start])
    while queue:
        key = queue.popleft()
        for neighbor in neighbors(key):
            if neighbor in connections[key] and neighbor not in result:
                result[neighbor] = result[key] + 1
                queue.append(neighbor)
    return result


def generate_layout(rng, room_count):
    """Return adjacency, BFS depths and the final room's coordinate.

    A small randomly oriented loop guarantees two entrance choices. A growing
    frontier adds winding passages and side branches; occasional extra doors
    make shortcuts. Two terminal rooms are added last, protecting a side dead
    end and ensuring that the boss can never block access to another room.
    """
    if room_count < 10:
        raise ValueError("A dungeon needs at least ten rooms")
    connections = {(0, 0): set()}

    def connect(first, second):
        connections.setdefault(first, set()).add(second)
        connections.setdefault(second, set()).add(first)

    first = rng.randrange(4)
    dx, dy = CARDINAL_DIRECTIONS[first]
    ex, ey = CARDINAL_DIRECTIONS[(first + rng.choice((-1, 1))) % 4]
    corner = (dx + ex, dy + ey)
    connect((0, 0), (dx, dy))
    connect((dx, dy), corner)
    connect(corner, (ex, ey))
    connect((ex, ey), (0, 0))
    tip = corner

    while len(connections) < room_count - 2:
        frontier = [(key, candidate) for key in sorted(connections)
                    for candidate in neighbors(key) if candidate not in connections]
        continuation = [edge for edge in frontier if edge[0] == tip]
        source, target = rng.choice(continuation if continuation and rng.random() < .55 else frontier)
        connect(source, target)
        tip = target
        # Adjacent rooms are not automatically connected: walls remain useful.
        for adjacent in neighbors(target):
            if adjacent in connections and adjacent != source and rng.random() < .16:
                connect(target, adjacent)

    # An optional dead end is deliberately left outside the boss route.
    frontier = [(key, candidate) for key in sorted(connections)
                for candidate in neighbors(key) if candidate not in connections]
    source, side_room = rng.choice(frontier)
    connect(source, side_room)

    depth = distances(connections)
    frontier = [(key, candidate) for key in sorted(connections) if key != side_room
                for candidate in neighbors(key) if candidate not in connections]
    farthest = max(depth[key] for key, _ in frontier)
    source, boss = rng.choice([edge for edge in frontier if depth[edge[0]] == farthest])
    connect(source, boss)
    return connections, distances(connections), boss
