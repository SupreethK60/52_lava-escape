import pygame
from game.player import Player
from game.world import generate_platforms, draw_lava, update_platforms, draw_platforms

WIDTH, HEIGHT = 500, 640
FPS = 60
BG = (20, 15, 30)
GROUND_Y = HEIGHT + 200

MAX_RISE = 1.2           # cap on base lava speed
SURGE_MULT = 2.0         # speed multiplier during a surge
SURGE_INTERVAL = 480     # about 8s between surges
SURGE_DURATION = 120     # about 2s per surge
SURGE_WARNING = 90       # about 1.5s warning before a surge


class GameEngine:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Lava Escape")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 24, bold=True)
        self.small_font = pygame.font.SysFont("monospace", 16, bold=True)
        self.big_font = pygame.font.SysFont("monospace", 42, bold=True)
        self.reset()

    def reset(self):
        self.platforms = generate_platforms(WIDTH, GROUND_Y)
        self.player = Player(WIDTH // 2 - 16, GROUND_Y - 50)
        self.cam_y = 0
        self.lava_y = GROUND_Y + 60
        self.lava_rise = 0.4
        self.current_rise = self.lava_rise
        self.score = 0
        self.game_over = False
        self.won = False
        self.top_y = self.platforms[-1].y
        self.frame = 0
        self.surge_left = 0
        self.next_surge = SURGE_INTERVAL

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self.reset()
        return True

    def update(self):
        if self.game_over or self.won:
            return
        keys = pygame.key.get_pressed()
        self.platforms = update_platforms(self.platforms)      # crumble timers / removal
        self.player.update(keys, self.platforms, WIDTH)
        target = self.player.rect.centery - HEIGHT // 2
        if target < self.cam_y:
            self.cam_y = target

        # surge state machine
        if self.surge_left > 0:
            self.surge_left -= 1
            if self.surge_left == 0:
                self.next_surge = self.frame + SURGE_INTERVAL
        elif self.frame >= self.next_surge:
            self.surge_left = SURGE_DURATION

        mult = SURGE_MULT if self.surge_left > 0 else 1.0
        self.current_rise = self.lava_rise * mult
        self.lava_y -= self.current_rise
        self.lava_rise = min(MAX_RISE, self.lava_rise + 0.0003)

        self.score = max(0, (GROUND_Y - self.player.rect.y) // 10)
        self.frame += 1
        if self.player.rect.bottom >= self.lava_y:
            self.game_over = True
        if self.player.rect.top <= self.top_y - 20:
            self.won = True

    def _draw_danger_hud(self):
        ratio = min(1.0, self.current_rise / (MAX_RISE * SURGE_MULT))
        x, y, w, h = 8, 42, 180, 14
        pygame.draw.rect(self.screen, (50, 40, 60), (x, y, w, h), border_radius=4)
        # green -> yellow -> red as the lava speeds up
        color = (int(255 * min(1, ratio * 2)), int(255 * min(1, (1 - ratio) * 2)), 40)
        pygame.draw.rect(self.screen, color, (x, y, int(w * ratio), h), border_radius=4)
        pygame.draw.rect(self.screen, (220, 200, 180), (x, y, w, h), 2, border_radius=4)
        label = self.small_font.render(f"DANGER  {self.current_rise:.2f}x", True, (220, 200, 180))
        self.screen.blit(label, (x + w + 8, y - 1))

        flash_on = (self.frame // 8) % 2 == 0
        if self.surge_left > 0 and flash_on:
            t = self.font.render("!! LAVA SURGE !!", True, (255, 80, 40))
            self.screen.blit(t, (WIDTH // 2 - t.get_width() // 2, 66))
        elif self.surge_left == 0 and 0 < self.next_surge - self.frame <= SURGE_WARNING and flash_on:
            t = self.font.render("Surge incoming...", True, (255, 200, 60))
            self.screen.blit(t, (WIDTH // 2 - t.get_width() // 2, 66))

    def draw(self):
        self.screen.fill(BG)
        draw_platforms(self.screen, self.platforms, self.cam_y)
        self.player.draw(self.screen, self.cam_y)
        draw_lava(self.screen, self.lava_y, self.cam_y, WIDTH, HEIGHT, self.frame)
        sc = self.font.render(f"Height: {self.score}m  R=Restart", True, (220, 200, 180))
        self.screen.blit(sc, (8, 10))
        self._draw_danger_hud()
        if self.game_over:
            self._msg("LAVA GOT YOU!", (220, 80, 40))
        if self.won:
            self._msg("ESCAPED!", (80, 220, 100))
        pygame.display.flip()

    def _msg(self, text, color):
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 150))
        self.screen.blit(ov, (0, 0))
        m = self.big_font.render(text, True, color)
        s = self.font.render("Press R to Play Again", True, (200, 200, 200))
        self.screen.blit(m, (WIDTH // 2 - m.get_width() // 2, HEIGHT // 2 - 40))
        self.screen.blit(s, (WIDTH // 2 - s.get_width() // 2, HEIGHT // 2 + 20))

    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()