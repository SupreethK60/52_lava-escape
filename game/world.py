import pygame
import random

PLATFORM_COLOR = (100, 80, 50)
CRUMBLE_COLOR = (150, 120, 90)
SPRING_COLOR = (60, 200, 90)
LAVA_COLOR = (220, 60, 20)

CRUMBLE_FRAMES = 30   # about 0.5s at 60 FPS between landing and breaking


class Platform(pygame.Rect):
    def __init__(self, x, y, w, h, kind="normal"):
        super().__init__(x, y, w, h)
        self.kind = kind            # "normal" | "crumble" | "spring"
        self.crumble_timer = -1     # -1 = untouched
        self.broken = False

    def trigger_crumble(self):
        if self.kind == "crumble" and self.crumble_timer < 0:
            self.crumble_timer = CRUMBLE_FRAMES

    def update(self):
        if self.crumble_timer > 0:
            self.crumble_timer -= 1
            if self.crumble_timer == 0:
                self.broken = True


def generate_platforms(width, base_y, count=30):
    plats = [Platform(0, base_y, width, 20)]  # ground
    y = base_y - 110
    for i in range(count):
        w = random.randint(80, 200)
        x = random.randint(0, width - w)
        kind = "normal"
        if i < count - 1:                      # keep the top platform solid for victory
            r = random.random()
            if r < 0.20:
                kind = "crumble"
            elif r < 0.32:
                kind = "spring"
        plats.append(Platform(x, y, w, 16, kind))
        y -= random.randint(80, 130)
    return plats


def update_platforms(platforms):
    """Tick crumble timers and return the list without broken platforms."""
    for p in platforms:
        p.update()
    return [p for p in platforms if not p.broken]


def draw_platforms(screen, platforms, cam_y):
    for p in platforms:
        r = p.move(0, -int(cam_y))
        color = PLATFORM_COLOR
        if p.kind == "crumble":
            color = CRUMBLE_COLOR
            if p.crumble_timer > 0:            # shake while about to break
                r.x += random.randint(-3, 3)
                r.y += random.randint(-2, 2)
                color = (200, 90, 60)
        elif p.kind == "spring":
            color = SPRING_COLOR
        pygame.draw.rect(screen, color, r, border_radius=3)
        if p.kind == "spring":
            for i in range(r.x + 8, r.right - 8, 16):
                pygame.draw.line(screen, (20, 120, 50), (i, r.y + 3), (i + 6, r.bottom - 3), 2)


def draw_lava(screen, lava_y, cam_y, width, height, frame):
    import math
    ly = int(lava_y - cam_y)
    if ly < height:
        # lava surface wave
        pts = [(0, ly)]
        for x in range(0, width + 20, 20):
            pts.append((x, ly + int(math.sin(x * 0.08 + frame * 0.1) * 8)))
        pts.append((width, height)); pts.append((0, height))
        pygame.draw.polygon(screen, LAVA_COLOR, pts)
        # glow
        s = pygame.Surface((width, 30), pygame.SRCALPHA)
        for i in range(15):
            pygame.draw.line(s, (255, 100, 0, max(0, 60 - i * 4)), (0, i), (width, i), 1)
        screen.blit(s, (0, ly - 15))