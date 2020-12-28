#!/usr/bin/env python3
from itertools import combinations
import random

import pygame

import vector
import colors as C


class Game:
    def __init__(self, width, height):
        self.width, self.height = width, height
        self.window = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Asteroids")
        self.surface = pygame.Surface([width, height])
        self.surface.fill(C.white)

    def run(self):
        running = True
        spritelist = [Asteroid.random(self.width, self.height) for _ in range(10)]
        asteroids = pygame.sprite.Group(spritelist)
        player = Player(
            pos=[self.width/2, self.height/2],
            direction=[0,-1],
            speed=0,
            width=30,
            height=60,
        )

        p_group = pygame.sprite.Group(player)

        clock = pygame.time.Clock()
        fps = 60
        rotate_speed = 1.5

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

    def __init__(self, pos, direction, speed, width, height):
        super().__init__()
        self.image = pygame.Surface([width, height])
        self.image.fill(C.white)
        self.image.set_colorkey(C.white)
        self.rect = self.image.get_rect()
        self.position = pos
        self.direction = direction
        self.speed = speed


    @property
    def velocity(self):
        return vector.Vector(*self.direction) * self.speed

    @velocity.setter
    def velocity(self, value):
        assert isinstance(value, vector.Vector)
        self.speed = value.norm()
        self.direction = value.normalize()

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


class Player(Object):
    _max_speed = 0.7
    _acceleration = 0.0005

    def __init__(self, pos, direction, speed, width, height):
        super().__init__(pos, direction, speed, width, height)
        line_width = 6
        pygame.draw.polygon(
            surface=self.image,
            color=C.black,
            points=[
                (line_width, height-line_width),
                (width/2, line_width),
                (width-line_width, height-line_width)
            ],
            width=line_width,
        )

        self.thrust = False
        self.rotate_speed = 0.0



    def move(self, dt):
        super().move(dt)
        if self.thrust and self.velocity.norm() < self._max_speed:
            self.speed += (self._acceleration * dt)

        if self.rotate_speed:
            self.image = pygame.transform.rotate(self.image, self.rotate_speed)


class Asteroid(Object):
    _draw_boxes = False

    def __init__(self, pos, direction, speed, radius, mass, color=C.red):
        super().__init__(pos, direction, speed, radius*2, radius*2)
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
                        color=C.black,
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
        return vector.Vector(self.x + self.radius, self.y + self.radius)

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

