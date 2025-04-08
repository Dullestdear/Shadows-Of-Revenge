import pygame as pg
import math
import csv
import os
import pygame.mixer

# Initialize Pygame
pg.init()

# Set up the display
screen = pg.display.set_mode((1280, 720))
pg.display.set_caption('Shadows Of Revenge')
screen.fill("silver")

# Main loop flag

running = True
BLACK = (0, 0, 0)
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
RED = (255, 0, 0)
# Scrolling variables
scroll = 0

# Load background images

sky_img = pg.image.load("img\\sky.png").convert_alpha()
mountain_img = pg.image.load("img\\mountain.png").convert_alpha()
pine1_img = pg.image.load("img\\pine1.png").convert_alpha()
pine2_img = pg.image.load("img\\pine2.png").convert_alpha()

# Level design constants
MAX_COLS = 150
TILE_SIZE = 40  # Tile size in pixels
ROWS = 16  # Number of rows in the level data


# Health variables
max_health = 100
current_health = 100  # Spearman's initial health

player_max_health = 100
player_current_health = 100  # Player's initial healths

def draw_bg(bg_scroll):
    screen.fill((0, 0, 0))
    
    width = sky_img.get_width()
    
    # Sky moves very slowly
    for x in range(5):
        screen.blit(sky_img, ((x * width) + bg_scroll * 0.1, 0))
    
    # Mountains move a bit faster
    for x in range(5):
        screen.blit(mountain_img, ((x * width) + bg_scroll * 0.3, SCREEN_HEIGHT - mountain_img.get_height() - 250))
    
    # Pine trees in background move faster
    for x in range(5):
        screen.blit(pine1_img, ((x * width) + bg_scroll * 0.5, SCREEN_HEIGHT - pine1_img.get_height() - 100))
    
    # Pine trees in foreground move even faster
    for x in range(5):
        screen.blit(pine2_img, ((x * width) + bg_scroll * 0.7, SCREEN_HEIGHT - pine2_img.get_height()+100))



def load_level_data(filename):
    world_data = []
    enemy_data = []
    player_position = None

    try:
        with open(filename, newline='') as file:
            reader = csv.reader(file)
            for row_index, row in enumerate(reader):
                if row:
                    mid = len(row) // 2
                    tile_row = [int(tile) for tile in row[:mid]]
                    enemies_row = [int(enemy) for enemy in row[mid:]]

                    # Check for player tile (tile number 4)
                    for col_index, tile in enumerate(tile_row):
                        if tile == 4:
                            # Adjust player position to be on the ground
                            adjusted_y = row_index * TILE_SIZE + (SCREEN_HEIGHT - ROWS * TILE_SIZE)
                            player_position = (col_index * TILE_SIZE, adjusted_y)
                            tile_row[col_index] = -1

                    world_data.append(tile_row)
                    enemy_data.append(enemies_row)
    except FileNotFoundError:
        print(f"Warning: Level file {filename} not found. Creating empty level.")
        # Create empty level data if file not found
        ROWS = 16
        MAX_COLS = 150
        for row in range(ROWS):
            r = [-1] * MAX_COLS
            e = [-1] * MAX_COLS
            world_data.append(r)
            enemy_data.append(e)

        # Create ground (bottom row filled with tile type 0)
        for tile in range(0, MAX_COLS):
            world_data[ROWS - 1][tile] = 0

    return world_data, enemy_data, player_position




