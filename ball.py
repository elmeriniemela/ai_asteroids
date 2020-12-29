#!/usr/bin/env python3
from itertools import combinations
import random
import math
from collections import namedtuple

import pygame

from vector import Vector as Vec
import colors as C

BG_COLOR = C.black

class Game:
    def __init__(self, width, height):
        self.width, self.height = width, height
        self.window = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Asteroids")
        self.surface = pygame.Surface([width, height])
        self.surface.fill(BG_COLOR)
        self.groups = []

    def update(self, dt):
        self.window.blit(self.surface, [0, 0])
        for group in self.groups:
            group.update(dt, window_mode=(self.width, self.height))
            group.draw(self.window)
        pygame.display.update()

    def group(self, *sprites):
        group = pygame.sprite.Group(*sprites)
        self.groups.append(group)
        return group

    def run(self):
        running = True
        player = Player(
            pos=[self.width/2, self.height/2],
            velocity=[0,0],
            size=60,
        )
        self.group(player)

        asteroids = self.group(Asteroid.random(self.width, self.height) for _ in range(10))
        bullets = self.group()

        clock = pygame.time.Clock()
        fps = 60
        rotate_speed = 3.5
        bullet_speed = 1.0

        while running is True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        player.thrust = True
                    if event.key == pygame.K_LEFT:
                        player.rotate_speed = -rotate_speed
                    if event.key == pygame.K_RIGHT:
                        player.rotate_speed = rotate_speed
                    if event.key == pygame.K_SPACE:
                        bullets.add(Bullet(player.cannon, (player.direction * bullet_speed) + player.velocity))

                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_UP:
                        player.thrust = False
                    if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                        player.rotate_speed = 0

            dt = clock.tick(fps)

            for a, b in combinations(asteroids, r=2):
                if pygame.sprite.collide_circle(a, b):
                    a.collide(b)

            self.update(dt)

        pygame.quit()

class Object(pygame.sprite.Sprite):

    def __init__(self, pos, velocity, size):
        super().__init__()
        # pygame attributes used by group.draw
        self.image = pygame.Surface([size, size])
        self.image.set_colorkey(BG_COLOR)
        self.rect = self.image.get_rect()
        self.position = pos
        self.velocity = Vec(*velocity)
        self.size = size

    def draw(self):
        self.image.fill(BG_COLOR)
        # pygame.draw.circle(self.image, C.silver, (self.size/2, self.size/2), self.size/2)

    def add_internal(self, group):
        """
        Overwrite for initial draw.
        """
        self.draw()
        return super().add_internal(group)

    @property
    def position(self):
        assert isinstance(self._pos, Vec)
        return self._pos

    @position.setter
    def position(self, value):
        # Using only rect.x and rect.y causes weird behaviour
        self._pos = Vec(*value)
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
        self.position += self.velocity * dt

    def wall_collision(self, window_mode):
        max_width, max_height = window_mode
        width, height = self.image.get_width(), self.image.get_height()
        if self.x > max_width - (width / 2):
            self.x = -(width / 2)
        elif self.x < -(width / 2):
            self.x = max_width - (width / 2)

        if self.y > max_height - (height / 2):
            self.y = -(height / 2)
        elif self.y < -(height / 2):
            self.y = max_height - (height / 2)

    def update(self, dt, window_mode):
        self.wall_collision(window_mode)
        self.move(dt)

class Bullet(Object):
    def __init__(self, pos, velocity):
        self.radius = 2.0
        super().__init__(pos, velocity, size=self.radius*2)
        self.ttl = 250

    def draw(self):
        super().draw()
        r = self.radius
        pygame.draw.circle(self.image, C.white, (r, r), r)


    def update(self, dt, window_mode):
        super().update(dt, window_mode)
        self.ttl -= dt
        if self.ttl < 0:
            self.kill()


Line = namedtuple('Line', ['color', 'start_pos', 'end_pos', 'width'])


