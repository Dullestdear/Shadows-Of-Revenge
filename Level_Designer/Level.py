import pygame
import csv

# Initialize pygame
pygame.init()
clock = pygame.time.Clock()
FPS = 60

# Game window dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 640
LOWER_MARGIN = 100
SIDE_MARGIN = 300
screen = pygame.display.set_mode((SCREEN_WIDTH + SIDE_MARGIN, SCREEN_HEIGHT + LOWER_MARGIN))
pygame.display.set_caption('Level Designer')

# Game variables
ROWS = 16
MAX_COLS = 150
TILE_SIZE = SCREEN_HEIGHT // ROWS
TILE_TYPES = 21  # Number of different tile types
ENEMY_TYPES = 1  # Number of enemy types (currently just Spearman)
level = 0
current_tile = 0
current_enemy = None
player_tile = 4  # Using tile number 4 for player
player_placed = False  # Track if player has been placed

level = 0
current_tile = 0
current_enemy = None
scroll_left = False
scroll_right = False
scroll = 0
scroll_speed = 1

# Define colors
GREEN = (144, 201, 120)
WHITE = (255, 255, 255)
RED = (200, 25, 25)

# Define font
font = pygame.font.SysFont('Futura', 30)

# Button class
class Button():
    def __init__(self, x, y, image, scale):
        width = image.get_width()
        height = image.get_height()
        self.image = pygame.transform.scale(image, (int(width * scale), int(height * scale)))
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.clicked = False

    def draw(self, surface):
        action = False
        # Get mouse position
        pos = pygame.mouse.get_pos()
        
        # Check mouseover and clicked conditions
        if self.rect.collidepoint(pos):
            if pygame.mouse.get_pressed()[0] == 1 and self.clicked == False:
                action = True
                self.clicked = True
        
        if pygame.mouse.get_pressed()[0] == 0:
            self.clicked = False
            
        # Draw button
        surface.blit(self.image, (self.rect.x, self.rect.y))
        return action

# Load images with error handling
try:
    # Background images
    pine1_img = pygame.image.load('img\\pine1.png').convert_alpha()
    pine2_img = pygame.image.load('img\\pine2.png').convert_alpha()
    mountain_img = pygame.image.load('img\\mountain.png').convert_alpha()
    sky_img = pygame.image.load('img\\sky.png').convert_alpha()
    
    # Button images
    save_img = pygame.image.load('img\\save_btn.png').convert_alpha()
    load_img = pygame.image.load('img\\load_btn.png').convert_alpha()
except FileNotFoundError as e:
    print(f"Error loading background images: {e}")
    # Create placeholder images if originals can't be loaded
    pine1_img = pygame.Surface((SCREEN_WIDTH, 200))
    pine1_img.fill((100, 150, 100))
    pine2_img = pygame.Surface((SCREEN_WIDTH, 100))
    pine2_img.fill((50, 100, 50))
    mountain_img = pygame.Surface((SCREEN_WIDTH, 300))
    mountain_img.fill((100, 100, 100))
    sky_img = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    sky_img.fill((135, 206, 235))
    
    # Placeholder button images
    save_img = pygame.Surface((100, 50))
    save_img.fill((0, 255, 0))
    load_img = pygame.Surface((100, 50))
    load_img.fill((0, 0, 255))

# Store tiles in a list
img_list = []
for x in range(TILE_TYPES):
    try:
        img = pygame.image.load(f'img\\{x+1}.png').convert_alpha()
        original_size = img.get_size()
        scale_factor = TILE_SIZE / max(original_size)
        new_size = (int(original_size[0] * scale_factor), 
                   int(original_size[1] * scale_factor))
        img = pygame.transform.scale(img, new_size)
        img_list.append(img)
    except FileNotFoundError:
        print(f"Warning: Could not load {x+1}.png")
        # Create placeholder
        img = pygame.Surface((TILE_SIZE, TILE_SIZE))
        img.fill((128, 128, 128))
        img_list.append(img)


# Load enemy preview images
enemy_img_list = []
try:
    spearman_preview = pygame.image.load('img\\spearmenidlelol.png').convert_alpha()
    spearman_preview = pygame.transform.scale(spearman_preview, (TILE_SIZE, TILE_SIZE))
    enemy_img_list.append(spearman_preview)
except FileNotFoundError:
    print("Warning: Could not load spearman preview image")
    placeholder = pygame.Surface((TILE_SIZE, TILE_SIZE))
    placeholder.fill((255, 0, 0))  # Red placeholder for enemy
    enemy_img_list.append(placeholder)

