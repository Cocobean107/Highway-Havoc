import pygame 
import pygame_gui
pygame.init()






#OOP
class GameObject:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def draw(self, surface):
        pygame.draw.rect(surface, (255, 0, 0), (self.x, self.y, self.width, self.height))

    def update(self):
        pass


class GameState:
    def __init__(self):
        self.money = 0
        self.car_type = None
        




# running
screen = pygame.display.set_mode((1280, 720))
clock = pygame.time.Clock()
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    screen.fill("grey69")
    pygame.display.flip()
    clock.tick(60)
pygame.quit()