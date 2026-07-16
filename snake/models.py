from enum import Enum
import random

class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

    def is_opposite(self, other):
        return (self.value[0] + other.value[0] == 0) and (self.value[1] + other.value[1] == 0)

class Snake:
    def __init__(self, start_pos, grid_size):
        self.grid_size = grid_size
        self.body = [start_pos]
        self.direction = Direction.RIGHT
        self.next_direction = Direction.RIGHT
        self.grow_pending = False

    def change_direction(self, new_dir):
        # We check self.direction (current movement direction) to prevent turning 180 degrees
        if not new_dir.is_opposite(self.direction):
            self.next_direction = new_dir

    def move(self):
        # Apply the validated direction change
        self.direction = self.next_direction
        head_x, head_y = self.body[0]
        dx, dy = self.direction.value

        # Wall-wrapping logic
        new_head = ((head_x + dx) % self.grid_size[0], (head_y + dy) % self.grid_size[1])

        self.body.insert(0, new_head)
        if not self.grow_pending:
            self.body.pop()
        else:
            self.grow_pending = False

    def grow(self):
        self.grow_pending = True

    def check_self_collision(self):
        # Collision with own body (excluding head)
        return self.body[0] in self.body[1:]

    def check_obstacle_collision(self, obstacles):
        return self.body[0] in obstacles

class Food:
    def __init__(self, grid_size):
        self.grid_size = grid_size
        self.position = (0, 0)

    def spawn(self, snake_body, obstacles):
        # Find all available spots on the grid to avoid spawning inside snake or obstacles
        width, height = self.grid_size
        all_spots = {(x, y) for x in range(width) for y in range(height)}
        occupied = set(snake_body).union(set(obstacles))
        available = list(all_spots - occupied)

        if available:
            self.position = random.choice(available)
            return True
        return False  # Screen is full (win condition/edge case)

# Define Levels with speed, target score to advance, and obstacle coordinate maps
# Grids are assumed to be 40x30 for optimal gameplay (800x600 with 20px cells)
LEVEL_CONFIGS = {
    1: {
        "speed": 8,
        "target_score": 10,
        "obstacles": []
    },
    2: {
        "speed": 10,
        "target_score": 25,
        "obstacles": [
            # Corner blocks
            (5, 5), (5, 6), (6, 5), (6, 6),
            (34, 5), (34, 6), (33, 5), (33, 6),
            (5, 24), (5, 23), (6, 24), (6, 23),
            (34, 24), (34, 23), (33, 24), (33, 23)
        ]
    },
    3: {
        "speed": 12,
        "target_score": 45,
        "obstacles": [
            # Two vertical walls with gap
            (10, y) for y in range(5, 12)
        ] + [
            (10, y) for y in range(18, 25)
        ] + [
            (30, y) for y in range(5, 12)
        ] + [
            (30, y) for y in range(18, 25)
        ]
    },
    4: {
        "speed": 14,
        "target_score": 70,
        "obstacles": [
            # Large central cross with a center gap
            (x, 15) for x in range(8, 18)
        ] + [
            (x, 15) for x in range(22, 32)
        ] + [
            (20, y) for y in range(5, 13)
        ] + [
            (20, y) for y in range(17, 25)
        ]
    },
    5: {
        "speed": 16,
        "target_score": 999,  # Infinite / Max level
        "obstacles": [
            # Complex maze structure
            (x, 5) for x in range(5, 35, 2)
        ] + [
            (x, 24) for x in range(5, 35, 2)
        ] + [
            (5, y) for y in range(5, 25, 2)
        ] + [
            (34, y) for y in range(5, 25, 2)
        ]
    }
}
