import pygame 
import time

# GUI



#OOP
pygame.init()

class GameState:
    def __init__(self):
        self.money = 0
        self.car_type = None
        self.floating_texts = []
        
    def add_score(self, money, x=None, y=None, color='white'):
        bonus_money = int(money * self.score_multiplier)
        self.money += bonus_money
        if x is not None and y is not None:
            self.add_floating_text(f"+{bonus_money}", x, y, color)
    
    def add_floating_text(self, text, x, y, color='white', duration=2.0):
        self.floating_texts.append({
            'text': text,
            'x': x,
            'y': y,
            'color': color,
            'start_time': time.time(),
            'duration': duration,
            'vel_y': -30
        })
    
    def update_floating_texts(self, delta_time):
        current_time = time.time()
        for text in self.floating_texts[:]:  # loop over a copy
            elapsed = current_time - text['start_time']
            if elapsed >= text['duration']:
                self.floating_texts.remove(text)  # safe to remove from the original
            else:
                text['y'] += text['vel_y'] * delta_time
                text['vel_y'] *= 0.98


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
   
    def draw(self, screen):
        pass
    
    def get_position(self):
        return (self.x, self.y)


class FallingObjects:
    def __init__(self, fall_speed=5):
        self.fall_speed = fall_speed
    
    def update_fall_speed(self, new_speed):
        self.fall_speed = new_speed


class player(GameObject):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)
        self.speed = 5
        self.color = 'tomato3'
        self.coin_timers = []
        self.spike_timers = []




# running
screen = pygame.display.set_mode((1280, 720))
clock = pygame.time.Clock()
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    screen.fill("crimson")
    pygame.display.flip()
    clock.tick(60)
pygame.quit()