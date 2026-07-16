import unittest
from snake.models import Direction, Snake, Food, LEVEL_CONFIGS
from snake.game import Game

class TestSnakeGame(unittest.TestCase):
    def setUp(self):
        self.grid_size = (10, 10)

    def test_direction_is_opposite(self):
        self.assertTrue(Direction.UP.is_opposite(Direction.DOWN))
        self.assertTrue(Direction.DOWN.is_opposite(Direction.UP))
        self.assertTrue(Direction.LEFT.is_opposite(Direction.RIGHT))
        self.assertTrue(Direction.RIGHT.is_opposite(Direction.LEFT))

        self.assertFalse(Direction.UP.is_opposite(Direction.LEFT))
        self.assertFalse(Direction.UP.is_opposite(Direction.UP))

    def test_snake_initial_state(self):
        snake = Snake((5, 5), self.grid_size)
        self.assertEqual(len(snake.body), 1)
        self.assertEqual(snake.body[0], (5, 5))
        self.assertEqual(snake.direction, Direction.RIGHT)

    def test_snake_movement_no_grow(self):
        snake = Snake((5, 5), self.grid_size)
        snake.move()
        self.assertEqual(len(snake.body), 1)
        self.assertEqual(snake.body[0], (6, 5))

    def test_snake_movement_and_wrapping(self):
        # Wrap right
        snake = Snake((9, 5), self.grid_size)
        snake.direction = Direction.RIGHT
        snake.next_direction = Direction.RIGHT
        snake.move()
        self.assertEqual(snake.body[0], (0, 5))

        # Wrap left
        snake = Snake((0, 5), self.grid_size)
        snake.direction = Direction.LEFT
        snake.next_direction = Direction.LEFT
        snake.move()
        self.assertEqual(snake.body[0], (9, 5))

        # Wrap up
        snake = Snake((5, 0), self.grid_size)
        snake.direction = Direction.UP
        snake.next_direction = Direction.UP
        snake.move()
        self.assertEqual(snake.body[0], (5, 9))

        # Wrap down
        snake = Snake((5, 9), self.grid_size)
        snake.direction = Direction.DOWN
        snake.next_direction = Direction.DOWN
        snake.move()
        self.assertEqual(snake.body[0], (5, 0))

    def test_snake_direction_change_valid(self):
        snake = Snake((5, 5), self.grid_size)
        snake.change_direction(Direction.UP)
        snake.move()
        self.assertEqual(snake.direction, Direction.UP)
        self.assertEqual(snake.body[0], (5, 4))

    def test_snake_direction_change_invalid_reversal(self):
        snake = Snake((5, 5), self.grid_size)
        # Attempt turning 180 degrees immediately
        snake.change_direction(Direction.LEFT)
        snake.move()
        # Snake should ignore the change and continue RIGHT
        self.assertEqual(snake.direction, Direction.RIGHT)
        self.assertEqual(snake.body[0], (6, 5))

    def test_snake_growth(self):
        snake = Snake((5, 5), self.grid_size)
        snake.grow()
        snake.move()
        self.assertEqual(len(snake.body), 2)
        self.assertEqual(snake.body[0], (6, 5))
        self.assertEqual(snake.body[1], (5, 5))

    def test_snake_self_collision(self):
        snake = Snake((5, 5), self.grid_size)
        # Grow to length 5
        for _ in range(4):
            snake.grow()
            snake.move()

        self.assertEqual(len(snake.body), 5)
        # Body segments are now [(9, 5), (8, 5), (7, 5), (6, 5), (5, 5)]
        # Force a self-intersection by wrapping/looping:
        # Move down, then left, then up to hit segment (8, 5)
        snake.change_direction(Direction.DOWN)
        snake.move()
        snake.change_direction(Direction.LEFT)
        snake.move()
        snake.change_direction(Direction.UP)
        snake.move()

        self.assertTrue(snake.check_self_collision())

    def test_obstacle_collision(self):
        snake = Snake((5, 5), self.grid_size)
        obstacles = [(6, 5), (6, 6)]
        snake.move() # moves to (6, 5)
        self.assertTrue(snake.check_obstacle_collision(obstacles))

    def test_food_spawn_safe(self):
        food = Food(self.grid_size)
        snake_body = [(0, 0), (0, 1), (0, 2)]
        obstacles = [(1, 1)]
        spawn_success = food.spawn(snake_body, obstacles)
        self.assertTrue(spawn_success)
        self.assertNotIn(food.position, snake_body)
        self.assertNotIn(food.position, obstacles)

    def test_game_headless_logic_reset(self):
        # Test Game logic state without invoking Pygame (as init_pygame is lazy)
        game = Game()
        self.assertEqual(game.level, 1)
        self.assertEqual(game.score, 0)
        self.assertEqual(len(game.snake.body), 1)
        self.assertFalse(game.state_game_over)
        self.assertFalse(game.state_paused)

    def test_game_level_progression(self):
        game = Game()
        # Set start screen to False so update runs
        game.state_start_screen = False
        # Mock target score update trigger
        game.score = 9
        # Snake moves over food, grows and hits level 1 target (10 points)
        game.food.position = (game.snake.body[0][0] + 1, game.snake.body[0][1])
        game.update()

        # After update: score increases by 5, level increases to 2
        self.assertEqual(game.score, 14)
        self.assertEqual(game.level, 2)
        # Obstacles should now be loaded from Level 2 configuration
        self.assertEqual(game.obstacles, LEVEL_CONFIGS[2]["obstacles"])
        self.assertEqual(game.speed, LEVEL_CONFIGS[2]["speed"])
