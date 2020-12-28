#!/usr/bin/env python3
from itertools import combinations

import vector
from colors import *


class Game:
    def __init__(self, width, height):
        self.window_size = width, height
        self.window = pygame.display.set_mode(self.window_size)
        pygame.display.set_caption("Asteroids")
        self.surface = pygame.Surface([width, height])
        self.surface.fill(white)


class Ball(pygame.sprite.Sprite):
    _wrap_walls = False
    _draw_boxes = False

    def __init__(self, pos, speed, radius, mass, color=red):
        super().__init__()
        self.image = pygame.Surface([radius * 2, radius * 2])
        self.image.fill(white)
        self.image.set_colorkey(white)
        pygame.draw.circle(self.image, color, (radius, radius), radius)

        if self._draw_boxes:
            N = 3
            step = (radius*2)/N
            for y in range(N):
                for x in range(N):
                    lines = [
                        (x*step, y*step),
                        ((x+1)*step, y*step),
                        ((x+1)*step, (y+1)*step),
                        (x*step, (y+1)*step),
                    ]

                    pygame.draw.lines(
                        surface=self.image,
                        color=black,
                        closed=True,
                        points=lines,
                        width=3,
                    )

        self.rect = self.image.get_rect()
        self.radius = radius
        self.speed = vector.Vector(*speed)
        self.position = pos
        self.mass = mass


    @property
    def origin(self):
        return vector.Vector(self.x + self.radius, self.y + self.radius)

    @property
    def position(self):
        return vector.Vector(*self._pos)

    @position.setter
    def position(self, value):
        # Using only rect.x and rect.y causes weird behaviour
        self._pos = value
        self.rect.x, self.rect.y = value

    @property
    def x(self):
        return self._pos[0]

    @x.setter
    def x(self, value):
        self.position = value, self.y

    @property
    def y(self):
        return self._pos[1]

    @y.setter
    def y(self, value):
        self.position = self.x, value

    def move(self):
        self.position += self.speed

    def wall_collision(self):
        max_width, max_height = game.window_size
        width, height = self.image.get_width(), self.image.get_height()

        if self._wrap_walls:
            if self.x > max_width - (width / 2):
                self.x = -(width / 2)
            elif self.x < -(width / 2):
                self.x = max_width - (width / 2)

            if self.y > max_height - (height / 2):
                self.y = -(height / 2)
            elif self.y < -(height / 2):
                self.y = max_height - (height / 2)
        else:
            if self.x > max_width - width:
                self.x = max_width - width
                self.speed[0] = -self.speed[0]

            if self.x < 0:
                self.x = 0
                self.speed[0] = -self.speed[0]

            if self.y > max_height - height:
                self.y = max_height - height
                self.speed[1] = -self.speed[1]

            if self.y < 0:
                self.y = 0
                self.speed[1] = -self.speed[1]

    def update(self):
        self.wall_collision()
        self.move()

    def collide(self, other):
        normal = (self.origin - other.origin).normalize()
        tangent = normal.perpendicular()

        self.position += normal
        other.position -= normal

        v1n = normal * self.speed
        v2n = normal * other.speed
        v1t = tangent * self.speed
        v2t = tangent * other.speed

        # Calculate new speed scalars on the collision normal
        normal_speed1 = normal * (v1n * (self.mass - other.mass) + 2 * other.mass * v2n) / (self.mass + other.mass)
        normal_speed2 = normal * (v2n * (other.mass - self.mass) + 2 * self.mass * v1n) / (self.mass + other.mass)

        # Tangent speed stays the same
        tangent_speed1 = v1t * tangent
        tangent_speed2 = v2t * tangent

        self.speed = normal_speed1 + tangent_speed1
        other.speed = normal_speed2 + tangent_speed2


if __name__ == "__main__":

    game = Game(640, 480)
    running = True
    ball01 = Ball(pos=[0, 0], speed=[1, 1], radius=50, mass=500, color=blue)
    ball02 = Ball(pos=[0, 380], speed=[0, 0], radius=50, mass=10, color=red)
    ball03 = Ball(pos=[430, 0], speed=[2, 2], radius=25, mass=5, color=black)
    ball04 = Ball(pos=[330, 0], speed=[2, 2], radius=25, mass=5, color=green)
    ball05 = Ball(pos=[230, 0], speed=[2, 2], radius=25, mass=5, color=gray)

    spritelist = [ball01, ball02, ball03, ball04, ball05]

    group = pygame.sprite.Group(spritelist)

    clock = pygame.time.Clock()
    fps = 120

    while running is True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False


        for a, b in combinations(group, r=2):
            if pygame.sprite.collide_circle(a, b):
                a.collide(b)

        for ball in spritelist:
            ball.update()

        game.window.blit(game.surface, [0, 0])
        group.draw(game.window)

        clock.tick(fps)
        pygame.display.update()

    pygame.quit()