# Create empty world data
world_data = []
enemy_data = []  # List to store enemy positions
player_position = [-1, -1]  # Track player position
for row in range(ROWS):
    r = [-1] * MAX_COLS
    e = [-1] * MAX_COLS  # -1 means no enemy
    world_data.append(r)
    enemy_data.append(e)

# Create ground (bottom row filled with tile type 0)
for tile in range(0, MAX_COLS):
    world_data[ROWS - 1][tile] = 0

# Function for outputting text onto the screen
def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))

# Function for drawing background
def draw_bg():
    screen.fill(GREEN)
    width = sky_img.get_width()
    for x in range(4):
        screen.blit(sky_img, ((x * width) - scroll * 0.5, 0))
        screen.blit(mountain_img, ((x * width) - scroll * 0.6, SCREEN_HEIGHT - mountain_img.get_height() - 300))
        screen.blit(pine1_img, ((x * width) - scroll * 0.7, SCREEN_HEIGHT - pine1_img.get_height() - 150))
        screen.blit(pine2_img, ((x * width) - scroll * 0.8, SCREEN_HEIGHT - pine2_img.get_height()))

# Function to draw grid
def draw_grid():
    # Vertical lines
    for c in range(MAX_COLS + 1):
        pygame.draw.line(screen, WHITE, (c * TILE_SIZE - scroll, 0), (c * TILE_SIZE - scroll, SCREEN_HEIGHT))
    # Horizontal lines
    for c in range(ROWS + 1):
        pygame.draw.line(screen, WHITE, (0, c * TILE_SIZE), (SCREEN_WIDTH, c * TILE_SIZE))

# Function for drawing the world tiles and enemies
def draw_world():
    # Draw tiles
    for y, row in enumerate(world_data):
        for x, tile in enumerate(row):
            if tile >= 0:
                # Highlight player tile with a blue border if it's the player tile (4)
                if tile == player_tile:
                    pygame.draw.rect(screen, (0, 0, 255), 
                                    (x * TILE_SIZE - scroll, y * TILE_SIZE, TILE_SIZE, TILE_SIZE), 2)
                screen.blit(img_list[tile], (x * TILE_SIZE - scroll, y * TILE_SIZE))
                
    # Draw enemies
    for y, row in enumerate(enemy_data):
        for x, enemy in enumerate(row):
            if enemy >= 0:
                screen.blit(enemy_img_list[enemy], (x * TILE_SIZE - scroll, y * TILE_SIZE))


