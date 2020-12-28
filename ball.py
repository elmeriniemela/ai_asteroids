import vector
from colors import *


class Game:
    def __init__(self, width, height):
        self.window_size = width, height
        self.window = pygame.display.set_mode(self.window_size)
        self.surface = pygame.Surface([width, height])
        self.surface.fill(white)


class Ball(pygame.sprite.Sprite):
    def __init__(self, pos, speed, radius, mass, color=red):
        super().__init__()
        self.image = pygame.Surface([radius * 2, radius * 2])
        self.image.fill(white)
        self.image.set_colorkey(white)
        pygame.draw.circle(self.image, color, (radius, radius), radius, )
        self.origin = pos[0] + radius, pos[1] + radius
        self.pos = pos
        self.rect = self.image.get_rect()
        self.radius = radius
        self.speed = speed
        self.set_position(pos)
        self.mass = mass
        print("init")

    def set_position(self, pos):
        self.rect.x = pos[0]
        self.rect.y = pos[1]
        self.origin = pos[0] + self.radius, pos[1] + self.radius
        self.pos = pos

    def move(self):
        self.pos = vector.plus(self.pos, self.speed)
        self.set_position(self.pos)

    def wall_collision(self):

        if self.pos[0] > game.window_size[0] - self.image.get_width():
            self.pos[0] = game.window_size[0] - self.image.get_width()
            self.speed[0] = -self.speed[0]

        if self.pos[0] < 0:
            self.pos[0] = 0
            self.speed[0] = -self.speed[0]

        if self.pos[1] > game.window_size[1] - self.image.get_height():
            self.pos[1] = game.window_size[1] - self.image.get_height()
            self.speed[1] = -self.speed[1]

        if self.pos[1] < 0:
            self.pos[1] = 0
            self.speed[1] = -self.speed[1]

    def update(self):
        self.wall_collision()
        self.move()


def object_collision(sprite1, sprite2):
    normal = [sprite1.origin[0] - sprite2.origin[0], sprite1.origin[1] - sprite2.origin[1]]
    unit_normal = vector.unit(normal)

    unit_tangent = [-unit_normal[1], unit_normal[0]]
    neg_unit_normal = vector.times(-1, unit_normal)

    sprite1.pos = vector.plus(sprite1.pos, unit_normal)
    sprite1.set_position(sprite1.pos)

    sprite2.pos = vector.plus(sprite2.pos, neg_unit_normal)
    sprite2.set_position(sprite2.pos)

    v1n = vector.dotp(unit_normal, sprite1.speed)

    v1t = vector.dotp(unit_tangent, sprite1.speed)

    v2n = vector.dotp(unit_normal, sprite2.speed)

    v2t = vector.dotp(unit_tangent, sprite2.speed)

    u1n = (v1n * (sprite1.mass - sprite2.mass) + 2 * sprite2.mass * v2n) / (sprite1.mass + sprite2.mass)

    u2n = (v2n * (sprite2.mass - sprite1.mass) + 2 * sprite1.mass * v1n) / (sprite1.mass + sprite2.mass)

    sprite1_tangent = vector.times(v1t, unit_tangent)
    sprite1_normal = vector.times(u1n, unit_normal)

    sprite2_tangent = vector.times(v2t, unit_tangent)
    sprite2_normal = vector.times(u2n, unit_normal)

    sprite1.speed = vector.plus(sprite1_tangent, sprite1_normal)
    sprite2.speed = vector.plus(sprite2_tangent, sprite2_normal)

if __name__ == "__main__":

    game = Game(640, 480)
    running = True
    ball01 = Ball(pos=[0, 0], speed=[1, 1], radius=50, mass=500, color=blue)
    ball02 = Ball(pos=[0, 430], speed=[0, 0], radius=50, mass=10, color=red)
    ball03 = Ball(pos=[430, 0], speed=[2, 2], radius=25, mass=5, color=black)
    ball04 = Ball(pos=[330, 0], speed=[2, 2], radius=25, mass=5, color=green)
    ball05 = Ball(pos=[230, 0], speed=[2, 2], radius=25, mass=5, color=gray)

    spritelist = [ball01, ball02, ball03, ball04, ball05]

    group = pygame.sprite.Group(spritelist)

    clock = pygame.time.Clock()
    fps = 120
    # This is so that collision loop doesnt call object_collision twice per collision(there is probably a better way)
    count = 0
    active = 0

    while running is True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        for a in group:
            for b in group:
                if a != b and pygame.sprite.collide_circle(a, b) and count == 0:
                    object_collision(a, b)
                    count = 1
        count = 0

        for ball in spritelist:
            ball.update()

        game.window.blit(game.surface, [0, 0])
        group.draw(game.window)

        clock.tick(fps)
        pygame.display.update()

    pygame.quit()
