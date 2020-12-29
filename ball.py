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
        self.window = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Asteroids")
        self.surface = pygame.Surface([width, height])
        self.surface.fill(BG_COLOR)

    def run(self):
        running = True
        spritelist = [Asteroid.random(self.width, self.height) for _ in range(10)]
        asteroids = pygame.sprite.Group(spritelist)
        player = Player(
            pos=[self.width/2, self.height/2],
            direction=[0,-1],
            speed=0,
            size=60,
        )

        p_group = pygame.sprite.Group(player)

        clock = pygame.time.Clock()
        fps = 60
        rotate_speed = 3.5

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
                    if event.key == pygame.K_SPACE and player_dying_delay == 0 and len(bullets) < bullet_capacity:
                        bullets.append(Bullet(player.x, player.y, player.dir))
                    if event.key == pygame.K_LSHIFT:
                        hyperspace = 30
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_UP:
                        player.thrust = False
                    if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                        player.rotate_speed = 0

            dt = clock.tick(fps)

            for a, b in combinations(asteroids, r=2):
                if pygame.sprite.collide_circle(a, b):
                    a.collide(b)

            for ball in spritelist:
                ball.update(dt)

            player.update(dt)

            game.window.blit(game.surface, [0, 0])
            asteroids.draw(game.window)
            p_group.draw(game.window)

            pygame.display.update()

        pygame.quit()

class Object(pygame.sprite.Sprite):

    def __init__(self, pos, direction, speed, size):
        super().__init__()
        # pygame attributes used by group.draw
        self.image = pygame.Surface([size, size])
        self.image.set_colorkey(BG_COLOR)
        self.rect = self.image.get_rect()


        self.position = pos
        self.direction = Vec(*direction)
        self.speed = speed

        self.size = size
        self.draw()

    def draw(self):
        self.image.fill(BG_COLOR)
        # pygame.draw.circle(self.image, C.silver, (self.size/2, self.size/2), self.size/2)


    @property
    def velocity(self):
        assert isinstance(self.direction, Vec)
        return self.direction * self.speed

    @velocity.setter
    def velocity(self, value):
        assert isinstance(value, Vec)
        self.speed = value.norm()
        self.direction = value.normalize()

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

    def wall_collision(self):
        width, height = self.image.get_width(), self.image.get_height()
        if self.x > game.width - (width / 2):
            self.x = -(width / 2)
        elif self.x < -(width / 2):
            self.x = game.width - (width / 2)

        if self.y > game.height - (height / 2):
            self.y = -(height / 2)
        elif self.y < -(height / 2):
            self.y = game.height - (height / 2)

    def update(self, dt):
        self.wall_collision()
        self.move(dt)



Line = namedtuple('Line', ['color', 'start_pos', 'end_pos', 'width'])


class Player(Object):
    _max_speed = 0.7
    _acceleration = 0.0005

    def __init__(self, pos, direction, speed, size):
        self.axis = Vec(*direction)
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

        super().__init__(pos, direction, speed, size)

    @property
    def thrust(self):
        return self._thrust

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
        if self.thrust and self.velocity.norm() < self._max_speed:
            self.speed += (self._acceleration * dt)
        elif not self.thrust and self.speed > 0:
            self.speed -= (self._acceleration * dt) / 100
        elif not self.thrust:
            self.speed = 0

        if self.rotate_speed:
            self.direction = self.direction.rotate(self.rotate_speed)
            self.draw()

class Asteroid(Object):
    _draw_boxes = False

    def __init__(self, pos, direction, speed, radius, mass):
        super().__init__(pos, direction, speed, radius*2)
        pygame.draw.circle(self.image, C.white, (radius, radius), radius, width=2)
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

    @classmethod
    def random(cls, width, height):
        mass = random.choice([100.0,90.0,80.0,70.0])
        direction = [random.uniform(-1, 1), random.uniform(-1, 1)]
        return cls(
            pos=[random.randint(0, width), random.randint(0, height)],
            direction=direction,
            speed=random.uniform(0.0, 0.5),
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


if __name__ == "__main__":
    game = Game(640*2, 480*2)
    game.run()

