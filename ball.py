#!/usr/bin/env python3
from itertools import combinations
import random

import pygame

import vector
import colors as C


class Game:
    def __init__(self, width, height):
        self.window_size = width, height
        self.window = pygame.display.set_mode(self.window_size)
        pygame.display.set_caption("Asteroids")
        self.surface = pygame.Surface([width, height])
        self.surface.fill(C.white)

    def run(self):
        running = True
        spritelist = [Asteroid.random(*self.window_size) for _ in range(10)]
        group = pygame.sprite.Group(spritelist)

        clock = pygame.time.Clock()
        fps = 60

        while running is True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            dt = clock.tick(fps)

            for a, b in combinations(group, r=2):
                if pygame.sprite.collide_circle(a, b):
                    a.collide(b)

            for ball in spritelist:
                ball.update(dt)

            game.window.blit(game.surface, [0, 0])
            group.draw(game.window)

            pygame.display.update()

        pygame.quit()

class Object(pygame.sprite.Sprite):

    def __init__(self, pos, speed, width, height):
        super().__init__()
        self.image = pygame.Surface([width, height])
        self.image.fill(C.white)
        self.image.set_colorkey(C.white)
        self.rect = self.image.get_rect()
        self.position = pos
        self.speed = vector.Vector(*speed)


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

    def move(self, dt):
        self.position += self.speed * dt

    def wall_collision(self):
        max_width, max_height = game.window_size
        width, height = self.image.get_width(), self.image.get_height()
        if self.x > max_width - (width / 2):
            self.x = -(width / 2)
        elif self.x < -(width / 2):
            self.x = max_width - (width / 2)

        if self.y > max_height - (height / 2):
            self.y = -(height / 2)
        elif self.y < -(height / 2):
            self.y = max_height - (height / 2)

    def update(self, dt):
        self.wall_collision()
        self.move(dt)


class Player(Object):
    pass



class Asteroid(Object):
    _draw_boxes = False

    def __init__(self, pos, speed, radius, mass, color=C.red):
        super().__init__(pos, speed, radius*2, radius*2)
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

        self.radius = radius
        self.mass = mass

    @classmethod
    def random(cls, width, height):
        mass = random.choice([100.0,90.0,80.0,70.0])
        speed_limit = 0.5
        return cls(
            pos=[random.randint(0, width), random.randint(0, height)],
            speed=[random.uniform(-speed_limit, speed_limit), random.uniform(-speed_limit, speed_limit)],
            radius=mass / 2,
            mass=mass
        )

    @property
    def origin(self):
        return vector.Vector(self.x + self.radius, self.y + self.radius)

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
    window_size = (640*2, 480*2)
    game = Game(*window_size)
    game.run()

