import math

def distance_xy(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)

def is_fist(lm):
    tips = [8, 12, 16, 20]
    pips = [6, 10, 14, 18]
    return all(lm[t].y > lm[p].y for t, p in zip(tips, pips))

def is_open_palm(lm):
    tips = [8, 12, 16, 20]
    pips = [6, 10, 14, 18]
    return all(lm[t].y < lm[p].y for t, p in zip(tips, pips))

def is_pinch_thumb_index(lm, thresh=0.05):
    return distance_xy(lm[4], lm[8]) < thresh

def is_pinch_thumb_middle(lm, thresh=0.05):
    return distance_xy(lm[4], lm[12]) < thresh

def map_to_screen(nx, ny, frame_w, frame_h, screen_w, screen_h):
    sx = int(min(max(nx * screen_w, 0), screen_w - 1))
    sy = int(min(max(ny * screen_h, 0), screen_h - 1))
    return sx, sy

class EMA2D:
    def __init__(self, alpha=0.25):
        self.alpha = alpha
        self.x = None
        self.y = None
    def update(self, x, y):
        if self.x is None:
            self.x, self.y = x, y
        else:
            self.x += (x - self.x) * self.alpha
            self.y += (y - self.y) * self.alpha
        return int(self.x), int(self.y)
