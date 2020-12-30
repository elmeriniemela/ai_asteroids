#!/usr/bin/env python3
from itertools import combinations
import random
import math
from collections import namedtuple

import pygame

from vector import Vector as Vec
import colors as C

BG_COLOR = C.black

class Font(pygame.font.Font):
    def render(self, text, antialias, color, background):
        return super().render(text, antialias, color, background)


def font_constructor(fontpath, size, bold, italic):
    font = Font(fontpath, size)
    if bold:
        font.set_bold(True)
    if italic:
        font.set_italic(True)
    return font


class Game:
    def __init__(self, width, height):
        self.width, self.height = width, height
        self.window = pygame.display.set_mode((width, height))
        self.background = pygame.Surface([width, height])
        self.background.fill(BG_COLOR)
        pygame.display.set_caption("Asteroids")
        pygame.font.init()
        self.font = pygame.font.SysFont('Comic Sans MS', 30, constructor=font_constructor)
        self.reset()
        self.mode = pygame.K_1
        self.modes = {
            pygame.K_1: 'Normal',
            pygame.K_2: 'God mode',
        }

    def reset(self):
        self.groups = []
        self.player = Player(
            pos=[self.width/2, self.height/2],
            velocity=[0,0],
            radius=30,
        )
        self.group(self.player)
        self.asteroids = self.group(Asteroid.random(self.width, self.height) for _ in range(5))
        self.bullets = self.group()


    def update(self, dt):
        self.window.blit(
            source=self.background,
            dest=[0, 0],
        )
        for group in self.groups:
            group.update(dt, window_mode=(self.width, self.height))
            group.draw(self.window)

        score_surface = self.font.render(
            text='Score: %s' % self.player.score,
            antialias=False,
            color=C.white,
            background=None,
        )
        self.window.blit(
            source=score_surface,
            dest=[self.width - score_surface.get_rect().width, 0],
        )

        if self.mode != 1:
            self.window.blit(
                source=self.font.render(
                    text=self.modes[self.mode],
                    antialias=False,
                    color=C.white,
                    background=None,
                ),
                dest=[0, 0],
            )
        pygame.display.update()

    def group(self, *sprites):
        group = pygame.sprite.Group(*sprites)
        self.groups.append(group)
        return group

    def run(self):
        clock = pygame.time.Clock()
        fps = 60
        rotate_speed = 3.5
        bullet_speed = 1.0
        running = True
        while running is True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        self.player.thrust = True
                    if event.key == pygame.K_LEFT:
                        self.player.rotate_speed = -rotate_speed
                    if event.key == pygame.K_RIGHT:
                        self.player.rotate_speed = rotate_speed
                    if event.key == pygame.K_SPACE:
                        self.bullets.add(Bullet(
                            pos=self.player.cannon,
                            velocity=(self.player.direction * bullet_speed) + self.player.velocity),
                        )
                    if event.key in self.modes:
                        self.mode = event.key


                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_UP:
                        self.player.thrust = False
                    if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                        self.player.rotate_speed = 0

            dt = clock.tick(fps)

            for a, b in combinations(self.asteroids, r=2):
                if pygame.sprite.collide_circle(a, b):
                    a.collide(b)

            for bullet in self.bullets:
                for asteroid in self.asteroids:
                    if pygame.sprite.collide_circle(bullet, asteroid):
                        bullet.collide(asteroid, self.asteroids)
                        self.player.score += 1


            die = all([
                not self.player.invincible,
                pygame.sprite.spritecollideany(
                    self.player,
                    self.asteroids,
                    collided=pygame.sprite.collide_circle,
                ),
                self.modes[self.mode] == 'Normal',
            ])

            if die:
                self.reset()

            self.update(dt)

        pygame.quit()

