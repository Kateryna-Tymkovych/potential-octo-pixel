import os
import json
import sys
import pygame
from .models import Snake, Food, Direction, LEVEL_CONFIGS

# Colors
COLOR_BG = (15, 15, 25)          # Dark Slate Blue
COLOR_GRID = (25, 25, 35)        # Slightly lighter for subtle grid lines
COLOR_HUD_BG = (10, 10, 18)      # Very dark
COLOR_SNAKE_HEAD = (50, 255, 50) # Bright neon green
COLOR_SNAKE_BODY = (34, 139, 34) # Forest green
COLOR_FOOD = (255, 50, 50)       # Candy red
COLOR_OBSTACLE = (120, 120, 135) # Gray stone
COLOR_TEXT = (240, 240, 255)     # Off-white
COLOR_HIGHLIGHT = (255, 215, 0)  # Gold

class Game:
    def __init__(self, width=800, height=600, cell_size=20):
        # We don't initialize pygame automatically on import so that
        # testing frameworks can safely import models and tools.
        self.width = width
        self.height = height
        self.cell_size = cell_size

        # Grid sizes: reserve top 2 rows (40px) for HUD
        self.hud_height = 40
        self.grid_width = width // cell_size
        self.grid_height = (height - self.hud_height) // cell_size
        self.grid_size = (self.grid_width, self.grid_height)

        self.high_score_file = "high_scores.json"
        self.high_score = self.load_high_score()

        # Game state control
        self.state_start_screen = True
        self.state_game_over = False
        self.state_paused = False
        self.state_level_up_anim = 0  # Number of frames to show level up text

        self.screen = None
        self.clock = None
        self.font_large = None
        self.font_medium = None
        self.font_small = None

        self.reset()

    def init_pygame(self):
        """Lazy initialization of Pygame to facilitate testing in headless environments."""
        if self.screen is None:
            pygame.init()
            # Set window centered
            os.environ['SDL_VIDEO_CENTERED'] = '1'
            self.screen = pygame.display.set_mode((self.width, self.height))
            pygame.display.set_caption("Ultimate Snake Arcade")
            self.clock = pygame.time.Clock()

            # Fonts
            pygame.font.init()
            self.font_large = pygame.font.SysFont("sans-serif", 48, bold=True)
            self.font_medium = pygame.font.SysFont("sans-serif", 28, bold=True)
            self.font_small = pygame.font.SysFont("sans-serif", 18)

    def load_high_score(self):
        if os.path.exists(self.high_score_file):
            try:
                with open(self.high_score_file, "r") as f:
                    return json.load(f).get("high_score", 0)
            except Exception:
                pass
        return 0

    def save_high_score(self):
        try:
            with open(self.high_score_file, "w") as f:
                json.dump({"high_score": self.high_score}, f)
        except Exception:
            pass

    def reset(self):
        self.level = 1
        self.score = 0
        self.state_game_over = False
        self.state_paused = False
        self.state_level_up_anim = 0

        # Load Level Config
        config = LEVEL_CONFIGS[self.level]
        self.speed = config["speed"]
        self.obstacles = config["obstacles"]

        # Instantiate Snake in middle of bottom portion (free from top level 2 obstacles)
        self.snake = Snake((self.grid_width // 2, self.grid_height - 5), self.grid_size)

        self.food = Food(self.grid_size)
        self.food.spawn(self.snake.body, self.obstacles)

    def handle_events(self):
        self.init_pygame()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                if self.state_start_screen:
                    if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                        self.state_start_screen = False
                        self.reset()
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()

                elif self.state_game_over:
                    if event.key == pygame.K_r:
                        self.reset()
                    elif event.key == pygame.K_ESCAPE:
                        self.state_start_screen = True

                else:
                    # Normal game keys
                    if event.key == pygame.K_ESCAPE:
                        self.state_start_screen = True
                    elif event.key in (pygame.K_p, pygame.K_SPACE):
                        self.state_paused = not self.state_paused

                    if not self.state_paused:
                        if event.key in (pygame.K_UP, pygame.K_w):
                            self.snake.change_direction(Direction.UP)
                        elif event.key in (pygame.K_DOWN, pygame.K_s):
                            self.snake.change_direction(Direction.DOWN)
                        elif event.key in (pygame.K_LEFT, pygame.K_a):
                            self.snake.change_direction(Direction.LEFT)
                        elif event.key in (pygame.K_RIGHT, pygame.K_d):
                            self.snake.change_direction(Direction.RIGHT)

    def update(self):
        if self.state_start_screen or self.state_game_over or self.state_paused:
            return

        # Decrease active frames for level up overlay
        if self.state_level_up_anim > 0:
            self.state_level_up_anim -= 1

        self.snake.move()

        # Check self collision
        if self.snake.check_self_collision():
            self.trigger_game_over()
            return

        # Check obstacle collision
        if self.snake.check_obstacle_collision(self.obstacles):
            self.trigger_game_over()
            return

        # Check food collision
        if self.snake.body[0] == self.food.position:
            self.snake.grow()
            self.score += 5

            # High score update
            if self.score > self.high_score:
                self.high_score = self.score
                self.save_high_score()

            # Check Level Up
            current_target = LEVEL_CONFIGS[self.level]["target_score"]
            if self.score >= current_target:
                self.level_up()
            else:
                # Spawn new food
                self.food.spawn(self.snake.body, self.obstacles)

    def level_up(self):
        next_lvl = self.level + 1
        if next_lvl in LEVEL_CONFIGS:
            self.level = next_lvl
            config = LEVEL_CONFIGS[self.level]
            self.speed = config["speed"]
            self.obstacles = config["obstacles"]
            self.state_level_up_anim = 45  # show flash/overlay for ~45 frames (approx 3-4 seconds depending on speed)

            # Reposition snake safely if necessary, or just clear space around it
            # For simplicity, we just keep current snake but spawn food at a safe position
            self.food.spawn(self.snake.body, self.obstacles)

    def trigger_game_over(self):
        self.state_game_over = True
        if self.score > self.high_score:
            self.high_score = self.score
            self.save_high_score()

    def draw(self):
        self.init_pygame()
        # Draw background
        self.screen.fill(COLOR_BG)

        # Draw grid lines for game area
        for x in range(0, self.width, self.cell_size):
            pygame.draw.line(self.screen, COLOR_GRID, (x, self.hud_height), (x, self.height))
        for y in range(self.hud_height, self.height, self.cell_size):
            pygame.draw.line(self.screen, COLOR_GRID, (0, y), (self.width, y))

        # Draw HUD bar
        pygame.draw.rect(self.screen, COLOR_HUD_BG, (0, 0, self.width, self.hud_height))
        pygame.draw.line(self.screen, COLOR_HIGHLIGHT, (0, self.hud_height), (self.width, self.hud_height), 2)

        # Render HUD labels
        lbl_score = self.font_medium.render(f"SCORE: {self.score}", True, COLOR_TEXT)
        lbl_level = self.font_medium.render(f"LEVEL: {self.level}", True, COLOR_HIGHLIGHT)
        lbl_high = self.font_medium.render(f"HIGH: {self.high_score}", True, COLOR_TEXT)

        self.screen.blit(lbl_score, (20, 8))
        self.screen.blit(lbl_level, (self.width // 2 - lbl_level.get_width() // 2, 8))
        self.screen.blit(lbl_high, (self.width - lbl_high.get_width() - 20, 8))

        # Draw Obstacles (shift y down by hud_height)
        for ox, oy in self.obstacles:
            rx = ox * self.cell_size
            ry = oy * self.cell_size + self.hud_height
            pygame.draw.rect(self.screen, COLOR_OBSTACLE, (rx, ry, self.cell_size, self.cell_size))
            # inner border for bevel effect
            pygame.draw.rect(self.screen, (150, 150, 165), (rx + 2, ry + 2, self.cell_size - 4, self.cell_size - 4), 1)

        # Draw Food
        fx = self.food.position[0] * self.cell_size
        fy = self.food.position[1] * self.cell_size + self.hud_height
        pygame.draw.ellipse(self.screen, COLOR_FOOD, (fx + 2, fy + 2, self.cell_size - 4, self.cell_size - 4))

        # Draw Snake
        for idx, segment in enumerate(self.snake.body):
            sx = segment[0] * self.cell_size
            sy = segment[1] * self.cell_size + self.hud_height
            color = COLOR_SNAKE_HEAD if idx == 0 else COLOR_SNAKE_BODY

            # Rounded corners or standard rectangles
            pygame.draw.rect(self.screen, color, (sx + 1, sy + 1, self.cell_size - 2, self.cell_size - 2))

            # Eye for head
            if idx == 0:
                eye_color = (0, 0, 0)
                # Draw small eyes depending on direction
                dx, dy = self.snake.direction.value
                if dx != 0: # LEFT or RIGHT
                    pygame.draw.circle(self.screen, eye_color, (sx + self.cell_size // 2, sy + 6), 2)
                    pygame.draw.circle(self.screen, eye_color, (sx + self.cell_size // 2, sy + 14), 2)
                else: # UP or DOWN
                    pygame.draw.circle(self.screen, eye_color, (sx + 6, sy + self.cell_size // 2), 2)
                    pygame.draw.circle(self.screen, eye_color, (sx + 14, sy + self.cell_size // 2), 2)

        # Overlays
        if self.state_start_screen:
            self.draw_overlay("ULTIMATE SNAKE ARCADE", "Press SPACE or ENTER to Play", "ESC to Quit | Arrows/WASD to Move")
        elif self.state_game_over:
            self.draw_overlay("GAME OVER", "Press 'R' to Restart", f"Final Score: {self.score} | ESC to Main Menu")
        elif self.state_paused:
            self.draw_overlay("PAUSED", "Press SPACE or 'P' to Resume", "ESC to Main Menu")
        elif self.state_level_up_anim > 0:
            # Draw a flash Level Up banner
            lbl_banner = self.font_large.render(f"LEVEL {self.level} UP!", True, COLOR_HIGHLIGHT)
            self.screen.blit(lbl_banner, (self.width // 2 - lbl_banner.get_width() // 2, self.height // 2 - 50))

        pygame.display.flip()

    def draw_overlay(self, title_text, subtitle_text, help_text):
        # Semi-transparent overlay panel
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((10, 10, 20, 210)) # Dark translucent slate
        self.screen.blit(overlay, (0, 0))

        # Title
        title_surf = self.font_large.render(title_text, True, COLOR_HIGHLIGHT if "ULTIMATE" in title_text else COLOR_TEXT)
        title_rect = title_surf.get_rect(center=(self.width // 2, self.height // 2 - 60))
        self.screen.blit(title_surf, title_rect)

        # Subtitle
        sub_surf = self.font_medium.render(subtitle_text, True, COLOR_TEXT)
        sub_rect = sub_surf.get_rect(center=(self.width // 2, self.height // 2))
        self.screen.blit(sub_surf, sub_rect)

        # Help footer
        help_surf = self.font_small.render(help_text, True, (160, 160, 180))
        help_rect = help_surf.get_rect(center=(self.width // 2, self.height // 2 + 60))
        self.screen.blit(help_surf, help_rect)

    def run(self):
        self.init_pygame()
        while True:
            self.handle_events()
            self.update()
            self.draw()
            # Clock ticks according to current level speed
            self.clock.tick(self.speed)

if __name__ == "__main__":
    game = Game()
    game.run()
