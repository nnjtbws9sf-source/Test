"""Space Shooter — main game class."""
import curses
import random
from entities import Player, Enemy, Bullet, EnemyBullet, Star, Explosion

_TITLE = [
    " ____  ____   _    ____ _____   ___ ",
    "/ ___||  _ \\ / \\  / ___| ____| |__ \\",
    "\\___ \\| |_) / _ \\| |   |  _|     ) |",
    " ___) |  __/ ___ \\ |___| |___   / / ",
    "|____/|_| /_/   \\_\\____|_____| |_|  ",
]

_SUBTITLE = [
    " ____  _   _  ___   ___ _____ _____ ____  ",
    "/ ___|| | | |/ _ \\ / _ \\_   _| ____|  _ \\ ",
    "\\___ \\| |_| | | | | | | || | |  _| | |_) |",
    " ___) |  _  | |_| | |_| || | | |___|  _ < ",
    "|____/|_| |_|\\___/ \\___/ |_| |_____|_| \\_\\",
]

_SHIP = [
    "    /\\    ",
    "   /##\\   ",
    "  / ## \\  ",
    " /______\\ ",
    "   |  |   ",
    "  /|  |\\  ",
]


class Game:
    # colour-pair IDs
    CP_PLAYER  = 1
    CP_ENEMY   = 2
    CP_BULLET  = 3
    CP_STAR    = 4
    CP_UI      = 5
    CP_EBULLET = 6
    CP_EXPLODE = 7
    CP_TITLE   = 8

    def __init__(self, scr):
        self.scr = scr
        self._init_curses()
        self.rows, self.cols = scr.getmaxyx()
        self._new_game()

    # ------------------------------------------------------------------ setup

    def _init_curses(self):
        curses.curs_set(0)
        self.scr.nodelay(True)
        self.scr.timeout(50)          # ~20 fps
        curses.start_color()
        curses.use_default_colors()
        pairs = [
            (self.CP_PLAYER,  curses.COLOR_GREEN,   -1),
            (self.CP_ENEMY,   curses.COLOR_RED,     -1),
            (self.CP_BULLET,  curses.COLOR_YELLOW,  -1),
            (self.CP_STAR,    curses.COLOR_CYAN,    -1),
            (self.CP_UI,      curses.COLOR_WHITE,   -1),
            (self.CP_EBULLET, curses.COLOR_MAGENTA, -1),
            (self.CP_EXPLODE, curses.COLOR_YELLOW,  -1),
            (self.CP_TITLE,   curses.COLOR_CYAN,    -1),
        ]
        for pid, fg, bg in pairs:
            curses.init_pair(pid, fg, bg)

    def _new_game(self):
        self.rows, self.cols = self.scr.getmaxyx()
        self.player     = Player(self.cols // 2 - 2, self.rows - 6)
        self.enemies    = []
        self.bullets    = []
        self.ebullets   = []
        self.explosions = []
        self.stars      = [Star(self.cols, self.rows) for _ in range(65)]
        self.wave       = 1
        self.score      = 0
        self.over       = False
        self.paused     = False
        self._spawn_wave()

    def _spawn_wave(self):
        cols_n  = min(10, 4 + self.wave)
        rows_n  = min(4,  1 + self.wave // 2)
        spacing = max(6, self.cols // (cols_n + 1))
        for row in range(rows_n):
            etype = min(2, row)
            for col in range(cols_n):
                x = spacing * (col + 1) - 2
                y = row * 5 + 2
                if x + 6 < self.cols:
                    self.enemies.append(Enemy(x, y, etype))

    # ------------------------------------------------------------------ logic

    @staticmethod
    def _overlap(ax1, ay1, ax2, ay2, bx1, by1, bx2, by2):
        return ax1 < bx2 and ax2 > bx1 and ay1 < by2 and ay2 > by1

    def _update(self):
        if self.over or self.paused:
            return

        for s in self.stars:
            s.update(self.rows)

        self.player.update()

        for b in self.bullets[:]:
            b.update()
            if b.offscreen(self.rows):
                self.bullets.remove(b)

        for b in self.ebullets[:]:
            b.update()
            if b.offscreen(self.rows):
                self.ebullets.remove(b)

        for e in self.enemies[:]:
            e.update(self.cols)
            if e.offscreen(self.rows):
                self.enemies.remove(e)
                self.player.lives -= 1
                if self.player.lives <= 0:
                    self.over = True
                    return
            shot = e.maybe_shoot()
            if shot:
                self.ebullets.append(shot)

        # player bullets vs enemies
        for b in self.bullets[:]:
            bbox = b.hitbox()
            for e in self.enemies[:]:
                if self._overlap(*bbox, *e.hitbox()):
                    cx = e.ix() + e.W // 2
                    cy = e.iy() + e.H // 2
                    self.explosions.append(Explosion(cx, cy))
                    self.score += e.pts
                    if b in self.bullets:
                        self.bullets.remove(b)
                    if e in self.enemies:
                        self.enemies.remove(e)
                    break

        # enemy bullets vs player
        pbox = self.player.hitbox()
        for b in self.ebullets[:]:
            if self._overlap(*b.hitbox(), *pbox):
                self.ebullets.remove(b)
                self.player.hit()
                if self.player.lives <= 0:
                    self.over = True
                    return

        for ex in self.explosions[:]:
            ex.update()
            if ex.done:
                self.explosions.remove(ex)

        if not self.enemies:
            self.wave += 1
            self._spawn_wave()

    # ------------------------------------------------------------------ draw

    def _s(self, y, x, text, cp, attr=0):
        """Safe addstr — clips to screen bounds."""
        if y < 0 or y >= self.rows or x >= self.cols:
            return
        if x < 0:
            text = text[-x:]
            x = 0
        text = text[:max(0, self.cols - x - 1)]
        if text:
            try:
                self.scr.addstr(y, x, text, curses.color_pair(cp) | attr)
            except curses.error:
                pass

    def _c(self, y, x, ch, cp, attr=0):
        """Safe addch — clips to screen bounds."""
        if 0 <= y < self.rows and 0 <= x < self.cols - 1:
            try:
                self.scr.addch(y, x, ch, curses.color_pair(cp) | attr)
            except curses.error:
                pass

    def _draw(self):
        self.scr.erase()

        for s in self.stars:
            self._c(s.iy(), s.x, s.ch, self.CP_STAR)

        for e in self.enemies:
            for i, row in enumerate(e.sprite):
                self._s(e.iy() + i, e.ix(), row, self.CP_ENEMY)

        for b in self.bullets:
            self._c(b.iy(), b.x, '|', self.CP_BULLET, curses.A_BOLD)

        for b in self.ebullets:
            self._c(b.iy(), b.x, 'v', self.CP_EBULLET, curses.A_BOLD)

        for ex in self.explosions:
            for i, row in enumerate(ex.lines()):
                self._s(ex.y + i, ex.x, row, self.CP_EXPLODE, curses.A_BOLD)

        # player (blinks while invincible)
        if self.player.invincible == 0 or self.player.invincible % 6 < 3:
            for i, row in enumerate(self.player.SPRITE):
                self._s(self.player.y + i, self.player.x, row,
                        self.CP_PLAYER, curses.A_BOLD)

        # ── HUD ──────────────────────────────────────────────────────────
        lives = "* " * self.player.lives
        hud = f" Score:{self.score:6d}  Lives: {lives} Wave:{self.wave} "
        self._s(0, 0, hud, self.CP_UI, curses.A_BOLD)

        ctrl = " Arrows:Move  Space:Shoot  P:Pause  Q:Quit "
        self._s(self.rows - 1, 0, ctrl, self.CP_UI)

        if self.paused:
            self._overlay(["   PAUSED   ", " [P] Resume "], self.CP_UI)
        if self.over:
            self._overlay([
                "  GAME  OVER  ",
                f"  Score: {self.score:5d}  ",
                f"  Wave:  {self.wave:3d}    ",
                " [R] Restart  ",
                "  [Q] Quit    ",
            ], self.CP_ENEMY)

        self.scr.refresh()

    def _overlay(self, lines, cp):
        w  = max(len(l) for l in lines) + 2
        h  = len(lines) + 2
        sy = self.rows // 2 - h // 2
        sx = self.cols // 2 - w // 2
        a  = curses.color_pair(cp) | curses.A_BOLD
        self._s(sy,     sx, "+" + "-" * w + "+", cp, curses.A_BOLD)
        for i, line in enumerate(lines):
            self._s(sy + 1 + i, sx, "|" + line.center(w) + "|", cp, curses.A_BOLD)
        self._s(sy + h - 1, sx, "+" + "-" * w + "+", cp, curses.A_BOLD)

    # ----------------------------------------------------------------- input

    def _handle_input(self):
        key = self.scr.getch()

        if key in (ord('q'), ord('Q'), 27):   # Q or ESC
            return False

        if key in (ord('p'), ord('P')):
            self.paused = not self.paused

        if self.over:
            if key in (ord('r'), ord('R')):
                self._new_game()
            return True

        if self.paused:
            return True

        dx = dy = 0
        if key == curses.KEY_LEFT:  dx = -2
        if key == curses.KEY_RIGHT: dx =  2
        if key == curses.KEY_UP:    dy = -1
        if key == curses.KEY_DOWN:  dy =  1
        if dx or dy:
            self.player.move(dx, dy, self.cols, self.rows)

        if key == ord(' ') and self.player.cooldown == 0:
            self.bullets.append(self.player.shoot())

        return True

    # ------------------------------------------------------------------ run

    def run(self):
        self._title_screen()
        while self._handle_input():
            self._update()
            self._draw()

    def _title_screen(self):
        self.rows, self.cols = self.scr.getmaxyx()
        self.scr.erase()

        # Try to show the big title; fall back to a simple banner on narrow terminals
        use_big = self.cols >= len(_SUBTITLE[0]) + 4

        if use_big:
            title_lines = _TITLE + [""] + _SUBTITLE
        else:
            title_lines = ["=== SPACE SHOOTER ==="]

        total_h = len(title_lines) + len(_SHIP) + 6
        sy = max(1, (self.rows - total_h) // 2)

        for i, line in enumerate(title_lines):
            x = max(0, self.cols // 2 - len(line) // 2)
            self._s(sy + i, x, line, self.CP_TITLE, curses.A_BOLD)

        ship_y = sy + len(title_lines) + 1
        for i, line in enumerate(_SHIP):
            x = self.cols // 2 - len(line) // 2
            self._s(ship_y + i, x, line, self.CP_PLAYER, curses.A_BOLD)

        controls = [
            " Controls ",
            " Arrows : Move     ",
            " Space  : Shoot    ",
            " P      : Pause    ",
            " Q / ESC: Quit     ",
        ]
        ctrl_y = ship_y + len(_SHIP) + 1
        for i, line in enumerate(controls):
            x = self.cols // 2 - len(line) // 2
            cp = self.CP_UI if i > 0 else self.CP_BULLET
            self._s(ctrl_y + i, x, line, cp, curses.A_BOLD if i == 0 else 0)

        prompt = "[ Press any key to start ]"
        self._s(ctrl_y + len(controls) + 1,
                self.cols // 2 - len(prompt) // 2,
                prompt, self.CP_UI, curses.A_BLINK)

        self.scr.refresh()
        self.scr.nodelay(False)
        self.scr.getch()
        self.scr.nodelay(True)
        self.scr.timeout(50)
