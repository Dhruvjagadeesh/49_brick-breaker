import pygame
from .paddle import Paddle
from .ball import Ball
from .brick import Brick
from .sounds import Sounds

# Game Engine

WHITE = (255, 255, 255)
BG = (15, 15, 25)
BRICK_COLORS = [
    (200, 60, 60),
    (200, 140, 60),
    (200, 200, 60),
    (80, 180, 80),
    (80, 140, 200),
]

# Difficulty: ball speed and paddle width
DIFFICULTIES = {
    "Easy":   {"ball_speed": 3, "paddle_width": 140},
    "Medium": {"ball_speed": 4, "paddle_width": 100},
    "Hard":   {"ball_speed": 6, "paddle_width": 70},
}
DIFFICULTY_KEYS = {
    pygame.K_1: "Easy", pygame.K_e: "Easy",
    pygame.K_2: "Medium", pygame.K_m: "Medium",
    pygame.K_3: "Hard", pygame.K_h: "Hard",
}

class GameEngine:
    def __init__(self, width, height, difficulty="Medium"):
        self.width = width
        self.height = height
        self.rows, self.cols = 5, 8
        self.font = pygame.font.SysFont("Arial", 28)
        self.big_font = pygame.font.SysFont("Arial", 56, bold=True)
        self.small_font = pygame.font.SysFont("Arial", 22)
        self.sounds = Sounds()
        self.new_game(difficulty)

    def new_game(self, difficulty):
        """(Re)start the game with the chosen difficulty."""
        self.difficulty = difficulty
        settings = DIFFICULTIES[difficulty]
        self.ball_speed = settings["ball_speed"]
        pw = settings["paddle_width"]
        self.paddle = Paddle(self.width // 2 - pw // 2, self.height - 30, pw, 14)
        self.ball = Ball(self.width // 2, self.height - 50, radius=8)
        self._reset_ball()
        self.bricks = self._build_bricks(self.rows, self.cols)
        self.lives = 3
        self.score = 0
        self.game_over = False
        self.result = None  # "win" or "lose"

    def _build_bricks(self, rows, cols):
        bricks = []
        margin, gap, top = 30, 6, 60
        brick_w = (self.width - margin * 2 - gap * (cols - 1)) // cols
        brick_h = 22
        for r in range(rows):
            for c in range(cols):
                x = margin + c * (brick_w + gap)
                y = top + r * (brick_h + gap)
                bricks.append(Brick(x, y, brick_w, brick_h))
        return bricks

    def handle_event(self, event):
        # Paddle uses held keys (handle_input); the end screen waits for a key press.
        if self.game_over and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.event.post(pygame.event.Event(pygame.QUIT))
            elif event.key in DIFFICULTY_KEYS:
                self.new_game(DIFFICULTY_KEYS[event.key])

    def handle_input(self):
        if self.game_over:
            return
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.paddle.move(-self.paddle.speed, self.width)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.paddle.move(self.paddle.speed, self.width)

    def update(self):
        if self.game_over:
            return

        self.ball.move()

        # Walls: use abs() so the ball can never get stuck inside a wall
        if self.ball.x - self.ball.radius <= 0:
            self.ball.x = self.ball.radius
            self.ball.vx = abs(self.ball.vx)
            self.sounds.play("wall")
        elif self.ball.x + self.ball.radius >= self.width:
            self.ball.x = self.width - self.ball.radius
            self.ball.vx = -abs(self.ball.vx)
            self.sounds.play("wall")
        if self.ball.y - self.ball.radius <= 0:
            self.ball.y = self.ball.radius
            self.ball.vy = abs(self.ball.vy)
            self.sounds.play("wall")

        # Paddle: only bounce when moving down; angle depends on hit position
        paddle = self.paddle.rect()
        if self.ball.vy > 0 and self.ball.rect().colliderect(paddle):
            side = self._collision_side(paddle)
            self.sounds.play("paddle")
            if side == "top":
                self.ball.y = paddle.top - self.ball.radius
                speed = (self.ball.vx ** 2 + self.ball.vy ** 2) ** 0.5
                offset = (self.ball.x - paddle.centerx) / (paddle.width / 2)
                offset = max(-1.0, min(1.0, offset))
                self.ball.vx = speed * 0.8 * offset
                if abs(self.ball.vx) < 1:
                    self.ball.vx = 1 if self.ball.vx >= 0 else -1
                self.ball.vy = -max(2.0, (speed ** 2 - self.ball.vx ** 2) ** 0.5)
            else:
                # Hit the side of the paddle: push sideways
                if side == "left":
                    self.ball.x = paddle.left - self.ball.radius
                    self.ball.vx = -abs(self.ball.vx)
                else:
                    self.ball.x = paddle.right + self.ball.radius
                    self.ball.vx = abs(self.ball.vx)

        # Bricks: flip vx or vy depending on which side was hit
        for brick in self.bricks:
            if brick.alive and self.ball.rect().colliderect(brick.rect()):
                brick.alive = False
                self.score += 1
                self.sounds.play("brick")
                r = brick.rect()
                side = self._collision_side(r)
                if side == "top":
                    self.ball.y = r.top - self.ball.radius
                    self.ball.vy = -abs(self.ball.vy)
                elif side == "bottom":
                    self.ball.y = r.bottom + self.ball.radius
                    self.ball.vy = abs(self.ball.vy)
                elif side == "left":
                    self.ball.x = r.left - self.ball.radius
                    self.ball.vx = -abs(self.ball.vx)
                else:
                    self.ball.x = r.right + self.ball.radius
                    self.ball.vx = abs(self.ball.vx)
                break

        if self.ball.y - self.ball.radius > self.height:
            self.lives -= 1
            if self.lives <= 0:
                self.game_over = True
                self.result = "lose"
                self.sounds.play("lose")
            else:
                self._reset_ball()

        if not self.game_over and all(not b.alive for b in self.bricks):
            self.game_over = True
            self.result = "win"
            self.sounds.play("win")

    def _collision_side(self, rect):
        """Return which side of rect the ball hit, using the smallest overlap."""
        b = self.ball.rect()
        overlap_left = b.right - rect.left
        overlap_right = rect.right - b.left
        overlap_top = b.bottom - rect.top
        overlap_bottom = rect.bottom - b.top
        min_x = min(overlap_left, overlap_right)
        min_y = min(overlap_top, overlap_bottom)
        if min_x < min_y:
            return "left" if overlap_left < overlap_right else "right"
        return "top" if overlap_top < overlap_bottom else "bottom"

    def _reset_ball(self):
        self.ball.x, self.ball.y = self.width // 2, self.height - 50
        self.ball.vx, self.ball.vy = self.ball_speed, -self.ball_speed

    def render(self, screen):
        screen.fill(BG)

        pygame.draw.rect(screen, WHITE, self.paddle.rect())
        pygame.draw.circle(screen, WHITE, (int(self.ball.x), int(self.ball.y)), self.ball.radius)

        for i, brick in enumerate(self.bricks):
            if brick.alive:
                row = i // self.cols
                color = BRICK_COLORS[row % len(BRICK_COLORS)]
                pygame.draw.rect(screen, color, brick.rect())

        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        screen.blit(score_text, (10, 10))
        lives_text = self.font.render(f"Lives: {self.lives}", True, WHITE)
        screen.blit(lives_text, (self.width - 130, 10))
        diff_text = self.small_font.render(self.difficulty, True, (180, 180, 180))
        screen.blit(diff_text, diff_text.get_rect(midtop=(self.width // 2, 14)))

        if self.game_over:
            self._render_end_screen(screen)

    def _draw_centered(self, screen, text, font, color, y):
        surf = font.render(text, True, color)
        screen.blit(surf, surf.get_rect(center=(self.width // 2, y)))

    def _render_end_screen(self, screen):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        if self.result == "win":
            title, color = "YOU WIN!", (90, 220, 90)
        else:
            title, color = "GAME OVER", (230, 70, 70)
        self._draw_centered(screen, title, self.big_font, color, self.height // 2 - 60)
        self._draw_centered(screen, f"Final Score: {self.score}", self.font, WHITE, self.height // 2)
        self._draw_centered(screen, "Play again? Choose difficulty:", self.small_font, WHITE, self.height // 2 + 50)
        self._draw_centered(screen, "1 - Easy    2 - Medium    3 - Hard", self.small_font, (255, 220, 120), self.height // 2 + 85)
        self._draw_centered(screen, "ESC - Exit", self.small_font, (180, 180, 180), self.height // 2 + 120)