def draw_player_health_bar_top_left(surface, current_health, max_health):
    # Constants for health bar appearance
    width = 200
    height = 25
    x = 20
    y = 20
    border = 2

    # Calculate health ratio and width
    health_ratio = max(0, min(current_health / max_health, 1))
    health_width = int(width * health_ratio)

    # Colors
    BORDER_COLOR = (50, 50, 50)  # Dark gray border
    BG_COLOR = (40, 40, 40)  # Darker background
    HEALTH_COLORS = [
        (255, 0, 0),  # Red for low health
        (255, 165, 0),  # Orange for medium health
        (0, 255, 0)  # Green for high health
    ]

    # Draw border (outer rectangle)
    pg.draw.rect(surface, BORDER_COLOR, (x - border, y - border, width + border * 2, height + border * 2))

    # Draw background (black)
    pg.draw.rect(surface, BG_COLOR, (x, y, width, height))

    # Draw health bar with gradient based on health percentage
    if health_width > 0:
        if health_ratio > 0.6:  # High health (green)
            color = HEALTH_COLORS[2]
        elif health_ratio > 0.3:  # Medium health (orange)
            color = HEALTH_COLORS[1]
        else:  # Low health (red)
            color = HEALTH_COLORS[0]

        pg.draw.rect(surface, color, (x, y, health_width, height))

        # Add shine effect (lighter line at top)
        shine_color = (min(color[0] + 50, 255), min(color[1] + 50, 255), min(color[2] + 50, 255))
        pg.draw.rect(surface, shine_color, (x, y, health_width, height // 4))


# Function: Rectangular Tube Health Bar (Red Only) for enemy
def draw_tube_health_bar(screen, x, y, current_health, max_health, width, height):
    # Calculate the ratio of health remaining
    ratio = max(0, current_health / max_health)  # Ensure the ratio does not go below 0

    # Draw the tube outline (black border)
    pg.draw.rect(screen, BLACK, (x, y, width, height), 2)

    # Draw the health bar inside the tube
    pg.draw.rect(screen, RED, (x + 2, y + 2, (width - 4) * ratio, height - 4))


# Background class
class Background(pg.sprite.Sprite):
    def __init__(self, image_path, x, y):
        super().__init__()
        self.image = pg.image.load(image_path).convert()
        self.image = pg.transform.scale(self.image, (1280, 720))  # Rescale to screen size
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)


# Function to display text character by character
def draw_text_box(text, font, color, x, y, width, height, char_index):
    box_screen = pg.Surface((width, height), pg.SRCALPHA)  # Allow transparency
    box_screen.fill((0, 0, 0, 180))  # Semi-transparent black
    screen.blit(box_screen, (x, y))

    words = text.split(' ')
    wrapped_lines = []
    current_line = ''
    for word in words:
        test_line = f"{current_line} {word}".strip()
        if font.size(test_line)[0] <= width - 40:  # Account for padding
            current_line = test_line
        else:
            wrapped_lines.append(current_line)
            current_line = word
    if current_line:
        wrapped_lines.append(current_line)

    visible_text = ''.join(wrapped_lines)[:char_index]
    line_height = font.size('Tg')[1]
    y_offset = 10

    for line in wrapped_lines:
        if visible_text:
            line_to_draw = visible_text[:len(line)]
            visible_text = visible_text[len(line):]
            text_screen = font.render(line_to_draw, True, color)
            text_rect = text_screen.get_rect(topleft=(x + 20, y + y_offset))
            screen.blit(text_screen, text_rect)
            y_offset += line_height


# Function for slide effect
def slide_effect(current_background, next_background, duration=2000):
    clock = pg.time.Clock()
    steps = 50
    step_duration = duration // steps

    for step in range(steps):
        current_background.rect.x = -(1280 * step // steps)
        next_background.rect.x = 1280 - (1280 * step // steps)
        screen.fill((0, 0, 0))
        screen.blit(current_background.image, current_background.rect)
        screen.blit(next_background.image, next_background.rect)
        pg.display.update()
        clock.tick(1000 // step_duration)


# Story data
# Story data
STORY_SCENES = [
    {
        "background_path": "img\\Scene1.png",
        "story": [
            "The stars twinkled above as the crackling of the campfire echoed in the dense forest. Your squad laughed and joked, You are a special forces soldier, one of the elite. As the firelight dances on your face, you feel a sense of camaraderie and purpose.",
            "'Tomorrow, the real mission begins', your squad leader says, their voice steady with determination.",
            "But for tonight, it's peace, a rare moment to breathe.",
            "This is where your journey begins, adventurer."
        ]
    },
    {
        "background_path": "img\\Scene2.png",
        "story": [
            "The laughter fades as you notice the canteens are dry. 'We're out of water', someone grumbles. ",
            "The nearest river isn't far, and you volunteer to fetch some.",
            "The dense forest seems alive as you make your way through the undergrowth, the sound of flowing water guiding you.",
            "The moonlight reflects off the rippling surface of the river as you kneel to fill the canteens. A shiver runs down your spine, but you shake it off—after all, you're trained for this!!"
        ]
    },
    {
        "background_path": "img\\Scene3.png",
        "story": [
            "You return to camp, the full canteens sloshing softly at your side.",
            "But something's wrong. The fire is out. The laughter—gone.",
            "Your heart pounds. Gear is scattered, tents slashed, and the silence is deafening.",
            "You scan the shadows—no bodies, no blood , just absence . Your squad is gone.",
            "Then, a rustle. Tribal war cries pierce the silence as tribal people burst from the treeline.",
            "You steady your stance, adrenaline surging.",
            "With fire in your voice, you growl—",
            "\"You think this ends here? No. This is where your nightmare begins. Whatever it takes."
        ]
    }
]


TITLE_SCREEN_BACKGROUND = "img\\Tittle.png"
current_scene = 0
scene_background = Background(STORY_SCENES[current_scene]["background_path"], 0, 0)
story = STORY_SCENES[current_scene]["story"]
story_index = 0
show_story = True
story_timer = pg.time.get_ticks()
story_char_index = 0


def show_title_screen():
    screen = pg.display.set_mode((1280, 720))
    clock = pg.time.Clock()
    background = Background(TITLE_SCREEN_BACKGROUND, 0, 0)

    # Initialize the mixer
    pygame.mixer.init()

    # Load and play the music
    try:
        pygame.mixer.music.load("music\\Age of empires 2 theme song!.mp3")  # Replace with your music file path
        pygame.mixer.music.play(-1)  # -1 means loop indefinitely
    except pygame.error:
        print("Music file not found or not supported. Continuing without music.")

    # Add font and text setup
    font = pg.font.Font(None, 48)
    instruction_text = "Press any key to continue"
    blink_timer = pg.time.get_ticks()
    instruction_visible = True

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pygame.mixer.music.stop()  # Stop the music
                return False
            if event.type == pg.KEYDOWN:
                pygame.mixer.music.stop()  # Stop the music
                return True

        screen.fill((0, 0, 0))
        screen.blit(background.image, background.rect)

        # Blink the instruction text
        if pg.time.get_ticks() - blink_timer > 500:  # Toggle every 500ms
            instruction_visible = not instruction_visible
            blink_timer = pg.time.get_ticks()

        if instruction_visible:
            text_surface = font.render(instruction_text, True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=(640, 600))  # Positioned near bottom
            screen.blit(text_surface, text_rect)

        pg.display.flip()
        clock.tick(60)

    return False



# Font setup
font = pg.font.Font(None, 36)
text_color = (255, 255, 255)
box_width = 1000
box_height = 150
box_x = 140
box_y = 720 - box_height

scale = 2


class Bullet(pg.sprite.Sprite):
    def __init__(self, x, y, facing_left):
        super().__init__()
        self.image = pg.image.load("img\\BulletStream.png").convert_alpha()
        self.image = pg.transform.scale(self.image, (15, 10))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.speed = -10 if facing_left else 10
        self.world_x = x  # Store the bullet's position in world coordinates

    def update(self):
        self.rect.x += self.speed
        
        # Remove the bullet if it goes off-screen
        if self.rect.right < 0 or self.rect.left > 1280:
            self.kill()



class Spear(pg.sprite.Sprite):
    def __init__(self, x, y, target_x, target_y):
        super().__init__()
        self.image = pg.image.load("img\\spear.png").convert_alpha()
        self.image = pg.transform.scale(self.image, (35, 20))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        
        # Calculate direction and speed
        dx = target_x - x
        dy = target_y - y
        distance = math.sqrt(dx**2 + dy**2)
        self.speed = 9 
        self.dx = (dx / distance) * self.speed if distance > 0 else 0
        self.dy = (dy / distance) * self.speed if distance > 0 else 0
        
        # Rotate spear to face direction of travel
        angle = math.degrees(math.atan2(-dy, dx))
        self.image = pg.transform.rotate(self.image, angle)

    def update(self):
        self.rect.x += self.dx
        self.rect.y += self.dy
        if (self.rect.right < 0 or self.rect.left > 1280 or 
            self.rect.bottom < 0 or self.rect.top > 720):
            self.kill()


class SpearmanEnemy(pg.sprite.Sprite):
    def __init__(self, sprite_sheet_paths, frame_width, frame_height, x, y, alert_range, spear_range=None):
        super().__init__()
        self.sprite_sheets = {
            "idle": pg.image.load(sprite_sheet_paths["idle"]).convert_alpha(),
            "running": pg.image.load(sprite_sheet_paths["running"]).convert_alpha(),
            "melee_attack": pg.image.load(sprite_sheet_paths["melee_attack"]).convert_alpha(),
            "spear_throw": pg.image.load(sprite_sheet_paths["spear_throw"]).convert_alpha(),
            "death": pg.image.load(sprite_sheet_paths["death"]).convert_alpha(),
        }
        self.vel_y = 0
        self.gravity = 0.8
        self.on_ground = False
        self.in_air = True
        self.facing_left = True
        self.last_attack_time = 0
        self.attack_cooldown = 1000
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.animations = {
            state: self.load_frames(self.sprite_sheets[state]) for state in self.sprite_sheets
        }
        self.state = "idle"
        self.current_animation = self.animations[self.state]
        self.current_frame = 0
        self.image = self.current_animation[self.current_frame]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.speed = 2
        self.alert_range = alert_range
        self.attack_range = 50
        self.spear_range = spear_range
        self.animation_timer = pg.time.get_ticks()
        self.animation_delay = 100
        self.health = 100
        self.is_dead = False
        self.death_animation_complete = False
        self.spear_cooldown = 4000
        self.last_spear_time = 0
        self.spears_group = pg.sprite.Group()
        self.throwing_spear = False
        self.spear_frame = 0

        # Initialize movement variables
        self.velocity_y = 0
        self.velocity_x = 0
        self.max_fall_speed = 10

        # Initialize fixed_position to avoid AttributeError
        self.fixed_position = (self.rect.x, self.rect.y)
    

    def move_and_handle_collision(self, world):
        # First handle horizontal movement
        self.rect.x += self.velocity_x
        
        # Check horizontal collisions
        for tile_rect in world.collision_rects:
            adjusted_rect = pg.Rect(
                tile_rect.x + bg_scroll,
                tile_rect.y + 64,
                tile_rect.width,
                tile_rect.height
            )
            if self.rect.colliderect(adjusted_rect):
                if self.velocity_x > 0:  # Moving right
                    self.rect.right = adjusted_rect.left
                elif self.velocity_x < 0:  # Moving left
                    self.rect.left = adjusted_rect.right
                self.velocity_x = 0
        
        # Apply gravity
        self.velocity_y += self.gravity
        if self.velocity_y > 10:  # Cap falling speed
            self.velocity_y = 10
        
        # Move vertically
        self.rect.y += self.velocity_y
        self.on_ground = False
        
        # Check vertical collisions
        for tile_rect in world.collision_rects:
            adjusted_rect = pg.Rect(
                tile_rect.x + bg_scroll,
                tile_rect.y + 64,
                tile_rect.width,
                tile_rect.height
            )
            if self.rect.colliderect(adjusted_rect):
                if self.velocity_y > 0:  # Falling
                    self.rect.bottom = adjusted_rect.top
                    self.velocity_y = 0
                    self.on_ground = True
                    self.in_air = False
                elif self.velocity_y < 0:  # Moving up
                    self.rect.top = adjusted_rect.bottom
                    self.velocity_y = 0
        
        # If not on ground after vertical movement, we're in the air
        if not self.on_ground:
            self.in_air = True



    def load_frames(self, sprite_sheet):
        frames = []
        sheet_width = sprite_sheet.get_width()
        sheet_height = sprite_sheet.get_height()
        for y in range(0, sheet_height, self.frame_height):
            for x in range(0, sheet_width, self.frame_width):
                frame = sprite_sheet.subsurface((x, y, self.frame_width, self.frame_height))
                frames.append(pg.transform.scale(frame, (self.frame_width * 2, self.frame_height * 2)))
        return frames

    def set_animation(self, state):
        if self.state != state:
            self.state = state
            self.current_animation = self.animations[state]
            self.current_frame = 0

    def animate(self):
        current_time = pg.time.get_ticks()
        if current_time - self.animation_timer > self.animation_delay:
            if self.state == "death" and self.current_frame >= len(self.current_animation) - 1:
                self.death_animation_complete = True
                return
            
            self.current_frame = (self.current_frame + 1) % len(self.current_animation)
            self.image = self.current_animation[self.current_frame]
            if not self.facing_left:
                self.image = pg.transform.flip(self.image, True, False)
            self.animation_timer = current_time

    def apply_gravity(self):
        """Apply gravity to the enemy's vertical movement"""
        self.velocity_y += self.gravity
        # Cap falling speed
        if self.velocity_y > self.max_fall_speed:
            self.velocity_y = self.max_fall_speed

    def update(self, player, bullets_group, world):
        global player_current_health
        current_time = pg.time.get_ticks()

        player_world_x = player.rect.x - bg_scroll
        
        # Handle physics (only once)
        self.move_and_handle_collision(world)  # Don't call apply_gravity separately
        
        # Update spears
        self.spears_group.update()
        for spear in self.spears_group:
            if pg.sprite.collide_rect(spear, player):
                player_current_health = max(0, player_current_health - 25)
                player.take_damage(25)
                spear.kill()
        
        bullet_hits = pg.sprite.spritecollide(self, bullets_group, True)
        if bullet_hits and not self.is_dead:
            self.health -= 25
            if self.health <= 0:
                self.is_dead = True
                self.current_frame = 0
                self.animation_timer = current_time
                self.set_animation("death")
                return
        
        # Handle death state
        if self.is_dead:
            if not self.death_animation_complete:
                self.set_animation("death")
                if current_time - self.animation_timer > self.animation_delay:
                    if self.current_frame < len(self.animations["death"]) - 1:
                        self.current_frame += 1
                        self.image = self.animations["death"][self.current_frame]
                        if not self.facing_left:
                            self.image = pg.transform.flip(self.image, True, False)
                        self.animation_timer = current_time
                    else:
                        self.death_animation_complete = True
                        self.kill()  # Remove from game
            return
        
        distance = abs(self.rect.centerx - player_world_x)

        if distance <= self.alert_range:
            # Face player
            self.facing_left = player.rect.centerx < self.rect.centerx
            
            # Check if close enough for melee attack
            if distance <= self.attack_range:
                self.velocity_x = 0
                self.set_animation("melee_attack")
                
                # Attack player if cooldown allows
                if current_time - self.last_attack_time >= self.attack_cooldown:
                    player_current_health = max(0, player_current_health - 10)
                    player.take_damage(10)
                    self.last_attack_time = current_time
            
            # Check if in range for throwing spear
            elif self.spear_range and distance <= self.spear_range:
                self.velocity_x = 0
                
                if current_time - self.last_spear_time >= self.spear_cooldown:
                    self.set_animation("spear_throw")
                    self.throwing_spear = True
                    
                    # Throw spear on specific animation frame
                    if self.current_frame == len(self.animations["spear_throw"]) // 2:
                        spear = Spear(self.rect.centerx, self.rect.centery, 
                                    player.rect.centerx, player.rect.centery)
                        self.spears_group.add(spear)
                        self.last_spear_time = current_time
                        self.throwing_spear = False
                else:
                    self.set_animation("running")
                    self.velocity_x = -self.speed if self.facing_left else self.speed
            
            # Otherwise move toward player
            else:
                self.set_animation("running")
                self.velocity_x = -self.speed if self.facing_left else self.speed
        else:
            # If player out of range, idle
            self.velocity_x = 0
            self.set_animation("idle")
        
        # Always animate
        self.animate()




# Global variables for player's health
player_max_health = 100
player_current_health = 100  # Player's initial health

def show_controls_screen():
    screen = pg.display.set_mode((1280, 720))
    clock = pg.time.Clock()
    
    # Try to load background
    try:
        bg_image = pg.image.load(r"img\\selection_bg.png").convert()
        bg_image = pg.transform.scale(bg_image, (1280, 720))
    except:
        bg_image = None

    # Setup font
    try:
        font = pg.font.Font("C:\\Users\\ayaan\\Desktop\\OldLondon.ttf", 48)
        title_font = pg.font.Font("C:\\Users\\ayaan\\Desktop\\OldLondon.ttf", 72)
    except:
        font = pg.font.SysFont("georgia", 48)
        title_font = pg.font.SysFont("georgia", 72)

    # Control instructions
    controls = [
        "Movement Controls:",
        "LEFT ARROW - Move Left",
        "RIGHT ARROW - Move Right",
        "UP ARROW - Jump",
        "SPACE - Shoot",
        "DOWN ARROW - Crouch",
        "",
        "Press ESC to return to menu"
    ]

    running = True
    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return "quit"
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    return None

        # Draw background
        if bg_image:
            screen.blit(bg_image, (0, 0))
        else:
            screen.fill((0, 0, 0))

        # Draw title
        title = title_font.render("Game Controls", True, (255, 215, 0))
        title_rect = title.get_rect(center=(640, 100))
        screen.blit(title, title_rect)

        # Draw control instructions
        for i, text in enumerate(controls):
            color = (255, 215, 0) if i == 0 else (255, 255, 255)  # Gold for header, white for instructions
            text_surface = font.render(text, True, color)
            text_rect = text_surface.get_rect(center=(640, 200 + i * 60))
            screen.blit(text_surface, text_rect)

        pg.display.flip()
        clock.tick(60)

def show_credits_screen():
    screen = pg.display.set_mode((1280, 720))
    clock = pg.time.Clock()
    
    # Try to load background
    try:
        bg_image = pg.image.load(r"img\\selection_bg.png").convert()
        bg_image = pg.transform.scale(bg_image, (1280, 720))
    except:
        bg_image = None

    # Setup font
    try:
        title_font = pg.font.Font("C:\\Users\\ayaan\\Desktop\\OldLondon.ttf", 72)
        section_font = pg.font.Font("C:\\Users\\ayaan\\Desktop\\OldLondon.ttf", 48)
        content_font = pg.font.Font("C:\\Users\\ayaan\\Desktop\\OldLondon.ttf", 36)
    except:
        title_font = pg.font.SysFont("georgia", 72)
        section_font = pg.font.SysFont("georgia", 48)
        content_font = pg.font.SysFont("georgia", 36)

    # Organize credits into sections
    credit_sections = {
        "Abhishek": [
            "Abhishek (Animator)",
            " • Player animations",
            " • Spearman animations",
            " • Boss animations",
            " • Boss creation",
            " • Debugging & testing"
        ],
        "Prakhar": [
            "Prakhar (Coder, Artist)",
            " • Level design code          • Spearman AI",
            " • Player design              • Knight design",
            " • Level tiles design         • Collision logic",
            " • Gravity logic              • Fall death logic",
            " • Applied entity gravity     • Level creation",
            " • Camera system              • Menu screen",
            " • End screen                 • Music selection",
            " • Music integration          • EXE file creation",
            " • Debugging & testing        • Game design"
        ],
        "Sulaksh": [
            "Sulaksh (Coder)",
            " • Spear throwing logic",
            " • Bullet logic",
            " • Title screen",
            " • Story scenes",
            " • Music selection",
            " • Player spawn logic",
            " • Debugging & testing"
        ],
        "Ayaan": [
            "Ayaan (Coder, Artist)",
            " • Health bar logic           • Spearman design",
            " • Spearman coding            • EXE file creation",
            " • Damage model               • Spear design",
            " • Story writing              • Music selection",
            " • Game over screen           • Title screen design",
            " • Knight creation            • Snow tileset",
            " • Debugging & testing        • Game design"
        ],
        "Music": [
            "Music",
            "• Title Screen – Age of Empires II Theme (1999)",
            "• Story & Menu – Counter-Strike: Condition Zero Selection Music",
            "• Gameplay – Electric Fountain (Tekken 6)",
            "• Death Music – Evil Morty Theme (Rick and Morty)"
        ],
        "References": [
            "References",
            "• ChatGPT",
            "• Cursor AI",
            "• GitHub Copilot",
            "• Perplexity AI"
        ],
        "Special Thanks": [
            "Special Thanks",
            "• Code With Russ",
            "• Game Maker's Toolkit",
            "• Itch.io"
        ]
    }

    # Create a list of sections for navigation
    sections = list(credit_sections.keys())
    current_section = 0

    # Pre-render instruction text
    instruction_text = content_font.render("Press any key to continue, ESC to exit", True, (200, 200, 200))
    instruction_rect = instruction_text.get_rect(center=(640, 680))

    running = True
    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return "quit"
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    return None
                else:
                    # Move to next section
                    current_section = (current_section + 1) % len(sections)

        # Draw background
        if bg_image:
            screen.blit(bg_image, (0, 0))
        else:
            screen.fill((0, 0, 0))

        # Create semi-transparent overlay
        overlay = pg.Surface((1280, 720), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        # Get current section content
        section_name = sections[current_section]
        content = credit_sections[section_name]

        # Draw section content
        y_pos = 100
        for i, text in enumerate(content):
            if i == 0:  # Section header
                color = (255, 215, 0)  # Gold
                font = section_font
            else:  # Content
                color = (200, 200, 200)  # Light gray
                font = content_font

            # Create shadow and main text
            shadow = font.render(text, True, (0, 0, 0))
            main_text = font.render(text, True, color)

            # Draw shadow
            shadow_rect = shadow.get_rect(center=(642, y_pos + 2))
            screen.blit(shadow, shadow_rect)

            # Draw main text
            text_rect = main_text.get_rect(center=(640, y_pos))
            screen.blit(main_text, text_rect)

            y_pos += 50

        # Draw instruction text
        screen.blit(instruction_text, instruction_rect)

        pg.display.flip()
        clock.tick(60)

def main_menu():
    pg.init()
    screen = pg.display.set_mode((1280, 720))
    clock = pg.time.Clock()
    
    # Ensure music is playing
    if not pygame.mixer.music.get_busy():
        try:
            pygame.mixer.music.load("music\\01 Counterstrike - Condition Zero.mp3")
            pygame.mixer.music.set_volume(0.4)  # Set volume to 40%
            pygame.mixer.music.play(-1)  # Loop indefinitely
        except pygame.error as e:
            print(f"Error loading music: {e}")
    
    try:
        bg_image = pg.image.load(r"img\\selection_bg.png").convert()
        bg_image = pg.transform.scale(bg_image, (1280, 720))
    except:
        bg_image = None
        print("Menu background image not found")
    
    # Create buttons with adjusted spacing
    start_button = Button("Start Game", 280)
    controls_button = Button("Controls", 360)
    credits_button = Button("Credits", 440)
    quit_button = Button("Quit Game", 520)
    
    running = True
    while running:
        mouse_pos = pg.mouse.get_pos()

        for event in pg.event.get():
            if event.type == pg.QUIT:
                pygame.mixer.music.stop()  # Stop music when quitting
                return None
            if event.type == pg.MOUSEBUTTONDOWN:
                if start_button.draw(screen).collidepoint(mouse_pos):
                    return 0  # Return level 0 to start the game
                if controls_button.draw(screen).collidepoint(mouse_pos):
                    result = show_controls_screen()
                    if result == "quit":
                        return None
                if credits_button.draw(screen).collidepoint(mouse_pos):
                    result = show_credits_screen()
                    if result == "quit":
                        return None
                if quit_button.draw(screen).collidepoint(mouse_pos):
                    pygame.mixer.music.stop()  # Stop music when quitting
                    return None
        
        # Draw background
        if bg_image:
            screen.blit(bg_image, (0, 0))
        else:
            screen.fill((0, 0, 0))
        
        # Draw title
        try:
            title_font = pg.font.Font("C:\\Users\\ayaan\\Desktop\\OldLondon.ttf", 90)
        except:
            title_font = pg.font.SysFont("georgia", 90)
        
        title = title_font.render("Shadows Of Revenge", True, (255, 215, 0))
        title_rect = title.get_rect(center=(640, 150))
        
        # Draw title shadow
        title_shadow = title_font.render("Shadows Of Revenge", True, (0, 0, 0))
        shadow_rect = title_shadow.get_rect(center=(644, 154))
        screen.blit(title_shadow, shadow_rect)
        screen.blit(title, title_rect)

        # Update and draw buttons
        start_button.is_hovered = start_button.draw(screen).collidepoint(mouse_pos)
        controls_button.is_hovered = controls_button.draw(screen).collidepoint(mouse_pos)
        credits_button.is_hovered = credits_button.draw(screen).collidepoint(mouse_pos)
        quit_button.is_hovered = quit_button.draw(screen).collidepoint(mouse_pos)
        
        start_button.draw(screen)
        controls_button.draw(screen)
        credits_button.draw(screen)
        quit_button.draw(screen)
        
        pg.display.flip()
        clock.tick(60)
    
    return None

# Update the main function to use main_menu instead of level_select_screen
def main():
    pg.init()
    running = True
    
    while running:
        # Show title screen first
        if show_title_screen():
            # Show story
            if show_story():
                restart_game = True
                while restart_game:
                    # Show main menu instead of level selection
                    selected_level = main_menu()
                    
                    if selected_level is not None:
                        # Reset player health when starting/restarting
                        global player_current_health
                        player_current_health = 100
                        
                        # Run the level
                        result = run_level(selected_level)
                        
                        if result == "game_over":
                            game_over_result = show_game_over_screen()
                            if game_over_result == "restart":
                                # Continue the loop to restart
                                continue
                            else:  # Quit was chosen
                                restart_game = False
                                running = False
                        elif result == "quit":
                            restart_game = False
                            running = False
                    else:
                        restart_game = False
                        running = False
            else:
                running = False
        else:
            running = False
    
    pg.quit()


scale = 2


class DamageIndicator(pg.sprite.Sprite):
    def __init__(self, x, y, damage):
        super().__init__()
        self.font = pg.font.Font(None, 36)  # You can adjust font size here
        self.text = f"-{damage}"  # Shows as "-10" when 10 damage is dealt
        self.color = (255, 0, 0)  # Red color
        self.image = self.font.render(self.text, True, self.color)
        self.rect = self.image.get_rect(center=(x, y))
        self.creation_time = pg.time.get_ticks()
        self.duration = 500  # How long the text stays (in milliseconds)
        self.float_speed = 2  # How fast the text floats up

    def update(self):
        # Move the text upward
        self.rect.y -= self.float_speed

        # Remove the indicator after duration expires
        if pg.time.get_ticks() - self.creation_time > self.duration:
            self.kill()


class Player(pg.sprite.Sprite):
    global MAX_COLS, TILE_SIZE
    def __init__(self, sprite_sheet_path, frame_width, frame_height):
        super().__init__()
        self.sprite_sheet = pg.image.load(sprite_sheet_path).convert_alpha()
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.state = "idle"
        self.velocity_x=0
        self.velocity_y = 0
        self.on_ground = False
        self.animations = {
            "idle": self.load_frames("img\\idle.png"),
            "running": self.load_frames("img\\Runner.png"),
            "crouching": self.load_frames("img\\crouchfinal.png"),
            "shooting": self.load_frames("img\\Fire.png"),
            "jumping": self.load_frames("img\\jump.png"),
            "death": self.load_frames("img\\dead.png")
        }
        self.is_dead = False
        self.death_animation_complete = False
        self.current_animation = self.animations[self.state]
        self.current_frame = 0 
        self.image = self.current_animation[self.current_frame]
        self.rect = self.image.get_rect()
        self.rect.center = (640, 642)
        self.velocity_x = 0  # Add horizontal velocity tracking
        self.speed = 2
        self.animation_timer = pg.time.get_ticks()
        self.animation_delay = 100
        self.facing_left = False
        

        # Jump-related variables
        self.is_jumping = False
        self.jump_velocity = 0
        self.gravity = 0.5
        self.jump_strength = 10
        self.ground_y = self.rect.y

        # Shooting cooldown
        self.last_shot_time = 0
        self.shooting_cooldown = 500
        self.shooting = False

        # Add this line to your existing _init_ method
        self.damage_indicators = pg.sprite.Group()

        # Add these variables for damage effect
        self.is_hurt = False
        self.hurt_timer = 0
        self.hurt_duration = 100  # Duration of red tint in milliseconds
        self.original_image = None  # Store original image for reverting after tint

    def load_frames(self, sprite_sheet_path):
        frames = []
        sprite_sheet = pg.image.load(sprite_sheet_path).convert_alpha()
        sheet_width = sprite_sheet.get_width()
        sheet_height = sprite_sheet.get_height()

        for y in range(0, sheet_height, self.frame_height):
            for x in range(0, sheet_width, self.frame_width):
                frame = sprite_sheet.subsurface((x, y, self.frame_width, self.frame_height))
                frames.append(pg.transform.scale(frame, (self.frame_width * scale, self.frame_height * scale)))
        return frames

    def set_animation(self, state):
        if self.state != state:
            self.state = state
            self.current_animation = self.animations[state]
            self.current_frame = 0

    def shoot(self, bullets_group):
        current_time = pg.time.get_ticks()
        if current_time - self.last_shot_time > self.shooting_cooldown:
            # Create bullet at player's world position
            bullet_x = self.rect.centerx
            bullet_y = self.rect.centery - 15  # Adjust for gun height
            
            # Create the bullet with the player's world position
            bullet = Bullet(bullet_x, bullet_y, self.facing_left)
            bullets_group.add(bullet)
            self.last_shot_time = current_time
            self.set_animation("shooting")
            
    def animate(self):
        current_time = pg.time.get_ticks()
        if current_time - self.animation_timer > self.animation_delay:
            if self.state == "death" and self.current_frame == len(self.current_animation) - 1:
                self.death_animation_complete = True
                return
            self.current_frame = (self.current_frame + 1) % len(self.current_animation)
            self.image = self.current_animation[self.current_frame]
            if self.facing_left:
                self.image = pg.transform.flip(self.image, True, False)
            self.animation_timer = current_time

    def take_damage(self, damage):
        # Create damage indicator
        indicator = DamageIndicator(self.rect.centerx, self.rect.top - 20, damage)
        self.damage_indicators.add(indicator)

        # Apply damage effect
        self.is_hurt = True
        self.hurt_timer = pg.time.get_ticks()

    def apply_damage_effect(self):
        if self.is_hurt:
            if not self.original_image:
                self.original_image = self.image.copy()

            # Create a copy of the current image
            self.image = self.original_image.copy()

            # Get color data for each pixel
            for x in range(self.image.get_width()):
                for y in range(self.image.get_height()):
                    color = self.image.get_at((x, y))
                    if color.a > 0:  # If pixel is not fully transparent
                        # Increase red, decrease other colors
                        red = min(255, color.r + 150)
                        green = color.g // 2
                        blue = color.b // 2
                        # Keep original alpha
                        self.image.set_at((x, y), (red, green, blue, color.a))

            # Check if effect duration is over
            if pg.time.get_ticks() - self.hurt_timer > self.hurt_duration:
                self.is_hurt = False
                if self.original_image:
                    self.image = self.original_image
                    self.original_image = None
        elif self.original_image:
            self.image = self.original_image
            self.original_image = None
    
    def check_collision(self, world, dx, dy):
        # Check horizontal collision
        self.rect.x += dx
        
        for tile_rect in world.collision_rects:
            adjusted_rect = pg.Rect(tile_rect.x + bg_scroll, tile_rect.y + 64,
                                tile_rect.width, tile_rect.height)
            if self.rect.colliderect(adjusted_rect):
                if dx > 0:  # Moving right
                    self.rect.right = adjusted_rect.left
                elif dx < 0:  # Moving left
                    self.rect.left = adjusted_rect.right
        
        # Check vertical collision
        self.rect.y += dy
        self.on_ground = False
        
        for tile_rect in world.collision_rects:
            adjusted_rect = pg.Rect(tile_rect.x + bg_scroll, tile_rect.y + 64,
                                tile_rect.width, tile_rect.height)
            if self.rect.colliderect(adjusted_rect):
                if dy > 0:  # Moving down
                    self.rect.bottom = adjusted_rect.top
                    self.velocity_y = 0
                    self.on_ground = True
                    self.is_jumping = False
                elif dy < 0:  # Jumping up
                    self.rect.top = adjusted_rect.bottom
                    self.velocity_y = 0

    
    def apply_gravity(self):
        self.velocity_y += 0.8  # Gravity
        # Cap falling speed
        if self.velocity_y > 15:
            self.velocity_y = 15

    def jump(self):
        if self.on_ground and not self.is_jumping:
            self.velocity_y = -15
            self.is_jumping = True
            self.on_ground = False
    
    def update(self, keys, bullets_group, world):
        global player_current_health

        current_time = pg.time.get_ticks()

        # Check if player is dead
        if player_current_health <= 0 and not self.is_dead:
            self.is_dead = True
            self.set_animation("death")
            self.current_frame = 0
            return

        # If dead, only handle death animation
        if self.is_dead:
            if not self.death_animation_complete:
                if current_time - self.animation_timer > self.animation_delay:
                    if self.current_frame < len(self.animations["death"]) - 1:
                        self.current_frame += 1
                        self.image = self.animations["death"][self.current_frame]
                        if self.facing_left:
                            self.image = pg.transform.flip(self.image, True, False)
                        self.animation_timer = current_time
                    else:
                        self.death_animation_complete = True
            return

        # Update damage indicators
        self.damage_indicators.update()

        # Check if player has fallen off the screen
        if self.rect.bottom > SCREEN_HEIGHT:
            player_current_health = 0  # Set health to 0 to trigger death state
            return
        if not keys[pg.K_LEFT] and not keys[pg.K_RIGHT]:
            self.velocity_x = 0
        # Handle movement and actions (existing code)
        # Set movement speed based on crouching state
        if keys[pg.K_DOWN]:
            self.speed = 2
            self.set_animation("crouching")
        else:
            self.speed = 1

        # Handle shooting
        if keys[pg.K_SPACE]:
            self.shoot(bullets_group)
            self.set_animation("shooting")

        # Handle jumping
        elif keys[pg.K_UP] and not self.is_jumping and self.on_ground:
            self.jump()

        # Handle other movements
        else:
            if keys[pg.K_LEFT] or keys[pg.K_RIGHT]:
                if not self.is_jumping and not keys[pg.K_DOWN]:
                    self.set_animation("running")
            elif not keys[pg.K_DOWN]:
                if not self.is_jumping:
                    self.set_animation("idle")

        # Apply horizontal movement
        if keys[pg.K_LEFT]:
            self.velocity_x = -self.speed
            self.facing_left = True

        if keys[pg.K_RIGHT]:
            self.velocity_x = self.speed
            self.facing_left = False

        for arrow_pos in world.arrow_tiles:
            arrow_rect = pg.Rect(
                arrow_pos[0] + bg_scroll,  # Adjust for camera scroll
                arrow_pos[1] + 64,         # Adjust for UI offset
                TILE_SIZE, 
                TILE_SIZE
            )
            if self.rect.colliderect(arrow_rect):
                fade_to_black(screen)
                return "quit"

        # Apply physics in the correct order - ONLY ONCE
        self.apply_gravity()
        self.check_collision(world, self.velocity_x, self.velocity_y)

        # Animate and apply damage effects
        self.animate()
        self.apply_damage_effect()

def fade_to_black(screen):
    fade_surface = pg.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    fade_surface.fill((0, 0, 0))
    
    for alpha in range(0, 255, 5):
        fade_surface.set_alpha(alpha)
        screen.blit(fade_surface, (0, 0))
        pg.display.flip()
        pg.time.delay(5)

def show_ending_screen():
    screen = pg.display.set_mode((1280, 720))
    clock = pg.time.Clock()
    
    # Play winner screen music
    try:
        pygame.mixer.music.load("music\\Victory.mp3")
        pygame.mixer.music.play()
    except pygame.error as e:
        print(f"Error loading death screen music: {e}")
    
    # Load and scale background
    try:
        end_bg = pg.image.load("img\\end_screen.jpg").convert()
        end_bg = pg.transform.scale(end_bg, (1280, 720))
    except FileNotFoundError:
        print("End screen background image not found")
        end_bg = None

    # Setup fancy fonts
    try:
        title_font = pg.font.Font("C:\\Users\\ayaan\\Desktop\\OldLondon.ttf", 90)
        subtitle_font = pg.font.Font("C:\\Users\\ayaan\\Desktop\\OldLondon.ttf", 60)
        instruction_font = pg.font.Font("C:\\Users\\ayaan\\Desktop\\OldLondon.ttf", 48)
    except FileNotFoundError:
        # Fallback to system fonts if OldLondon isn't available
        title_font = pg.font.SysFont("georgia", 90)
        subtitle_font = pg.font.SysFont("georgia", 60)
        instruction_font = pg.font.SysFont("georgia", 48)
    
    # Create text surfaces with shadow effect
    def create_text_with_shadow(font, text, color):
        # Create shadow text
        shadow_surface = font.render(text, True, (0, 0, 0))
        # Create main text
        text_surface = font.render(text, True, color)
        return shadow_surface, text_surface
    
    # Create text surfaces with shadow
    title_shadow, title_text = create_text_with_shadow(
        title_font, "Congratulations!", (255, 215, 0)  # Gold color
    )
    subtitle_shadow, subtitle_text = create_text_with_shadow(
        subtitle_font, "You have completed your mission", (255, 255, 255)
    )
    instruction_shadow, instruction_text = create_text_with_shadow(
        instruction_font, "Press any key to exit", (200, 200, 200)
    )
    
    # Get text positions
    title_rect = title_text.get_rect(center=(640, 200))
    title_shadow_rect = title_shadow.get_rect(center=(644, 204))  # Offset for shadow
    
    subtitle_rect = subtitle_text.get_rect(center=(640, 300))
    subtitle_shadow_rect = subtitle_shadow.get_rect(center=(644, 304))
    
    instruction_rect = instruction_text.get_rect(center=(640, 500))
    instruction_shadow_rect = instruction_shadow.get_rect(center=(644, 504))
    
    # Fade in from black
    fade_surface = pg.Surface((1280, 720))
    fade_surface.fill((0, 0, 0))
    
    # Fade in animation
    for alpha in range(255, -1, -5):
        if end_bg:
            screen.blit(end_bg, (0, 0))
        else:
            screen.fill((0, 0, 0))
            
        fade_surface.set_alpha(alpha)
        screen.blit(fade_surface, (0, 0))
        
        if alpha < 200:  # Start showing text when mostly faded in
            screen.blit(title_shadow, title_shadow_rect)
            screen.blit(title_text, title_rect)
        if alpha < 150:
            screen.blit(subtitle_shadow, subtitle_shadow_rect)
            screen.blit(subtitle_text, subtitle_rect)
        if alpha < 100:
            screen.blit(instruction_shadow, instruction_shadow_rect)
            screen.blit(instruction_text, instruction_rect)
            
        pg.display.flip()
        pg.time.delay(5)

    running = True
    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT or event.type == pg.KEYDOWN:
                running = False

        if end_bg:
            screen.blit(end_bg, (0, 0))
        else:
            screen.fill((0, 0, 0))
            
        # Draw text with pulsing effect
        pulse = (pg.time.get_ticks() % 2000) / 2000  # 2 second cycle
        title_alpha = int(200 + 55 * abs(math.sin(pulse * math.pi)))
        
        # Create pulsing text copies
        title_shadow_pulse = title_shadow.copy()
        title_text_pulse = title_text.copy()
        title_shadow_pulse.set_alpha(title_alpha - 55)  # Shadow slightly more transparent
        title_text_pulse.set_alpha(title_alpha)
        
        # Draw all text elements with shadows
        screen.blit(title_shadow_pulse, title_shadow_rect)
        screen.blit(title_text_pulse, title_rect)
        screen.blit(subtitle_shadow, subtitle_shadow_rect)
        screen.blit(subtitle_text, subtitle_rect)
        screen.blit(instruction_shadow, instruction_shadow_rect)
        screen.blit(instruction_text, instruction_rect)
        
        pg.display.flip()
        clock.tick(60)

    return "quit"


def run_level(level_number=0):
    pg.init()
    global running, player_current_health, player_max_health, screen, scroll, scroll_speed, bg_scroll

    clock = pg.time.Clock()

    # Stop any previous music and start gameplay music
    pygame.mixer.music.stop()
    try:
        pygame.mixer.music.load("music\\Bg_music.mp3")
        pygame.mixer.music.set_volume(0.4)  # Set volume to 40%
        pygame.mixer.music.play(-1)  # Loop indefinitely
    except pygame.error as e:
        print(f"Error loading gameplay music: {e}")

    # Load level data
    world_data, enemy_data, player_position = load_level_data(f"level{level_number}_data.csv")

    # Create world
    world = World(world_data)

    # Create player
    player = Player("img\\Runner.png", 32, 32)

    # Set player position
    if player_position:
        player.rect.x, player.rect.y = player_position
        player.ground_y = player.rect.y

    # Spawn enemies from level data
    enemies = spawn_enemies_from_data(enemy_data)

    # Create sprite groups
    all_sprites = pg.sprite.Group(player)
    enemies_group = pg.sprite.Group()
    for enemy in enemies:
        enemies_group.add(enemy)
        all_sprites.add(enemy)
    bullets_group = pg.sprite.Group()

    # Initialize background scroll
    bg_scroll = 0

    running_level = True

    while running_level:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pygame.mixer.music.stop()  # Stop music when quitting
                return "quit"
            # Check for Caps Lock key press
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_CAPSLOCK:
                    fade_to_black(screen)
                    pygame.mixer.music.stop()  # Stop music before ending
                    return show_ending_screen()

        keys = pg.key.get_pressed()

        # Update player
        player.update(keys, bullets_group, world)

        # Check for collision with arrow tile (tile index 3)
        player_world_x = player.rect.x - bg_scroll
        player_tile_x = int(player_world_x // TILE_SIZE)
        player_tile_y = int(player.rect.y // TILE_SIZE)

        # Check if player is on tile 3 (arrow tile)
        if (0 <= player_tile_y < len(world_data) and 
            0 <= player_tile_x < len(world_data[0]) and 
            world_data[player_tile_y][player_tile_x] == 3):
            # Fade to black
            fade_to_black(screen)
            pygame.mixer.music.stop()  # Stop music before ending
            return show_ending_screen()

        # Check if the player has died (health is 0 or fell off-screen)
        if player_current_health <= 0:
            pygame.mixer.music.stop()  # Stop music before game over
            return show_game_over_screen()

        # Handle scrolling based on player movement
        if keys[pg.K_RIGHT]:
            bg_scroll -= 6
        elif keys[pg.K_LEFT]:
            bg_scroll += 6

        # Draw everything
        screen.fill((0, 0, 0))
        draw_bg(bg_scroll)
        world.draw(screen, bg_scroll)

        # Update and draw enemies
        for enemy in enemies_group:
            enemy.update(player, bullets_group, world)
            screen.blit(enemy.image, (enemy.rect.x + bg_scroll, enemy.rect.y))

        # Draw sprites
        for sprite in all_sprites:
            screen.blit(sprite.image, sprite.rect)

        # Draw bullets
        bullets_group.update()
        for bullet in bullets_group:
            screen.blit(bullet.image, bullet.rect)

        # Update and draw enemy spears
        for enemy in enemies_group:
            enemy.spears_group.update()
            enemy.spears_group.draw(screen)

        # Draw damage indicators and health bars
        player.damage_indicators.draw(screen)
        for enemy in enemies_group:
            if not enemy.is_dead:
                draw_tube_health_bar(screen, enemy.rect.x, enemy.rect.y - 20,
                                     enemy.health, max_health, 50, 10)

        draw_player_health_bar_top_left(screen, player_current_health, player_max_health)

        pg.display.flip()
        clock.tick(60)

    pygame.mixer.music.stop()  # Ensure music stops if we exit the loop
    return "quit"






class World():
    def __init__(self, world_data, tile_size=40):
        self.tile_list = []
        self.collision_rects = []
        self.tile_size = tile_size
        self.arrow_tiles = []  # List to store arrow tiles
        
        # Load tile images
        self.tile_images = []
        for x in range(21):
            try:
                img = pg.image.load(f'img\\{x+1}.png').convert_alpha()
                img = pg.transform.scale(img, (tile_size, tile_size))
                self.tile_images.append(img)
            except:
                # Create placeholder
                img = pg.Surface((tile_size, tile_size))
                img.fill((100, 100, 100))
                self.tile_images.append(img)
        
        # Process world data
        for y, row in enumerate(world_data):
            for x, tile in enumerate(row):
                if tile >= 0:
                    if tile == 3:
                        self.arrow_tiles.append((x * tile_size, y * tile_size))
                    # Store tile with its position
                    self.tile_list.append((self.tile_images[tile], x * tile_size, y * tile_size))
                    # Create collision rectangle
                    self.collision_rects.append(pg.Rect(x * tile_size, y * tile_size, tile_size, tile_size))
    
    def draw(self, screen, bg_scroll=0):
        for tile, x, y in self.tile_list:
            screen.blit(tile, (x + bg_scroll, y + 64))  # Keep the +64 adjustment for visual alignment


    def check_collision(self, player_rect):
        collided_rects = []
        for rect in self.collision_rects:
            # Create a new rect that accounts for background scroll
            adjusted_rect = rect.copy()
            adjusted_rect.x += bg_scroll
            
            if player_rect.colliderect(adjusted_rect):
                collided_rects.append(rect)
        return collided_rects

def spawn_enemies_from_data(enemy_data, tile_size=40):
    GROUND_Y = 600 # Adjust this value based on your level design
    
    enemies = []
    for y, row in enumerate(enemy_data):
        for x, enemy_type in enumerate(row):
            if enemy_type == 0 and not any(e.rect.x== x*tile_size for e in enemies):  # Spearman enemy
                enemy = SpearmanEnemy(
                    sprite_sheet_paths={
                        "idle": "img\\spearmenidlelol.png",
                        "running": "img\\spearmenrun.png",
                        "melee_attack": "img\\spearmenattack.png",
                        "spear_throw": "img\\spearmenspearthrow.png",
                        "death": "img\\spearmenrunninggotshotlol.png"
                    },
                    frame_width=32,
                    frame_height=32,
                    x=x * tile_size,
                    y=GROUND_Y,  # Place directly on ground
                    alert_range=500,
                    spear_range=400
                )
                enemies.append(enemy)
    return enemies




def show_story():
    pg.init()
    screen = pg.display.set_mode((1280, 720))
    clock = pg.time.Clock()

    # Initialize the mixer and set up music
    pygame.mixer.init()
    try:
        pygame.mixer.music.load("music\\01 Counterstrike - Condition Zero.mp3")
        pygame.mixer.music.set_volume(0.4)  # Set volume to 40%
        pygame.mixer.music.play(-1)  # Loop indefinitely
    except pygame.error as e:
        print(f"Error loading music: {e}")

    try:
        font = pg.font.Font("C:\\Users\\ayaan\\Desktop\\OldLondon.ttf", 32)
    except:
        font = pg.font.SysFont("georgia", 32)

    # Load and scale background images
    for scene in STORY_SCENES:
        scene["background"] = pg.image.load(scene["background_path"]).convert_alpha()
        scene["background"] = pg.transform.scale(scene["background"], (1280, 720))

    # Text box properties
    text_box_height = 200
    text_box_y = 720 - text_box_height
    text_box_alpha = 160
    border_size = 4
    showing_story = True
    current_scene = 0
    current_text = 0
    text_alpha = 0
    fade_speed = 2
    scene_alpha = 0
    key_pressed = False

    def draw_fancy_text_box(surface, x, y, width, height, border_size):
        # Draw main box with gradient
        box = pg.Surface((width, height), pg.SRCALPHA)  # Allow transparency
        for i in range(height):
            alpha = int(160 * (1 - i / height))
            pg.draw.line(box, (0, 0, 0, alpha), (0, i), (width, i))

        # Draw borders
        pg.draw.rect(box, (139, 69, 19, 255), (0, 0, width, height), border_size)
        pg.draw.rect(box, (218, 165, 32, 255), (border_size, border_size,
                                                width - 2 * border_size, height - 2 * border_size), 1)

        # Corner decorations
        corner_size = 15
        for corner in [(0, 0), (width - corner_size, 0),
                       (0, height - corner_size), (width - corner_size, height - corner_size)]:
            pg.draw.rect(box, (218, 165, 32, 255), (*corner, corner_size, corner_size), 1)

        surface.blit(box, (x, y))

    while showing_story:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pygame.mixer.music.stop()  # Stop music before quitting
                return False
            if event.type == pg.KEYDOWN:
                if not key_pressed:
                    key_pressed = True
                    current_text += 1
                    text_alpha = 0
                    if current_text >= len(STORY_SCENES[current_scene]["story"]):
                        if current_scene >= len(STORY_SCENES) - 1:
                            pygame.mixer.music.stop()  # Stop music when story ends
                            return True
                        current_scene += 1
                        current_text = 0
                        scene_alpha = 0
            if event.type == pg.KEYUP:
                key_pressed = False

        screen.fill((0, 0, 0))

        # Draw background
        scene_alpha = min(scene_alpha + fade_speed, 255)
        current_bg = STORY_SCENES[current_scene]["background"].copy()
        current_bg.set_alpha(scene_alpha)
        screen.blit(current_bg, (0, 0))

        # Draw text box and text
        draw_fancy_text_box(screen, 0, text_box_y, 1280, text_box_height, border_size)
        text_alpha = min(text_alpha + fade_speed, 255)
        current_story_text = STORY_SCENES[current_scene]["story"][current_text]

        # Word wrap
        words = current_story_text.split()
        lines = []
        current_line = []
        for word in words:
            test_line = ' '.join(current_line + [word])
            if font.size(test_line)[0] <= 1200:
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
        lines.append(' '.join(current_line))

        # Draw text
        for i, line in enumerate(lines):
            # Shadow
            shadow_surface = font.render(line, True, (0, 0, 0))
            shadow_surface.set_alpha(text_alpha)
            shadow_rect = shadow_surface.get_rect(topleft=(42, text_box_y + 22 + i * 35))
            screen.blit(shadow_surface, shadow_rect)

            # Main text
            text_surface = font.render(line, True, (255, 223, 186))
            text_surface.set_alpha(text_alpha)
            text_rect = text_surface.get_rect(topleft=(40, text_box_y + 20 + i * 35))
            screen.blit(text_surface, text_rect)

        # Continue prompt
        pulse = (pg.time.get_ticks() % 1000) / 1000
        continue_alpha = int(128 + 127 * pulse)
        continue_text = font.render("Press any key to continue", True, (218, 165, 32))
        continue_text.set_alpha(continue_alpha)
        continue_rect = continue_text.get_rect(bottomright=(1260, 710))
        screen.blit(continue_text, continue_rect)

        pg.display.flip()
        clock.tick(60)

    pygame.mixer.music.stop()  # Ensure music stops if we exit the loop
    return False


def show_game_over_screen():
    screen = pg.display.set_mode((1280, 720))
    clock = pg.time.Clock()
    
    # Play death screen music
    try:
        pygame.mixer.music.load("music\\evil_morty_song.mp3")
        pygame.mixer.music.set_volume(0.4)  # Set volume to 40%
        pygame.mixer.music.play(-1)  # Loop indefinitely
    except pygame.error as e:
        print(f"Error loading death screen music: {e}")
    
    # Create a fade in transition
    fade_surface = pg.Surface((1280, 720))
    fade_surface.fill((0, 0, 0))
    
    # Load and scale level background
    try:
        bg = pg.image.load("img\\bleh.png").convert()
        bg = pg.transform.scale(bg, (1280, 720))
        
        # Create dark tint
        tint = pg.Surface((1280, 720))
        tint.fill((0, 0, 0))
        tint.set_alpha(180)  # Adjust darkness level
    except:
        bg = None

    # Create buttons
    restart_button = Button("Restart Game", 400)
    quit_button = Button("Quit Game", 500)
    
    running = True
    fade_alpha = 255
    fade_speed = 3

    while running:
        mouse_pos = pg.mouse.get_pos()

        for event in pg.event.get():
            if event.type == pg.QUIT:
                pygame.mixer.music.stop()  # Stop music before quitting
                return "quit"
            if event.type == pg.MOUSEBUTTONDOWN:
                if restart_button.draw(screen).collidepoint(mouse_pos):
                    pygame.mixer.music.stop()  # Stop music before restarting
                    return "restart"
                if quit_button.draw(screen).collidepoint(mouse_pos):
                    pygame.mixer.music.stop()  # Stop music before quitting
                    return "quit"

        # Draw background
        if bg:
            screen.blit(bg, (0, 0))
            screen.blit(tint, (0, 0))
        else:
            screen.fill((0, 0, 0))

        # Draw buttons
        restart_button.draw(screen)
        quit_button.draw(screen)

        # Update hover states
        restart_button.is_hovered = restart_button.draw(screen).collidepoint(mouse_pos)
        quit_button.is_hovered = quit_button.draw(screen).collidepoint(mouse_pos)

        pg.display.flip()
        clock.tick(60)

    pygame.mixer.music.stop()  # Ensure music stops if we exit the loop
    return "quit"


class Button:
    def __init__(self, text, y_position):
        self.text = text
        self.y_position = y_position
        self.color = (218, 165, 32)      # Darker gold
        self.hover_color = (255, 215, 0)  # Brighter gold when hovered
        self.is_hovered = False
        self.alpha = 255
        self.pulse_value = 0
        try:
            self.font = pg.font.Font("C:\\Users\\ayaan\\Desktop\\OldLondon.ttf", 48)
        except:
            self.font = pg.font.Font(None, 48)


    def draw(self, surface):
        if self.is_hovered:
            self.pulse_value = (pg.time.get_ticks() % 1000) / 1000
            self.alpha = int(200 + 55 * self.pulse_value)

        # Add shadow effect
        shadow_surface = self.font.render(self.text, True, (0, 0, 0))
        shadow_rect = shadow_surface.get_rect(center=(642, self.y_position + 2))
        surface.blit(shadow_surface, shadow_rect)

        # Main text
        text_surface = self.font.render(self.text, True, 
                                      self.hover_color if self.is_hovered else self.color)
        text_surface.set_alpha(self.alpha)
        text_rect = text_surface.get_rect(center=(640, self.y_position))

        if self.is_hovered:
            # Glowing effect when hovered
            glow_size = int(10 * (1 + 0.2 * math.sin(self.pulse_value * 2 * math.pi)))
            for i in range(glow_size):
                glow_alpha = int(100 * (1 - i/glow_size))
                glow_color = self.hover_color + (glow_alpha,)
                glow_rect = text_rect.inflate(i*2, i*2)
                pg.draw.rect(surface, glow_color, glow_rect, 1)

            # Decorative lines with gradient
            line_length = 120
            for i in range(3):
                line_alpha = int(255 * (1 - i/3))
                line_color = self.color + (line_alpha,)
                pg.draw.line(surface, line_color,
                            (text_rect.left - line_length + i*2, self.y_position + i),
                            (text_rect.left - 20, self.y_position + i), 2)
                pg.draw.line(surface, line_color,
                            (text_rect.right + 20, self.y_position + i),
                            (text_rect.right + line_length - i*2, self.y_position + i), 2)

            # Ornate end pieces
            for x in [text_rect.left - line_length, text_rect.right + line_length]:
                pg.draw.circle(surface, self.color, (x, self.y_position), 4)
                pg.draw.circle(surface, self.hover_color, (x, self.y_position), 2)

        surface.blit(text_surface, text_rect)
        return text_rect


if __name__ == "__main__":
    main()