"""Game entities for Space Shooter."""
import random


class Player:
    SPRITE = [
        "  ^  ",
        " /|\\ ",
        "/___\\",
    ]
    W, H = 5, 3

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.lives = 3
        self.cooldown = 0
        self.invincible = 0

    def move(self, dx, dy, cols, rows):
        self.x = max(0, min(cols - self.W, self.x + dx))
        self.y = max(2, min(rows - self.H - 2, self.y + dy))

    def update(self):
        if self.cooldown > 0:
            self.cooldown -= 1
        if self.invincible > 0:
            self.invincible -= 1

    def shoot(self):
        self.cooldown = 8
        return Bullet(self.x + self.W // 2, self.y - 1, -1, player=True)

    def hit(self):
        if self.invincible == 0:
            self.lives -= 1
            self.invincible = 80
            return True
        return False

    def hitbox(self):
        return self.x, self.y, self.x + self.W, self.y + self.H


ENEMY_DEFS = [
    {
        "sprite": [" /V\\ ", "(---)", " \\_/ "],
        "pts": 10, "spd": 0.35, "shoot_p": 0.002,
    },
    {
        "sprite": [" >-< ", " |T| "],
        "pts": 20, "spd": 0.60, "shoot_p": 0.004,
    },
    {
        "sprite": ["/WW\\\\", "|==|", "\\__/"],
        "pts": 40, "spd": 0.20, "shoot_p": 0.007,
    },
]


class Enemy:
    def __init__(self, x, y, etype=0):
        cfg = ENEMY_DEFS[etype % len(ENEMY_DEFS)]
        self.sprite  = cfg["sprite"]
        self.pts     = cfg["pts"]
        self.spd     = cfg["spd"]
        self.shoot_p = cfg["shoot_p"]
        self.x       = float(x)
        self.y       = float(y)
        self.W       = max(len(r) for r in self.sprite)
        self.H       = len(self.sprite)
        self.dx      = 1

    def ix(self):
        return int(self.x)

    def iy(self):
        return int(self.y)

    def update(self, cols):
        self.x += self.spd * self.dx
        if self.x <= 0:
            self.x = 0.0
            self.dx = 1
            self.y += 1
        elif self.x + self.W >= cols:
            self.x = float(cols - self.W)
            self.dx = -1
            self.y += 1

    def maybe_shoot(self):
        if random.random() < self.shoot_p:
            return EnemyBullet(self.ix() + self.W // 2, self.iy() + self.H)
        return None

    def hitbox(self):
        return self.ix(), self.iy(), self.ix() + self.W, self.iy() + self.H

    def offscreen(self, rows):
        return self.iy() + self.H >= rows - 2


class Bullet:
    def __init__(self, x, y, dy, player=True):
        self.x      = x
        self.y      = float(y)
        self.dy     = dy
        self.player = player

    def update(self):
        self.y += self.dy * 2.0

    def iy(self):
        return int(self.y)

    def offscreen(self, rows):
        return self.y < 0 or self.y >= rows

    def hitbox(self):
        return self.x, self.iy(), self.x + 1, self.iy() + 1


class EnemyBullet(Bullet):
    def __init__(self, x, y):
        super().__init__(x, y, 1, player=False)


class Star:
    def __init__(self, cols, rows):
        self.x   = random.randint(0, cols - 1)
        self.y   = float(random.randint(0, rows - 1))
        self.spd = random.choice([0.15, 0.35, 0.70])
        self.ch  = '.' if self.spd < 0.5 else '*'

    def update(self, rows):
        self.y += self.spd
        if self.y >= rows:
            self.y = 0.0

    def iy(self):
        return int(self.y)


class Explosion:
    FRAMES = [
        ["\\|/", "-X-", "/|\\"],
        [" * ", "* *", " * "],
        ["   ", "   ", "   "],
    ]

    def __init__(self, x, y):
        self.x     = x - 1
        self.y     = y - 1
        self.frame = 0
        self.timer = 0

    @property
    def done(self):
        return self.frame >= len(self.FRAMES)

    def update(self):
        self.timer += 1
        if self.timer >= 4:
            self.timer = 0
            self.frame += 1

    def lines(self):
        if not self.done:
            return self.FRAMES[self.frame]
        return []
