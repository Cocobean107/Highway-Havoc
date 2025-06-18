import pygame
import time

pygame.init()

class GameState:
    def __init__(self):
        self.money = 0
        self.car_type = None
        self.floating_texts = []
        
    def add_score(self, money, x=None, y=None, color='white'):
        self.money += money
        if x is not None and y is not None:
            self.add_floating_text(f"+{money}", x, y, color)
    
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

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Highway Havoc")

# Game states
MENU_STATE = 0
PLAYING_STATE = 1
GAME_OVER_STATE = 2

# Road settings
ROAD_WIDTH = 400
LANE_WIDTH = ROAD_WIDTH // 4
ROAD_X = (SCREEN_WIDTH - ROAD_WIDTH) // 2


class Car(GameObject):
    def __init__(self, x, y, width, height, player_id, color='blue'):
        super().__init__(x, y, width, height)
        self.player_id = player_id
        self.speed = 5
        self.base_speed = 5
        self.color = color
        self.boost_timers = []
        self.spike_timers = []
        self.lane = 1 if player_id == 1 else 2
        self.target_x = ROAD_X + self.lane * LANE_WIDTH + LANE_WIDTH // 2 - self.width // 2
        self.flash_color = None
        self.flash_end_time = 0
        self.last_coin_time = 0
        self.last_spike_time = 0
        self.last_spike_decrease = 0
        self.distance = 0
        self.position_offset = 0
    
    def reset(self):
        """Reset car for new game"""
        self.speed = 5
        self.base_speed = 5
        self.boost_timers = []
        self.spike_timers = []
        self.lane = 1
        self.target_x = ROAD_X + self.lane * LANE_WIDTH + LANE_WIDTH // 2 - self.width // 2
        self.x = self.target_x
        self.flash_color = None
        self.flash_end_time = 0
        self.last_coin_time = 0
        self.last_spike_time = 0
        self.last_spike_decrease = 0
        self.distance = 0
        self.position_offset = 0
    
    def move(self, direction):
        new_lane = self.lane + direction
        if 0 <= new_lane < 4:
            self.lane = new_lane
            self.target_x = ROAD_X + self.lane * LANE_WIDTH + LANE_WIDTH // 2 - self.width // 2
    
    def update_speed_and_position(self, delta_time):
        current_time = time.time()
        self.speed = self.base_speed
        self.position_offset = 0
        
        for boost in self.boost_timers[:]:
            t = current_time - boost['start_time']
            if t < 3:
                self.speed += boost['amount']
                self.position_offset -= boost['amount'] * 2
            elif t < 7:
                progress = (t - 3) / 4
                remaining_boost = boost['amount'] * (1 - progress)
                self.speed += remaining_boost
                self.position_offset -= remaining_boost * 2
            else:
                self.boost_timers.remove(boost)
        
        for spike in self.spike_timers[:]:
            t = current_time - spike['start_time']
            if t < 2:
                self.speed -= spike['amount']
                self.position_offset += spike['amount'] * 2
            elif t < 6:
                progress = (t - 2) / 4
                remaining_slowdown = spike['amount'] * (1 - progress)
                self.speed -= remaining_slowdown
                self.position_offset += remaining_slowdown * 2
            else:
                self.spike_timers.remove(spike)
        
        self.speed = max(self.speed, 0)  # Allow speed to reach 0
        self.position_offset = max(min(self.position_offset, 0), -100)
        self.distance += self.speed * delta_time * 10
    
    def draw(self, screen):
        if abs(self.x - self.target_x) > 1:
            self.x += (self.target_x - self.x) * 0.1
        visual_y = self.y + self.position_offset
        current_time = time.time()
        if current_time < self.flash_end_time:
            pygame.draw.rect(screen, self.flash_color, (self.x, visual_y, self.width, self.height))
        else:
            pygame.draw.rect(screen, self.color, (self.x, visual_y, self.width, self.height))
    
    def flash_white(self):
        self.flash_color = 'white'
        self.flash_end_time = time.time() + 0.2
    
    def flash_red(self):
        self.flash_color = 'red'
        self.flash_end_time = time.time() + 0.2

