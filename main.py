from types import FunctionType
from typing import Sequence, Tuple
import pygame
from pygame.math import clamp, lerp, remap
import random
import math
from perlin_noise import PerlinNoise

vec = pygame.Vector2
frames = 0

# force field
# def d(v: pygame.Vector2, b: pygame.Vector2):
#     x = v.x
#     y = v.y
#     cx = x*x*x - 3.0*x*y*y;
#     cy = y*y*y - 3.0*x*x*y;
#
#     v -= b
#     x = v.x
#     y = v.y
#
#     cx += 3.0*x*x*y - y*y*y;
#     cy += 3.0*x*y*y - x*x*x;
#
#     c=vec(cx,cy)
#     if c.x == 0 and c.y == 0: return c
#     c.scale_to_length(1)
#     return c

    # c = v.copy()
    # if c.x == 0 and c.y == 0: return c
    # c.scale_to_length(10)
    #return c

class Ball:
    def __init__(self, p: pygame.Vector2) -> None:
        self.pos = p
        self.d = vec(0,0)# vec(random.uniform(-1,1), random.uniform(-1,1))
        #self.color = "red" if p.x < 0 else "blue"
        #self.mask = (255,0, 255) if p.x < 0 else (0,0,255)
        self.max_ttl = 20 #120
        self.ttl = self.max_ttl
        self.deleted = False
        #self.surf = pygame.Surface((160,160))
        #self.surf.set_alpha(255)
        #self.surf.set_colorkey((0,0,0))
    def update(self, d: FunctionType):
        dd = d(self.pos)
        self.d += dd#.clamp_magnitude(0.5)
        self.pos += self.d
        #x = lerp(255,0,self.ttl/self.max_ttl)
        x = lerp(0,1,self.ttl/self.max_ttl)
        #self.color = (max(self.mask[0],int(x)), max(self.mask[1],int(x)), max(self.mask[2],int(x)))
        self.color = (int(lerp(200, 255, self.pos.x / 500)), int(lerp(128, 255, self.pos.y / 500)), int(lerp(0, 255, self.pos.x*self.pos.y/500/500)))
        #self.d *= .9
        self.ttl -= 1
        if self.ttl < 0:
            self.deleted = True
        #self.surf.set_alpha(int(x))
        #pygame.draw.circle(self.surf, self.color, self.surf.get_rect().center, 3)
    def draw(self, surf: pygame.Surface, camera):
        #pygame.draw.circle(surf, self.color, self.pos+camera, 15)
        pygame.draw.rect(surf, self.color, (self.pos+camera-(5,5),(10,10)), 0)
        #surf.blit(self.surf, self.surf.get_rect(center=self.pos+camera))

class Spawner:
    def __init__(self, p, balls) -> None:
        #self.balls = balls
        self.pos = p
        self.color = "purple"
        self.frames = 0
    def update(self, balls):
        if self.frames == 0:
            balls.append(Ball(self.pos.copy()))
            self.frames = 1
        self.frames -= 1
    def draw(self, surf: pygame.Surface, camera):
        pygame.draw.circle(surf, self.color, self.pos+camera, 10)

class Attractor:
    def __init__(self, p, r=None) -> None:
        self.pos = p
        self.r = r or random.uniform(15, 55)
        self.color = "orange"
        self.radius_color = "lightblue"
        self.dragging = False
    def update(self, balls, mpos):
        md = self.pos.distance_to(mpos)
        if self.dragging or md < 10:
            self.color = "blue"
            if self.dragging and md < 10:
                self.pos = mpos
        else:
            self.color = "orange"
        if self.dragging or 10 < md < self.r:
            self.radius_color = "blue"
            if self.dragging and 10 < md:
                self.r = max(15, min(md, 500))
                self.r = md
        else:
            self.radius_color = "lightblue"
    def draw(self, surf: pygame.Surface, camera):
        pygame.draw.circle(surf, self.color, self.pos+camera, 10)
        pygame.draw.circle(surf, self.radius_color, self.pos+camera, self.r, width=1)

# def create_vector_field(mpos: pygame.Vector2):
#     def d(pos: pygame.Vector2):
#         return (mpos-pos).clamp_magnitude(10)
#     return d

# def create_vector_field(spawners: Sequence[Attractor]):
#     def d(pos: pygame.Vector2):
#         result = vec(0,0)
#         if len(spawners) == 0:
#             return result
#         total_r = sum([sp.r for sp in spawners])
#         if total_r == 0:
#             return result
#         for sp in spawners:
#             pp = sp.pos-pos
#             if pp.x == 0 and pp.y == 0:
#                 continue
#             result += pp * (1/pp.length_squared()) * (sp.r/total_r)
#         return result.normalize()
#     return d

def create_vector_field_perlin(noise: PerlinNoise, zoff: float, size=Tuple[float,float]):
    def d(pos: pygame.Vector2):
        p = vec(pos.x/size[0],pos.y/size[1])
        n = noise([p.x,p.y,zoff,0], tile_sizes=(1,1,100,1))
        r = noise([p.x,p.y,zoff,1], tile_sizes=(1,1,100,1))
        v = pygame.Vector2()
        v.from_polar((remap(-1,1,.5,5, r), remap(-1, 1, 0, 4*360, n)))
        return v
    return d

def main():
    pygame.init()
    #screen = pygame.display.set_mode((500, 500), pygame.FULLSCREEN|pygame.SCALED)
    screen = pygame.display.set_mode((500, 500))

    clock = pygame.time.Clock()
    running = True

    balls = []
    spawners = []
    attractors = []

    camera = vec(screen.width//2,screen.height//2)

    frames = 0
    dragging = None
    noise = PerlinNoise(octaves=10)

    zoff = 0

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        (b1, _, b3, _, _) = pygame.mouse.get_just_pressed()
        mx, my = pygame.mouse.get_pos()
        mpos = vec(mx,my)-camera

        (d1, _, _) = pygame.mouse.get_pressed()

        simregion = screen.get_rect(center=(0,0)).scale_by(2)
        balls = [ball for ball in balls if not ball.deleted and simregion.collidepoint(ball.pos)]
        #d = create_vector_field(attractors)
        d = create_vector_field_perlin(noise, zoff, screen.get_size())
        zoff+=0.0005

        if dragging and not d1:
            dragging.dragging = False
            dragging = None

        for sp in attractors:
            if dragging is None and sp.pos.distance_to(mpos) < sp.r:
                if d1:
                    dragging = sp
                    sp.dragging = True
            sp.update(balls, mpos)

        if not dragging:
            if b1:
                attractors.append(Attractor(mpos))
            elif b3:
                spawners.append(Spawner(mpos, balls))

        for sp in spawners:
            sp.update(balls)
        for ball in balls:
            ball.update(d)

        screen.fill((230,230,230))
        #screen.fill("blue")

        if False:
            grid_size = 50
            for y in range(0, screen.height, grid_size):
                for x in range(0, screen.width, grid_size):
                    pos = vec(x,y)
                    pygame.draw.line(screen, (0,0,0), pos, pos+d(pos-camera) * 10, width=1)

        if False:
            for sp in attractors:
                sp.draw(screen, camera)
            for sp in spawners:
                sp.draw(screen, camera)
        #buffer = pygame.Surface(screen.get_rect().size)
        #buffer.set_colorkey((0,0,0))
        for ball in balls:
            ball.draw(screen, camera)
        #screen.blit(buffer)

        # flip() the display to put your work on screen
        pygame.display.flip()
        pygame.display.set_caption(f"fps: {clock.get_fps():.0f}")

        clock.tick(60)  # limits FPS to 60

if __name__ == "__main__":
    main()

