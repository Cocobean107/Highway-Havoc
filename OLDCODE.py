import asyncio
import platform
import pygame
import sys
import random
import time
import math

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Racing Game")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

# Road settings
ROAD_WIDTH = 400
ROAD_X = (SCREEN_WIDTH - ROAD_WIDTH) // 2
LANE_WIDTH = ROAD_WIDTH // 4

# Load sounds (assuming coin.mp3 and spike.mp3 are available)
try:
    coin_sound = pygame.mixer.Sound('coin.mp3')
    spike_sound = pygame.mixer.Sound('spike.mp3')
except FileNotFoundError:
    coin_sound = None
    spike_sound = None

class GameObjects:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
    
    def draw(self, screen):
        pass
    
    def get_position(self):
        return (self.x, self.y)

class FallingObjects:
    def __init__(self, fall_speed=5):
        self.fall_speed = fall_speed
    
    def update_fall_speed(self, new_speed):
        self.fall_speed = new_speed

class Car(GameObjects):
    def __init__(self, x, y, width, height, player_id):
        super().__init__(x, y, width, height)
        self.player_id = player_id
        self.speed = 0
        self.base_speed = 0
        self.color = BLUE
        self.boost_timers = []
        self.spike_timers = []
        self.lane = 2  # Start in second lane (0-based indexing)
        self.target_x = ROAD_X + self.lane * LANE_WIDTH + LANE_WIDTH // 2 - self.width // 2
        self.flash_color = None
        self.flash_end_time = 0
        self.last_coin_time = 0
        self.last_spike_time = 0
        self.last_spike_decrease = 0
    
    def move(self, direction):
        new_lane = self.lane + direction
        if 0 <= new_lane < 4:  # Ensure car stays within 4 lanes
            self.lane = new_lane
            self.target_x = ROAD_X + self.lane * LANE_WIDTH + LANE_WIDTH // 2 - self.width // 2
    
    def update_speed(self, delta_time):
        # Update position based on boosts and spikes
        current_time = time.time()
        self.speed = self.base_speed
        
        # Process boosts
        for boost in self.boost_timers[:]:
            t = current_time - boost['start_time']
            if t < 3:
                self.speed += boost['amount']
            elif t < 7:
                progress = (t - 3) / 4
                self.speed += boost['amount'] * (1 - progress)
            else:
                self.boost_timers.remove(boost)
        
        # Process spikes
        for spike in self.spike_timers[:]:
            t = current_time - spike['start_time']
            if t < 2:
                self.speed -= spike['amount']
            elif t < 6:
                progress = (t - 2) / 4
                self.speed -= spike['amount'] * (1 - progress)
            else:
                self.spike_timers.remove(spike)
        
        # Cap speed at 200
        self.speed = min(max(self.speed, -200), 200)
    
    def draw(self, screen):
        # Smoothly move to target x position
        if abs(self.x - self.target_x) > 1:
            self.x += (self.target_x - self.x) * 0.1
        
        # Draw car with flash effect if active
        current_time = time.time()
        if current_time < self.flash_end_time:
            pygame.draw.rect(screen, self.flash_color, (self.x, self.y, self.width, self.height))
        else:
            pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
    
    def flash_white(self):
        self.flash_color = WHITE
        self.flash_end_time = time.time() + 0.2
    
    def flash_red(self):
        self.flash_color = RED
        self.flash_end_time = time.time() + 0.2