class Player(Object):
    _max_speed = 0.7
    _acceleration = 0.0005

    def __init__(self, pos, velocity, size):
        self.axis = Vec(0, -1)
        self.direction = Vec(0, -1)
        self._thrust = False
        self.rotate_speed = 0.0
        width = 2
        color = C.white
        s = size
        r = size/2



        def clockAngle(r, theta):
            rad = math.radians(theta - 90 % 360)
            return Vec(r + r*math.cos(rad), r+r*math.sin(rad))

        wingtip1 = clockAngle(r, 135)
        wingtip2 = clockAngle(r, -135)
        nose = Vec(r, 0)
        backtip1 = wingtip1 * 0.95
        backtip2 = wingtip2 * 0.95
        thrust = Vec(r, backtip1.y)

        # For some reason the back is off by 1 pixel on the x-axis
        backtip1[0] += 1.0
        backtip2[0] += 1.0

        self.standby_lines = [
            Line(color, Vec(r, 0), Vec(r,r), width ),
            Line(
                color=color,
                start_pos=nose,
                end_pos=wingtip1,
                width=width,
            ),
            Line(
                color=color,
                start_pos=nose,
                end_pos=wingtip2,
                width=width,
            ),
            Line(
                color=color,
                start_pos=backtip1,
                end_pos=backtip2,
                width=width,
            ),
        ]
        self.thrust_lines = [
            Line(
                color=C.red,
                start_pos=thrust,
                end_pos=Vec(r, 2*r),
                width=size//20,
            ),
        ]

        super().__init__(pos, velocity, size)

    @property
    def thrust(self):
        return self._thrust

    @property
    def cannon(self):
        return self.position + self.transform(Vec(self.size/2, 0))

    @thrust.setter
    def thrust(self, value):
        self._thrust = value
        self.draw()


    def transform(self, point):
        return point.rotate_origin(self.angle(), origin=Vec(self.size/2, self.size/2))


    def draw(self):
        super().draw()
        # Draw player
        lines = self.standby_lines[:]
        if self.thrust:
            lines += self.thrust_lines[:]

        for line in lines:
            pygame.draw.line(
                surface=self.image,
                color=line.color,
                start_pos=self.transform(line.start_pos),
                end_pos=self.transform(line.end_pos),
                width=line.width,
            )


    def angle(self, radians=False):
        angle = self.axis.directional_angle2D(self.direction, radians=radians)
        return angle

    def move(self, dt):
        super().move(dt)
        if self.thrust:
            dv = self.direction * (self._acceleration * dt)
            if (self.velocity + dv).norm() < self._max_speed:
                self.velocity += dv

        if self.rotate_speed:
            self.direction = self.direction.rotate(self.rotate_speed)
            self.draw()

class Asteroid(Object):
    _draw_boxes = False

    def __init__(self, pos, velocity, radius, mass):
        super().__init__(pos, velocity, radius*2)
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
                        color=C.white,
                        closed=True,
                        points=lines,
                        width=3,
                    )

        self.radius = radius
        self.mass = mass


    def draw(self):
        super().draw()
        r = self.radius
        pygame.draw.circle(self.image, C.white, (r, r), r, width=2)

    @classmethod
    def random(cls, width, height):
        mass = random.choice([100.0,90.0,80.0,70.0])
        speed = 0.5
        velocity = [random.uniform(-speed, speed), random.uniform(-speed, speed)]
        return cls(
            pos=[random.randint(0, width), random.randint(0, height)],
            velocity=velocity,
            radius=mass / 2,
            mass=mass
        )

    @property
    def origin(self):
        return Vec(self.x + self.radius, self.y + self.radius)

    def collide(self, other):
        normal = (self.origin - other.origin).normalize()
        tangent = normal.perpendicular()

        self.position += normal
        other.position -= normal

        v1n = normal * self.velocity
        v2n = normal * other.velocity
        v1t = tangent * self.velocity
        v2t = tangent * other.velocity

        # Calculate new velocity scalars on the collision normal
        normal_speed1 = normal * (v1n * (self.mass - other.mass) + 2 * other.mass * v2n) / (self.mass + other.mass)
        normal_speed2 = normal * (v2n * (other.mass - self.mass) + 2 * self.mass * v1n) / (self.mass + other.mass)

        # Tangent velocity stays the same
        tangent_speed1 = v1t * tangent
        tangent_speed2 = v2t * tangent

        self.velocity = normal_speed1 + tangent_speed1
        other.velocity = normal_speed2 + tangent_speed2


def main():
    game = Game(640*2, 480*2)
    game.run()

if __name__ == "__main__":
    main()