class Coin(GameObject, FallingObjects):
    def __init__(self, x, y, width=20, height=20):
        GameObject.__init__(self, x, y, width, height)
        FallingObjects.__init__(self, 5)
        self.collected = False
        self.color = 'yellow'
    
    def collect(self, player_car, game_state):
        if self.collected:
            return
        current_time = time.time()
        boost_amount = 20
        if current_time - player_car.last_coin_time <= 1:
            boost_amount = 5
        player_car.boost_timers.append({'start_time': current_time, 'amount': boost_amount})
        player_car.last_coin_time = current_time
        self.collected = True
        game_state.coins_collected += 1
        
        # Simple base points without combo bonuses
        base_points = 10 if boost_amount == 20 else 5
        game_state.add_score(base_points, self.x, self.y, 'yellow')
        player_car.flash_white()
    
    def update_position(self, delta_time):
        self.y += self.fall_speed * 50 * delta_time
        if self.y > SCREEN_HEIGHT:
            self.collected = True
    
    def draw(self, screen):
        if not self.collected:
            pygame.draw.circle(screen, self.color, (self.x + self.width // 2, self.y + self.height // 2), self.width // 2)

class Spikes(GameObject, FallingObjects):
    def __init__(self, x, y, width=25, height=25):
        GameObject.__init__(self, x, y, width, height)
        FallingObjects.__init__(self, 5)
        self.hit = False
        self.color = 'green'
    
    def collect(self, player_car, game_state):
        if self.hit:
            return
        current_time = time.time()
        decrease_amount = 30
        if current_time - player_car.last_spike_time <= 1:
            decrease_amount = player_car.last_spike_decrease / 2
        player_car.spike_timers.append({'start_time': current_time, 'amount': decrease_amount})
        player_car.last_spike_time = current_time
        player_car.last_spike_decrease = decrease_amount
        self.hit = True
        game_state.spikes_hit += 1
        
        # Simple money deduction without combo breaking
        game_state.add_floating_text("-25", self.x, self.y, 'red')
        game_state.money = max(0, game_state.money - 25)
        player_car.flash_red()
    
    def update_position(self, delta_time):
        self.y += self.fall_speed * 50 * delta_time
        if self.y > SCREEN_HEIGHT:
            self.hit = True
    
    def draw(self, screen):
        if not self.hit:
            points = [(self.x + self.width // 2, self.y), 
                      (self.x, self.y + self.height), 
                      (self.x + self.width, self.y + self.height)]
            pygame.draw.polygon(screen, self.color, points)

# Simplified GameState class without combo, level, and achievements
class SimplifiedGameState(GameState):
    def __init__(self):
        super().__init__()
        self.high_score = 0
        self.coins_collected = 0
        self.spikes_hit = 0
        self.total_distance = 0
        self.current_state = MENU_STATE
        
    def reset_game(self):
        """Reset game state for a new game"""
        self.money = 0
        self.coins_collected = 0
        self.spikes_hit = 0
        self.total_distance = 0
        self.floating_texts = []

def draw_start_screen(screen):
    screen.fill((20, 20, 40))  # Dark blue background
    
    # Title
    title_font = pygame.font.Font(None, 72)
    title_text = title_font.render("HIGHWAY HAVOC", True, (255, 255, 0))
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 150))
    screen.blit(title_text, title_rect)
    
    # Subtitle
    subtitle_font = pygame.font.Font(None, 36)
    subtitle_text = subtitle_font.render("Race through traffic and collect coins!", True, (255, 255, 255))
    subtitle_rect = subtitle_text.get_rect(center=(SCREEN_WIDTH // 2, 200))
    screen.blit(subtitle_text, subtitle_rect)
    
    # Instructions
    instruction_font = pygame.font.Font(None, 28)
    instructions = [
        "Controls:",
        "A/Left Arrow - Move Left",
        "D/Right Arrow - Move Right",
        "",
        "Collect coins to boost speed!",
        "Avoid spikes - they slow you down!",
        "Game ends when speed reaches 0!"
    ]
    
    start_y = 280
    for i, instruction in enumerate(instructions):
        color = (255, 255, 255) if instruction != "Controls:" else (255, 255, 0)
        text = instruction_font.render(instruction, True, color)
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, start_y + i * 30))
        screen.blit(text, text_rect)
    
    # Start button
    button_font = pygame.font.Font(None, 48)
    button_text = button_font.render("PRESS SPACE TO START", True, (0, 255, 0))
    button_rect = button_text.get_rect(center=(SCREEN_WIDTH // 2, 500))
    screen.blit(button_text, button_rect)
    
    # Pulsing effect for start button
    import math
    pulse = abs(math.sin(time.time() * 3)) * 0.3 + 0.7
    pygame.draw.rect(screen, (0, int(255 * pulse), 0), button_rect, 3)

def draw_game_over_screen(screen, game_state):
    screen.fill((40, 20, 20))  # Dark red background
    
    # Game Over title
    title_font = pygame.font.Font(None, 72)
    title_text = title_font.render("GAME OVER", True, (255, 100, 100))
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 150))
    screen.blit(title_text, title_rect)
    
    # Final Score
    score_font = pygame.font.Font(None, 48)
    score_text = score_font.render(f"Final Money: ${game_state.money:,}", True, (255, 255, 0))
    score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, 220))
    screen.blit(score_text, score_rect)
    
    # High Score
    if game_state.money > game_state.high_score:
        game_state.high_score = game_state.money
        high_score_text = score_font.render("NEW HIGH SCORE!", True, (0, 255, 255))
    else:
        high_score_text = score_font.render(f"High Score: ${game_state.high_score:,}", True, (255, 255, 255))
    high_score_rect = high_score_text.get_rect(center=(SCREEN_WIDTH // 2, 270))
    screen.blit(high_score_text, high_score_rect)
    
    # Stats
    stats_font = pygame.font.Font(None, 32)
    stats = [
        f"Distance Traveled: {int(game_state.total_distance)}",
        f"Coins Collected: {game_state.coins_collected}",
        f"Spikes Hit: {game_state.spikes_hit}"
    ]
    
    start_y = 340
    for i, stat in enumerate(stats):
        text = stats_font.render(stat, True, (255, 255, 255))
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, start_y + i * 35))
        screen.blit(text, text_rect)
    
    # Restart instructions
    restart_font = pygame.font.Font(None, 36)
    restart_text = restart_font.render("PRESS SPACE TO PLAY AGAIN", True, (0, 255, 0))
    restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, 480))
    screen.blit(restart_text, restart_rect)
    
    quit_text = restart_font.render("PRESS ESC TO QUIT", True, (255, 255, 255))
    quit_rect = quit_text.get_rect(center=(SCREEN_WIDTH // 2, 520))
    screen.blit(quit_text, quit_rect)
    
    # Pulsing effect for restart button
    import math
    pulse = abs(math.sin(time.time() * 3)) * 0.3 + 0.7
    pygame.draw.rect(screen, (0, int(255 * pulse), 0), restart_rect, 2)

# Game setup
player_car = Car(SCREEN_WIDTH // 2 - 25, SCREEN_HEIGHT * 2 // 3, 50, 30, 1, 'blue')
game_state = SimplifiedGameState()

coins = []
spikes = []
last_spawn_time = 0
game_start_time = time.time()
BASE_SPAWN_INTERVAL = 1.5
MAX_OBJECTS_ON_SCREEN = 8
road_scroll_offset = 0
FPS = 60
clock = pygame.time.Clock()

def draw_ui(screen):
    font_large = pygame.font.Font(None, 36)
    font_medium = pygame.font.Font(None, 28)
    font_small = pygame.font.Font(None, 24)
    base_x, base_y = 10, 10
    
    # Main game stats
    speed_text = font_medium.render(f"Speed: {int(player_car.speed)}", True, 'white')
    distance_text = font_medium.render(f"Distance: {int(player_car.distance)}", True, 'white')
    screen.blit(speed_text, (base_x, base_y))
    screen.blit(distance_text, (base_x, base_y + 30))
    
    # Money display
    money_text = font_large.render(f"Money: ${game_state.money:,}", True, 'yellow')
    screen.blit(money_text, (SCREEN_WIDTH - 250, base_y))
    
    # Bottom stats
    stats_y = SCREEN_HEIGHT - 60
    coins_text = font_small.render(f"Coins: {game_state.coins_collected}", True, 'yellow')
    spikes_text = font_small.render(f"Spikes Hit: {game_state.spikes_hit}", True, 'red')
    screen.blit(coins_text, (base_x, stats_y))
    screen.blit(spikes_text, (base_x + 100, stats_y))

def draw_floating_texts(screen):
    font = pygame.font.Font(None, 32)
    for text_obj in game_state.floating_texts:
        elapsed = time.time() - text_obj['start_time']
        alpha = max(0, 255 - int(255 * elapsed / text_obj['duration']))
        text_surface = font.render(text_obj['text'], True, text_obj['color'])
        text_surface.set_alpha(alpha)
        x = text_obj['x'] - text_surface.get_width() // 2
        y = text_obj['y']
        screen.blit(text_surface, (x, y))

def check_spawn_collision(new_x, new_y, existing_objects):
    import math
    collision_radius = 40
    for obj in existing_objects:
        if not (hasattr(obj, 'collected') and obj.collected) and not (hasattr(obj, 'hit') and obj.hit):
            distance = math.sqrt((new_x - obj.x)**2 + (new_y - obj.y)**2)
            if distance < collision_radius:
                return True
    return False

def start_new_game():
    global coins, spikes, last_spawn_time, road_scroll_offset
    game_state.reset_game()
    player_car.reset()
    coins = []
    spikes = []
    last_spawn_time = 0
    road_scroll_offset = 0
    game_state.current_state = PLAYING_STATE



# Main game loop
import asyncio
import platform
import random
import math
import sys

async def main():
    global last_spawn_time, road_scroll_offset
    running = True
    
    while running:
        delta_time = clock.tick(FPS) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if game_state.current_state == MENU_STATE:
                    if event.key == pygame.K_SPACE:
                        start_new_game()
                elif game_state.current_state == PLAYING_STATE:
                    if event.key in (pygame.K_a, pygame.K_LEFT):
                        player_car.move(-1)
                    elif event.key in (pygame.K_d, pygame.K_RIGHT):
                        player_car.move(1)
                elif game_state.current_state == GAME_OVER_STATE:
                    if event.key == pygame.K_SPACE:
                        start_new_game()
                    elif event.key == pygame.K_ESCAPE:
                        running = False
        
        if game_state.current_state == MENU_STATE:
            draw_start_screen(screen)
            
        elif game_state.current_state == PLAYING_STATE:
            current_time = time.time()
            speed_multiplier = max(player_car.speed / player_car.base_speed, 0.1) if player_car.speed > 0 else 0.1
            dynamic_spawn_interval = BASE_SPAWN_INTERVAL / speed_multiplier
            
            active_objects = len([obj for obj in coins if not obj.collected]) + len([obj for obj in spikes if not obj.hit])
            
            if current_time - last_spawn_time > dynamic_spawn_interval and active_objects < MAX_OBJECTS_ON_SCREEN:
                max_attempts = 10
                attempts = 0
                spawned = False
                
                while attempts < max_attempts and not spawned:
                    lane = random.randint(0, 3)
                    spawn_x = ROAD_X + lane * LANE_WIDTH + LANE_WIDTH // 2 - 10
                    spawn_y = -20
                    all_objects = coins + spikes
                    if not check_spawn_collision(spawn_x, spawn_y, all_objects):
                        if random.random() < 0.6:
                            coins.append(Coin(spawn_x, spawn_y))
                        else:
                            spikes.append(Spikes(spawn_x, spawn_y))
                        spawned = True
                    attempts += 1
                last_spawn_time = current_time
            
            player_car.update_speed_and_position(delta_time)
            game_state.total_distance = player_car.distance
            game_state.update_floating_texts(delta_time)
            
            # Check for game over condition
            if player_car.speed <= 0:
                game_state.current_state = GAME_OVER_STATE
            
            road_scroll_speed = 30 * (player_car.speed / player_car.base_speed) if player_car.speed > 0 else 0
            road_scroll_offset += road_scroll_speed * delta_time
            
            for coin in coins[:]:
                coin.update_position(delta_time)
                if (not coin.collected and 
                    abs(coin.x - player_car.x) < player_car.width and 
                    abs(coin.y - (player_car.y + player_car.position_offset)) < player_car.height):
                    coin.collect(player_car, game_state)
            
            for spike in spikes[:]:
                spike.update_position(delta_time)
                if (not spike.hit and 
                    abs(spike.x - player_car.x) < player_car.width and 
                    abs(spike.y - (player_car.y + player_car.position_offset)) < player_car.height):
                    spike.collect(player_car, game_state)
            
            coins[:] = [coin for coin in coins if not coin.collected]
            spikes[:] = [spike for spike in spikes if not spike.hit]
            
            # Draw game
            screen.fill('black')
            pygame.draw.rect(screen, 'grey50', (ROAD_X, 0, ROAD_WIDTH, SCREEN_HEIGHT))
            for i in range(1, 4):
                pygame.draw.line(screen, 'white', (ROAD_X + i * LANE_WIDTH, 0), 
                               (ROAD_X + i * LANE_WIDTH, SCREEN_HEIGHT), 2)
            marking_spacing = 100
            marking_offset = int(road_scroll_offset) % marking_spacing
            for y in range(-marking_spacing + marking_offset, SCREEN_HEIGHT + marking_spacing, marking_spacing):
                pygame.draw.rect(screen, 'white', (ROAD_X + ROAD_WIDTH // 2 - 5, y, 10, 40))
            
            for coin in coins:
                coin.draw(screen)
            for spike in spikes:
                spike.draw(screen)
            
            player_car.draw(screen)
            draw_ui(screen)
            draw_floating_texts(screen)
            
        elif game_state.current_state == GAME_OVER_STATE:
            draw_game_over_screen(screen, game_state)
        
        pygame.display.flip()
        await asyncio.sleep(1.0 / FPS)

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())

pygame.quit()