class Object(pygame.sprite.Sprite):

    def __init__(self, pos, velocity, radius):
        super().__init__()
        # pygame attributes used by group.draw
        self.image = pygame.Surface([radius*2, radius*2])
        self.image.set_colorkey(BG_COLOR)
        self.rect = self.image.get_rect()
        self.position = pos
        self.velocity = Vec(*velocity)
        self.radius = radius

    @property
    def origin(self):
        return Vec(self.x + self.radius, self.y + self.radius)

    def draw(self):
        self.image.fill(BG_COLOR)

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
        super().__init__(pos, velocity, radius=2)
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

    def collide(self, asteroid, group):
        self.kill()
        asteroid.kill()
        if asteroid.radius < 20:
            return
        # Split into multiple pieces
        tangent = self.velocity.normalize().perpendicular()

        origin1 = asteroid.position + (tangent * (asteroid.radius / 2))
        origin2 = asteroid.position - (tangent * (asteroid.radius / 2))
        mag = asteroid.velocity.norm() + (self.velocity.norm() * 0.1)

        dir_center = (asteroid.velocity + self.velocity).normalize()
        dir1 = dir_center.rotate(15).normalize()
        dir2 = dir_center.rotate(-15).normalize()

        a1 = Asteroid(
            pos=origin1,
            velocity=dir1 * mag,
            radius=asteroid.radius / 2,
        )
        a2 = Asteroid(
            pos=origin2,
            velocity=dir2 * mag,
            radius=asteroid.radius / 2,
        )
        group.add(a1, a2)


Line = namedtuple('Line', ['color', 'start_pos', 'end_pos', 'width'])


class Player(Object):
    _max_speed = 0.7
    _acceleration = 0.0005

    def __init__(self, pos, velocity, radius):
        super().__init__(pos, velocity, radius)
        self.axis = Vec(0, -1)
        self.direction = Vec(0, -1)
        self._thrust = False
        self.rotate_speed = 0.0
        self.score = 0
        self.invincible = 200

        def clockAngle(r, theta):
            rad = math.radians(theta - 90 % 360)
            return Vec(r + r*math.cos(rad), r+r*math.sin(rad))

        wingtip1 = clockAngle(self.radius, 135)
        wingtip2 = clockAngle(self.radius, -135)
        nose = Vec(self.radius, 0)
        backtip1 = wingtip1 * 0.95
        backtip2 = wingtip2 * 0.95

        # For some reason the back is off by 1 pixel on the x-axis
        backtip1[0] += 1.0
        backtip2[0] += 1.0

        width = 2
        color = C.white
        self.standby_lines = [
            Line(color, Vec(self.radius, 0), Vec(self.radius,self.radius), width ),
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

        thrust_start = Vec(self.radius, backtip1.y)
        thrust_end = Vec(self.radius, 2*self.radius)
        thrust_mid = Vec(self.radius, backtip1.y + (2*self.radius - backtip1.y) * 0.5)

        self.thrust_lines = [
            Line(
                color=C.red,
                start_pos=thrust_start,
                end_pos=thrust_mid,
                width=radius//5,
            ),
             Line(
                color=C.orange,
                start_pos=thrust_mid,
                end_pos=thrust_end,
                width=radius//10,
            ),
        ]


    @property
    def thrust(self):
        return self._thrust

    @property
    def cannon(self):
        return self.position + self.transform(Vec(self.radius, 0))

    @thrust.setter
    def thrust(self, value):
        self._thrust = value
        self.draw()


    def transform(self, point):
        return point.rotate_origin(self.angle(), origin=Vec(self.radius, self.radius))

    def update(self, dt, window_mode):
        super().update(dt, window_mode)
        if self.invincible:
            self.invincible -= dt * 0.1
            if self.invincible < 0:
                self.invincible = 0
            self.draw()

    def draw(self):
        super().draw()
        if self.invincible:
            pygame.draw.circle(self.image, (self.invincible, self.invincible, self.invincible), (self.radius, self.radius), self.radius)
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

    def __init__(self, pos, velocity, radius):
        super().__init__(pos, velocity, radius)
        self.mass = 2*math.pi*radius


    def draw(self):
        super().draw()
        pygame.draw.circle(self.image, C.white, (self.radius, self.radius), self.radius, width=2)

    @classmethod
    def random(cls, width, height):
        radius = random.choice([100.0,90.0,80.0,70.0])
        speed = 0.2
        velocity = [random.uniform(-speed, speed), random.uniform(-speed, speed)]
        return cls(
            pos=[random.randint(0, width), random.randint(0, height)],
            velocity=velocity,
            radius=radius,
        )

    def collide(self, other):
        normal = (self.origin - other.origin).normalize()
        overlap = (self.radius + other.radius) - (self.origin - other.origin).norm()
        tangent = normal.perpendicular()

        self.position += normal * overlap / 2
        other.position -= normal * overlap / 2

        assert (self.origin - other.origin).norm() - (self.radius + other.radius) < 1e-10, \
            "Collision between asteroids left them overlapping."

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