# Create buttons
save_button = Button(SCREEN_WIDTH // 2, SCREEN_HEIGHT + LOWER_MARGIN - 50, save_img, 1)
load_button = Button(SCREEN_WIDTH // 2 + 200, SCREEN_HEIGHT + LOWER_MARGIN - 50, load_img, 1)

# Create tile buttons
# Original button layout (lines 130-137)
button_list = []
button_col = 0
button_row = 0
for i in range(len(img_list)):
    tile_button = Button(SCREEN_WIDTH + (75 * button_col) + 50, 75 * button_row + 50, img_list[i], 1)
    button_list.append(tile_button)
    button_col += 1
    if button_col == 3:
        button_row += 1
        button_col = 0

# Modified for better spacing
BUTTONS_PER_ROW = 4  # Increased from 3
VERTICAL_SPACING = 85  # Increased from 75

button_list = []
button_col = 0
button_row = 0
for i in range(len(img_list)):
    tile_button = Button(
        SCREEN_WIDTH + (VERTICAL_SPACING * button_col) + 50,
        VERTICAL_SPACING * button_row + 50,
        img_list[i], 1
    )
    button_list.append(tile_button)
    button_col += 1
    if button_col == BUTTONS_PER_ROW:
        button_row += 1
        button_col = 0

# Create enemy buttons
enemy_button_list = []
enemy_button_col = 0
enemy_button_row = 8  # Start enemy buttons below tile buttons

for i in range(len(enemy_img_list)):
    enemy_button = Button(
        SCREEN_WIDTH + (VERTICAL_SPACING * enemy_button_col) + 50,
        VERTICAL_SPACING * enemy_button_row + 50,
        enemy_img_list[i], 1
    )
    enemy_button_list.append(enemy_button)
    enemy_button_col += 1
    if enemy_button_col == BUTTONS_PER_ROW:
        enemy_button_row += 1
        enemy_button_col = 0

# Main game loop
run = True
while run:
    clock.tick(FPS)
    
    # Draw background, grid and world
    draw_bg()
    draw_grid()
    draw_world()
    
    # Display level info
    draw_text(f'Level: {level}', font, WHITE, 10, SCREEN_HEIGHT + LOWER_MARGIN - 90)
    draw_text('Press UP or DOWN to change level', font, WHITE, 10, SCREEN_HEIGHT + LOWER_MARGIN - 60)
    
    # Save and load functionality
    if save_button.draw(screen):
    # Save level data
        try:
            # In the level editor's save function
            with open(f'level{level}_data.csv', 'w', newline='') as csvfile:
                writer = csv.writer(csvfile, delimiter=',')
                for row in range(ROWS):
                    # Combine world and enemy data
                    combined_row = world_data[row] + enemy_data[row]
                    writer.writerow(combined_row)

            print(f"Level {level} saved successfully!")
        except Exception as e:
            print(f"Error saving level: {e}")

    
    if load_button.draw(screen):
        # Load level data
        try:
            scroll = 0  # Reset scroll back to the start of the level
            with open(f'level{level}_data.csv', 'r', newline='') as csvfile:
                reader = csv.reader(csvfile, delimiter=',')
                for x, row in enumerate(reader):
                    mid = len(row) // 2
                    world_data[x] = [int(tile) for tile in row[:mid]]
                    enemy_data[x] = [int(enemy) for enemy in row[mid:]]
            print(f"Level {level} loaded successfully!")
        except FileNotFoundError:
            print(f"No saved data found for level {level}")
        except Exception as e:
            print(f"Error loading level: {e}")
    
    # Draw tile panel
    pygame.draw.rect(screen, GREEN, (SCREEN_WIDTH, 0, SIDE_MARGIN, SCREEN_HEIGHT))
    
    # Handle tile/enemy selection
    for button_count, i in enumerate(button_list):
        if i.draw(screen):
            current_tile = button_count
            current_enemy = None  # Deselect enemy when tile selected
    
    for button_count, i in enumerate(enemy_button_list):
        if i.draw(screen):
            current_enemy = button_count
            current_tile = None  # Deselect tile when enemy selected
    
    # Highlight the selected item
    if current_tile is not None:
        pygame.draw.rect(screen, RED, button_list[current_tile].rect, 3)
    elif current_enemy is not None:
        pygame.draw.rect(screen, RED, enemy_button_list[current_enemy].rect, 3)
    
    # Handle scrolling
    if scroll_left and scroll > 0:
        scroll -= 5 * scroll_speed
    if scroll_right and scroll < (MAX_COLS * TILE_SIZE) - SCREEN_WIDTH:
        scroll += 5 * scroll_speed
    
    # Add new tiles/enemies to the screen
    pos = pygame.mouse.get_pos()
    x = (pos[0] + scroll) // TILE_SIZE
    y = pos[1] // TILE_SIZE
    
    # Check that the coordinates are within the tile area
    if 0 <= x < MAX_COLS and 0 <= y < ROWS:  # Prevent index errors
        # Left mouse button - place tile/enemy
        # Check that the coordinates are within the tile area

        if 0 <= x < MAX_COLS and 0 <= y < ROWS:  # Prevent index errors
        # Left mouse button - place tile/enemy
            if pygame.mouse.get_pressed()[0] == 1:
                if current_tile is not None:
                    # If placing player tile (4)
                    if current_tile == player_tile:
                        # Remove previous player tile if it exists
                        for row_idx, row in enumerate(world_data):
                            for col_idx, tile in enumerate(row):
                                if tile == player_tile:
                                    world_data[row_idx][col_idx] = -1
                
                        # Place new player tile
                        world_data[y][x] = current_tile
                        player_position = [x, y]
                    elif world_data[y][x] != current_tile:
                        world_data[y][x] = current_tile
                elif current_enemy is not None and enemy_data[y][x] != current_enemy:
                        enemy_data[y][x] = current_enemy
            # Right mouse button - delete tile/enemy
            if pygame.mouse.get_pressed()[2] == 1:
                world_data[y][x] = -1
                enemy_data[y][x] = -1

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        
        # Keyboard controls
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                level += 1
            if event.key == pygame.K_DOWN and level > 0:
                level -= 1
            if event.key == pygame.K_LEFT:
                scroll_left = True
            if event.key == pygame.K_RIGHT:
                scroll_right = True
            if event.key == pygame.K_RSHIFT:
                scroll_speed = 5
        
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT:
                scroll_left = False
            if event.key == pygame.K_RIGHT:
                scroll_right = False
            if event.key == pygame.K_RSHIFT:
                scroll_speed = 1
    
    # Update display
    pygame.display.update()

# Quit pygame
pygame.quit()
