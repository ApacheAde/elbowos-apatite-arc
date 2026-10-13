#!/usr/bin/env python3
"""Apatite Arc — neon grappling swing arcade for ElbowOS. Python 3 + pygame."""
import math, os, random, subprocess, sys

RECORD = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
PLAY = "--play" in sys.argv
if RECORD or not PLAY:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

W, H, FPS, SECS = 1080, 1920, 30, 15
OUT = os.environ.get("ELBOWOS_MP4", "/workspace/artifacts/APATITE_ARC_ElbowOS.mp4")
TITLE, HANDLE = "APATITE ARC", "x.com/ElbowOS"

VOID = (8, 6, 22)
DEEP = (14, 10, 38)
PEG = (180, 90, 255)
APATITE = (72, 220, 255)
GOLD = (255, 210, 80)
ROSE = (255, 70, 140)
MINT = (90, 255, 180)
WHITE = (240, 236, 255)
SPIKE = (255, 50, 80)

class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        flags = 0 if PLAY else pygame.HIDDEN
        try:
            self.screen = pygame.display.set_mode((W, H), flags)
        except pygame.error:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            pygame.display.quit()
            pygame.display.init()
            self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption(TITLE)
        self.font_lg = pygame.font.SysFont("DejaVu Sans", 58, bold=True)
        self.font = pygame.font.SysFont("DejaVu Sans", 38, bold=True)
        self.font_sm = pygame.font.SysFont("DejaVu Sans", 24)
        self.clock = pygame.time.Clock()
        self.score = self.combo = self.t = self.flash = 0
        self.pegs = self._make_pegs()
        self.orbs = self._make_orbs()
        self.spikes = self._make_spikes()
        self.player = [W//2, 400, 0, 0, None, 0]  # x,y,vx,vy, attached_peg, angle
        self.sparks = []
        self.trail = []
        self.stars = [[random.randint(0,W), random.randint(0,H), random.uniform(0.4,1.6), random.choice([APATITE, GOLD, ROSE])] for _ in range(60)]

    def _make_pegs(self):
        pegs = []
        for i in range(9):
            y = 280 + i * 170
            x = 180 + (i % 3) * 360 + random.randint(-40, 40)
            pegs.append([x, y, 22])
        return pegs

    def _make_orbs(self):
        return [[random.randint(100, W-100), random.randint(350, 1600), 16, 1] for _ in range(6)]

    def _make_spikes(self):
        return [[random.randint(60, W-60), random.randint(500, 1700), 28] for _ in range(4)]

    def nearest_peg(self, x, y, maxd=280):
        best, bd = None, maxd
        for p in self.pegs:
            d = math.hypot(p[0]-x, p[1]-y)
            if d < bd:
                best, bd = p, d
        return best

    def autoplay(self):
        x, y, vx, vy, peg, ang = self.player
        if peg is None:
            np = self.nearest_peg(x, y, 320)
            if np and abs(vx) + abs(vy) < 8:
                self.attach(np)
        else:
            if ang > 1.2 or ang < -1.2 or self.t % 28 == 0:
                self.release()

    def attach(self, peg):
        x, y = self.player[0], self.player[1]
        self.player[4] = peg
        dx, dy = x - peg[0], y - peg[1]
        self.player[5] = math.atan2(dy, dx)
        self.player[2] = self.player[3] = 0

    def release(self):
        peg = self.player[4]
        if peg is None:
            return
        ang = self.player[5]
        spd = 11.5
        self.player[2] = math.cos(ang) * spd
        self.player[3] = math.sin(ang) * spd + 1.2
        self.player[4] = None
        self.burst(self.player[0], self.player[1], GOLD, 6)

    def burst(self, x, y, col, n=8):
        for _ in range(n):
            a = random.uniform(0, 6.28)
            sp = random.uniform(2, 9)
            self.sparks.append([x, y, math.cos(a)*sp, math.sin(a)*sp, 16, col])

    def tick(self):
        self.t += 1
        self.flash = max(0, self.flash - 1)
        x, y, vx, vy, peg, ang = self.player
        if peg:
            ang += 0.045
            self.player[5] = ang
            rad = 140
            x = peg[0] + math.cos(ang) * rad
            y = peg[1] + math.sin(ang) * rad
            self.player[0], self.player[1] = x, y
        else:
            vy += 0.22
            x += vx
            y += vy
            vx *= 0.992
            if x < 40 or x > W-40:
                vx *= -0.7
                x = max(40, min(W-40, x))
            if y > H-80:
                y = 300
                vy = -4
                vx *= 0.5
                self.combo = 0
            self.player[0], self.player[1], self.player[2], self.player[3] = x, y, vx, vy
        for o in self.orbs:
            if math.hypot(o[0]-x, o[1]-y) < 36:
                self.score += 25 + self.combo * 5
                self.combo += 1
                self.flash = 6
                self.burst(o[0], o[1], MINT, 12)
                o[0] = random.randint(80, W-80)
                o[1] = random.randint(400, 1650)
        for s in self.spikes:
            if math.hypot(s[0]-x, s[1]-y) < 40:
                self.combo = 0
                self.burst(x, y, ROSE, 10)
                self.player[0], self.player[1] = W//2, 350
                self.player[2] = self.player[3] = 0
                self.player[4] = None
        for s in self.spikes:
            s[0] += math.sin(self.t * 0.03 + s[1]) * 1.4
            s[0] = max(50, min(W-50, s[0]))
        for p in self.sparks:
            p[0] += p[2]; p[1] += p[3]; p[4] -= 1
        self.sparks = [p for p in self.sparks if p[4] > 0]
        self.trail.append((int(x), int(y)))
        if len(self.trail) > 18:
            self.trail.pop(0)
        for e in self.stars:
            e[1] -= e[2]
            if e[1] < 0:
                e[1] = H
                e[0] = random.randint(0, W)

    def draw(self, surf):
        surf.fill(VOID)
        for e in self.stars:
            pygame.draw.circle(surf, e[3], (int(e[0]), int(e[1])), 2)
        pygame.draw.rect(surf, DEEP, (30, 200, W-60, H-280), border_radius=24)
        pygame.draw.rect(surf, APATITE, (30, 200, W-60, H-280), 3, border_radius=24)
        for px, py, r in self.pegs:
            pygame.draw.circle(surf, PEG, (int(px), int(py)), r)
            pygame.draw.circle(surf, WHITE, (int(px), int(py)), r, 3)
            pygame.draw.circle(surf, GOLD, (int(px), int(py)), 6)
        for sx, sy, sr in self.spikes:
            pts = [(sx, sy-sr), (sx+sr*0.7, sy+sr*0.4), (sx-sr*0.7, sy+sr*0.4)]
            pygame.draw.polygon(surf, SPIKE, pts)
            pygame.draw.polygon(surf, ROSE, pts, 2)
        for ox, oy, orad, _ in self.orbs:
            pygame.draw.circle(surf, MINT, (int(ox), int(oy)), orad)
            pygame.draw.circle(surf, WHITE, (int(ox), int(oy)), orad, 2)
            pygame.draw.circle(surf, GOLD, (int(ox)-4, int(oy)-4), 5)
        for i, (tx, ty) in enumerate(self.trail):
            pygame.draw.circle(surf, APATITE, (tx, ty), 4 + i//3)
        px, py = int(self.player[0]), int(self.player[1])
        if self.player[4]:
            peg = self.player[4]
            pygame.draw.line(surf, GOLD, (int(peg[0]), int(peg[1])), (px, py), 4)
        pygame.draw.circle(surf, APATITE, (px, py), 20)
        pygame.draw.circle(surf, WHITE, (px, py), 20, 3)
        pygame.draw.circle(surf, GOLD, (px-6, py-6), 6)
        for p in self.sparks:
            pygame.draw.circle(surf, p[5], (int(p[0]), int(p[1])), max(2, p[4]//3))
        if self.flash:
            ov = pygame.Surface((W, H), pygame.SRCALPHA)
            ov.fill((72, 220, 255, 40))
            surf.blit(ov, (0, 0))
        title = self.font_lg.render(TITLE, True, APATITE)
        surf.blit(title, title.get_rect(center=(W//2, 78)))
        sub = self.font_sm.render(HANDLE, True, ROSE)
        surf.blit(sub, sub.get_rect(center=(W//2, 132)))
        sc = self.font.render(f"SCORE  {self.score}", True, WHITE)
        cb = self.font_sm.render(f"STREAK  x{self.combo}", True, GOLD)
        hint = self.font_sm.render("space grapple  auto swing", True, MINT)
        surf.blit(sc, sc.get_rect(center=(W//2, H-140)))
        surf.blit(cb, cb.get_rect(center=(W//2, H-88)))
        surf.blit(hint, hint.get_rect(center=(W//2, H-42)))

    def play_interactive(self):
        running = True
        while running:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                    running = False
                elif ev.type == pygame.KEYDOWN and ev.key in (pygame.K_SPACE, pygame.K_UP):
                    if self.player[4]:
                        self.release()
                    else:
                        np = self.nearest_peg(self.player[0], self.player[1])
                        if np:
                            self.attach(np)
            self.tick()
            self.draw(self.screen)
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()

    def record(self):
        frames = FPS * SECS
        cmd = [
            "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
            "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "20", "-preset", "fast", "-movflags", "+faststart",
            OUT,
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        canvas = pygame.Surface((W, H))
        try:
            for i in range(frames):
                self.autoplay()
                self.tick()
                self.draw(canvas)
                proc.stdin.write(pygame.image.tostring(canvas, "RGB"))
                if i % 30 == 0:
                    print(f"frame {i}/{frames}", flush=True)
        finally:
            proc.stdin.close()
            err = proc.stderr.read().decode("utf-8", "ignore")
            rc = proc.wait()
        if rc != 0:
            raise SystemExit(f"ffmpeg failed ({rc}):\n{err[-1200:]}")
        print("wrote", OUT)
        pygame.quit()

def main():
    g = Game()
    if PLAY and not RECORD:
        g.play_interactive()
    else:
        g.record()

if __name__ == "__main__":
    main()