class Coin(GameObjects, FallingObjects):
    def __init__(self, x, y, width=20, height=20, fall_speed=5):
        GameObjects.__init__(self, x, y, width, height)
        FallingObjects.__init__(self, fall_speed)
        self.collected = False
        self.color = YELLOW
    
    def collect(self, player):
        if self.collected:
            return
        current_time = time.time()
        boost_amount = 20
        if current_time - player.last_coin_time <= 1:
            boost_amount = 5
        player.boost_timers.append({'start_time': current_time, 'amount': boost_amount})
        player.last_coin_time = current_time
        self.collected = True
        if coin_sound:
            coin_sound.play()
        player.flash_white()
    
    def update_position(self, delta_time):
        self.y += self.fall_speed * delta_time
        if self.y > SCREEN_HEIGHT:
            self.collected = True  # Despawn when off screen
    
    def draw(self, screen):
        if not self.collected:
            pygame.draw.circle(screen, self.color, (self.x + self.width // 2, self.y + self.height // 2), self.width // 2)

class Spikes(GameObjects, FallingObjects):
    def __init__(self, x, y, width=25, height=25, fall_speed=5):
        GameObjects.__init__(self, x, y, width, height)
        FallingObjects.__init__(self, fall_speed)
        self.hit = False
        self.color = GREEN
    
    def collect(self, player):
        if self.hit:
            return
        current_time = time.time()
        decrease_amount = 30
        if current_time - player.last_spike_time <= 1:
            decrease_amount = player.last_spike_decrease / 2
        player.spike_timers.append({'start_time': current_time, 'amount': decrease_amount})
        player.last_spike_time = current_time
        player.last_spike_decrease = decrease_amount
        self.hit = True
        if spike_sound:
            spike_sound.play()
        player.flash_red()
    
    def update_position(self, delta_time):
        self.y += self.fall_speed * delta_time
        if self.y > SCREEN_HEIGHT:
            self.hit = True  # Despawn when off screen
    
    def draw(self, screen):
        if not self.hit:
            points = [(self.x + self.width // 2, self.y), 
                      (self.x, self.y + self.height), 
                      (self.x + self.width, self.y + self.height)]
            pygame.draw.polygon(screen, self.color, points)

# Game setup
player = Car(SCREEN_WIDTH // 2 - 25, SCREEN_HEIGHT * 2 // 3, 50, 30, 1)
coins = []
spikes = []
last_spawn_time = 0
game_start_time = time.time()
BASE_SPAWN_INTERVAL = 1.0  # Initial spawn interval in seconds
MIN_SPAWN_INTERVAL = 0.3   # Minimum spawn interval
SPAWN_RATE_INCREASE = 0.0001  # Rate at which spawn interval decreases per second
FPS = 60
clock = pygame.time.Clock()

async def main():
    global last_spawn_time
    running = True
    
    while running:
        delta_time = clock.tick(FPS) / 1000.0
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    player.move(-1)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    player.move(1)
        
        # Calculate current spawn interval (decreases over time)
        elapsed_time = time.time() - game_start_time
        spawn_interval = max(MIN_SPAWN_INTERVAL, BASE_SPAWN_INTERVAL - elapsed_time * SPAWN_RATE_INCREASE)
        
        # Spawn coins and spikes
        current_time = time.time()
        if current_time - last_spawn_time > spawn_interval:
            lane = random.randint(0, 3)
            spawn_x = ROAD_X + lane * LANE_WIDTH + LANE_WIDTH // 2 - 20 // 2
            if random.random() < 0.6:
                coins.append(Coin(spawn_x, -20, 20, 20, 200))
            else:
                spikes.append(Spikes(spawn_x, -25, 25, 25, 200))
            last_spawn_time = current_time
        
        # Update game objects
        player.update_speed(delta_time)
        for coin in coins[:]:
            coin.update_position(delta_time)
            if not coin.collected and abs(coin.x - player.x) < player.width and abs(coin.y - player.y) < player.height:
                coin.collect(player)
        
        for spike in spikes[:]:
            spike.update_position(delta_time)
            if not spike.hit and abs(spike.x - player.x) < player.width and abs(spike.y - player.y) < player.height:
                spike.collect(player)
        
        # Remove despawned objects
        coins[:] = [coin for coin in coins if not coin.collected]
        spikes[:] = [spike for spike in spikes if not spike.hit]
        
        # Draw everything
        screen.fill(BLACK)
        pygame.draw.rect(screen, (100, 100, 100), (ROAD_X, 0, ROAD_WIDTH, SCREEN_HEIGHT))  # Road
        for i in range(1, 4):
            pygame.draw.line(screen, WHITE, (ROAD_X + i * LANE_WIDTH, 0), (ROAD_X + i * LANE_WIDTH, SCREEN_HEIGHT), 2)
        
        # Draw road markings moving to give illusion of movement
        road_marking_y = (pygame.time.get_ticks() % 2000) / 2000 * SCREEN_HEIGHT - player.speed
        while road_marking_y < SCREEN_HEIGHT:
            pygame.draw.rect(screen, WHITE, (ROAD_X + ROAD_WIDTH // 2 - 10, road_marking_y, 20, 50))
            road_marking_y += 100
        
        for coin in coins:
            coin.draw(screen)
        for spike in spikes:
            spike.draw(screen)
        player.draw(screen)
        
        pygame.display.flip()
        await asyncio.sleep(1.0 / FPS)

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())

pygame.quit()