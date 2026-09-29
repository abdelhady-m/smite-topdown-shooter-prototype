import pygame
import sys
import math
import pygame_widgets
from pytmx.util_pygame import load_pygame
from pygame_widgets.slider import Slider
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

pygame.init()

#Screen
screen = pygame.display.set_mode((1300,800))
pygame.display.set_caption("Top-Down Shooter")

#Map
tmx_data = load_pygame(BASE_DIR / 'Project Folder' / 'Map' / 'tilemaptake1.tmx')

clock = pygame.time.Clock()
game_state = "menu"

#Background Music
pygame.mixer.music.load(BASE_DIR / 'Project Folder' / 'Audio' / 'ActionMusic.mp3')
pygame.mixer.music.play(-1)  # Play the background music on loop

#Gunshot Sound Effect
gunshot_sound = pygame.mixer.Sound(BASE_DIR / 'Project Folder' / 'Audio' / 'PistolShot.mp3')
gunshot_sound_enemy = pygame.mixer.Sound(BASE_DIR / 'Project Folder' / 'Audio' / 'AK2.mp3')

#Music Volume Slider
music_slider = Slider(
    screen,
    75, 250,     # x, y
    1000, 25,      # width, height
    min=0,
    max=100,
    step=1,
    initial=50
)

#Volume Slider
sfx_slider = Slider(
    screen,
    75, 375,
    1000, 25,
    min=0,
    max=100,
    step=1,
    initial=50
)



#Classes ---------------------------------------------------------------------------------

#Button Class -----------------------------------------------------------------------------
class Button:
    def __init__(self, x, y, width, height, text, color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color

    def draw(self, screen, font):
        pygame.draw.rect(screen, self.color, self.rect)

        text_surface = font.render(self.text, True, (255,255,255))
        text_rect = text_surface.get_rect(center = self.rect.center)
        screen.blit(text_surface, text_rect)

    def clicked(self, event):
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        ) 

#Player Class -----------------------------------------------------------------------------

#--------------------------------------------------------
#Player Class Setup
class Player(pygame.sprite.Sprite):

    def __init__(self):
        super().__init__()

        self.angle = 0
        self.muzzle_offset = pygame.math.Vector2(65, 10.18)

        self.shoot_cooldown = 1000 #milliseconds
        self.last_shot_time = 0
        
        #Idle Animation Frames
        self.player_idle = []
        raw_movement = pygame.image.load(BASE_DIR / 'Project Folder' / 'Graphics' / 'MyGraphics' / 'Hitman.png').convert_alpha()
        scaled_movement = pygame.transform.smoothscale(raw_movement, (130,86))
        self.player_idle.append(scaled_movement)

        #Movement Animation Frames
        self.player_walk = []
        raw_movement = pygame.image.load(BASE_DIR / 'Project Folder' / 'Graphics' / 'MyGraphics' / 'Hitman.png').convert_alpha()
        scaled_movement = pygame.transform.smoothscale(raw_movement, (130,86))
        self.player_walk.append(scaled_movement)

        self.player_index = 0

        #Start with first idle frame
        self.original_image = self.player_idle[0]
        self.image = self.original_image

        self.rect = self.image.get_rect(center = (1387,1340))

        self.pos = pygame.math.Vector2(1387,1340) #Placed in init rather than player input to avoid constantly resetting to the position
        self.speed = 5
        self.health = 200

        self.hitbox = pygame.Rect(0, 0, 40, 40) #Hitbox for collision detection
        self.hitbox.center = self.pos

#Player Class Movement (Vector)
    def player_input(self, walls):
        keys = pygame.key.get_pressed()
        move_vec = pygame.math.Vector2(0,0)
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            move_vec.x -= 10
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            move_vec.x += 10
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            move_vec.y -= 10
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            move_vec.y += 10

        if move_vec.length() > 0: #If normalize divided by zero, the program would crash.
            move_vec = move_vec.normalize() * self.speed  #Normalize takes any vector and rescales it to have a length of exactly 1 without changing its direction. It divides vector values by their own length so that the resultant velocity of two displacement vectors is still 1.

#Horizontal and Vertical Collision Detection
        self.pos.x += move_vec.x
        self.hitbox.centerx = int(self.pos.x)
        for wall in walls:
            if self.hitbox.colliderect(wall.rect):
                if move_vec.x > 0:  # Moving Right
                    self.hitbox.right = wall.rect.left
                elif move_vec.x < 0:  # Moving Left
                    self.hitbox.left = wall.rect.right
                self.pos.x = self.hitbox.centerx

        self.pos.y += move_vec.y
        self.hitbox.centery = int(self.pos.y)
        for wall in walls:
            if self.hitbox.colliderect(wall.rect):
                if move_vec.y > 0:  # Moving Down
                    self.hitbox.bottom = wall.rect.top
                elif move_vec.y < 0:  # Moving Up
                    self.hitbox.top = wall.rect.bottom
                self.pos.y = self.hitbox.centery

#Player Movement Animation
    def animation_state(self):
        keys = pygame.key.get_pressed()
        moving = keys[pygame.K_LEFT] or keys[pygame.K_RIGHT] or keys[pygame.K_UP] or keys[pygame.K_DOWN] or keys[pygame.K_a] or keys[pygame.K_d] or keys[pygame.K_w] or keys[pygame.K_s]

        if moving:
            self.player_index += 0.3 #Controls movementanimation speed

            if self.player_index >= len(self.player_walk):
                self.player_index = 0

            self.original_image = self.player_walk[int(self.player_index)] #Picks the current movement frame

        else:
            self.player_index += 0.3 #Controls idle animation speed

            if self.player_index >= len(self.player_idle):
                self.player_index = 0
            
            self.original_image = self.player_idle[int(self.player_index)]

#Rotating Player to Face the Mouse (atan2)
    def rotate_to_mouse(self, camera):
        mouse_pos = pygame.math.Vector2(pygame.mouse.get_pos())
        mouse_world_pos = mouse_pos + camera  #Convert mouse position to world coordinates
        
        direction = mouse_world_pos - self.pos  #Vector from player towards the mouse

        self.angle = math.degrees(math.atan2(-direction.y, direction.x))

        self.image = pygame.transform.rotozoom(self.original_image, self.angle, 1)
        self.rect = self.image.get_rect(center = self.pos)

#Gun Muzzle Position
    def get_muzzle_world_pos(self):
        rotated_offset = self.muzzle_offset.rotate(-self.angle)
        muzzle_world_pos = self.pos + rotated_offset #Determines gun muzzle position based on player position and the direction they're facing.

        return muzzle_world_pos

#Update Player Class
    def update(self, walls):
        self.player_input(walls)
        self.animation_state()
#--------------------------------------------------------

#--------------------------------------------------------
#Enemy Class
#Enemy Class Setup
class Enemy(pygame.sprite.Sprite):

    def __init__(self, x, y, angle = 0, patrol_points = None): #Now I can include the angle they're facing in coords when I spawn them.
        super().__init__()

        self.state = "idle"
        self.detection_range = 480
        self.attack_range = 430
        self.personal_space = 100

        self.alerted = False

        self.patrol_points = patrol_points or []
        self.patrol_index = 0

        self.angle = angle

        self.muzzle_offset = pygame.math.Vector2(43.61, 23.429)

        self.shoot_cooldown = 1000 #milliseconds
        self.last_shot_time = 0

        self.reaction_time = 500 #ms
        self.spotted_time = None

        self.last_seen_position = None
        self.chase_memory = 2000
        self.last_seen_time = None
        
        #Idle Animation Frames
        self.enemy_idle = []
        for i in range(20):
            raw_idle_image = pygame.image.load(BASE_DIR / 'Project Folder' / 'Graphics' / 'Top_Down_Survivor' / 'handgun' / 'idle' / f'survivor-idle_handgun_{i}.png').convert_alpha()
            scaled_idle_image = pygame.transform.scale(raw_idle_image, (100,100))
            self.enemy_idle.append(scaled_idle_image)
        #Movement Animation Frames
        self.enemy_walk = []
        for i in range(20):
            raw_walk_image = pygame.image.load(BASE_DIR / 'Project Folder' / 'Graphics' / 'Top_Down_Survivor' / 'handgun' / 'move' / f'survivor-move_handgun_{i}.png').convert_alpha()
            scaled_walk_image = pygame.transform.scale(raw_walk_image, (100,100))
            self.enemy_walk.append(scaled_walk_image)

        self.enemy_index = 0

        #Start with first idle frame
        self.original_image = self.enemy_idle[0]

        self.pos = pygame.math.Vector2(x, y)

        self.image = pygame.transform.rotate(self.original_image, self.angle)

        self.rect = self.image.get_rect(center = self.pos)

        self.hitbox = pygame.Rect(0, 0, 40, 70) #Hitbox for collision detection
        self.hitbox.center = self.pos

        self.speed = 5
        self.patrol_speed = 2
        self.health = 100

#Field of View Cone
    def line_of_sight(self, player, walls, use_fov = True):
        distance_to_player = player.pos - self.pos

        if distance_to_player.length() > self.detection_range:
            return False
        if distance_to_player.length() == 0:
            return True

        if use_fov:
            facing = pygame.math.Vector2(1,0).rotate(-self.angle)
            angle_to_player = facing.angle_to(distance_to_player)

            if abs(angle_to_player) > 75:
                return False

        #Checking for walls blocking enemy vision
        for wall in walls:
            if wall.rect.clipline(self.pos, player.pos):
                return False
        return True

#Patrol
    def patrol(self, walls):
        if not self.patrol_points:
            return

        target = pygame.math.Vector2(self.patrol_points[self.patrol_index])

        distance = self.pos.distance_to(target)

        if distance < 5:
            self.patrol_index += 1

            if self.patrol_index >= len(self.patrol_points):
                self.patrol_index = 0

            return

        self.rotate_to_target(target)

        self.move_toward(target, walls, speed = self.patrol_speed) #This line does all the movement and collision work for patrol

#Rotate to Target (Patrol)
    def rotate_to_target(self, target):
        direction = pygame.math.Vector2(target) - self.pos

        if direction.length() > 0:
            self.angle = math.degrees(math.atan2(-direction.y, direction.x))
        self.image = pygame.transform.rotate(self.original_image, self.angle)

        self.rect = self.image.get_rect(center = self.pos)

#UPDATE ENEMY STATE
    def update_state(self, player, walls):

        distance = self.pos.distance_to(player.pos)

        if self.alerted:
            can_see_player = self.line_of_sight(player, walls, use_fov = False)
        else:
            can_see_player = self.line_of_sight(player, walls, use_fov = True)

        if can_see_player:

            self.alerted = True

            self.last_seen_position = player.pos.copy()
            self.last_seen_time = pygame.time.get_ticks()

            if distance <= self.attack_range:
                self.state = "attack"
            else:
                self.state = "chase"
                self.spotted_time = None
        else:
            current_time = pygame.time.get_ticks()

            if self.last_seen_position is not None:
                distance_to_last_seen = self.pos.distance_to(self.last_seen_position)

                if (distance_to_last_seen > 20
                    and current_time - self.last_seen_time < self.chase_memory):
                    self.state = "search"

                elif self.patrol_points:
                    self.state = "patrol"

                else:
                    self.state = "idle"

            elif self.patrol_points:
                self.state = "patrol"

            else:
                self.state = "idle"   

            self.spotted_time = None

#Enemy Movement
    def move_toward(self, target, walls, stopping_distance = 0, speed = None):
        direction = pygame.math.Vector2(target) - self.pos
        distance = direction.length()

        if speed is None:
            speed = self.speed

        # if distance <= self.personal_space: #Makes it so they cant cross a 50px distance from player
        #     return

        if distance <= stopping_distance:
            return
        if distance > 0:
            direction = direction.normalize()

        move_distance = min(
            speed,
            distance - stopping_distance
        )
        #This line makes the enemy stop at the exact boundary, even by moving a distance smaller than 5 px to reach it.

        move_vec = direction * move_distance

        #Horizontal and Vertical Collision Detection
        self.pos.x += move_vec.x
        self.hitbox.centerx = int(self.pos.x)
        for wall in walls:
            if self.hitbox.colliderect(wall.rect):
                if move_vec.x > 0:  # Moving Right
                    self.hitbox.right = wall.rect.left
                elif move_vec.x < 0:  # Moving Left
                    self.hitbox.left = wall.rect.right
                self.pos.x = self.hitbox.centerx

        self.pos.y += move_vec.y
        self.hitbox.centery = int(self.pos.y)
        for wall in walls:
            if self.hitbox.colliderect(wall.rect):
                if move_vec.y > 0:  # Moving Down
                    self.hitbox.bottom = wall.rect.top
                elif move_vec.y < 0:  # Moving Up
                    self.hitbox.top = wall.rect.bottom
                self.pos.y = self.hitbox.centery

        self.rect.center = (int(self.pos.x), int(self.pos.y)) #Keeps visible sprite attached to world position

#Enemy Animation State
    def animation_state(self):

        if self.state in ("chase", "attack", "patrol", "search"):
            frames = self.enemy_walk
            self.enemy_index += 0.3 #Controls movement animation speed

            if self.enemy_index >= len(self.enemy_walk):
                    self.enemy_index = 0

            self.original_image = self.enemy_walk[int(self.enemy_index)]

        else:
            frames = self.enemy_idle
            self.enemy_index += 0.3 #Controls movement animation speed

            if self.enemy_index >= len(self.enemy_idle):
                    self.enemy_index = 0

            self.original_image = self.enemy_idle[int(self.enemy_index)]

#Rotation Toward the Player (IF IN FIELD OF VIEW)
    def rotate_to_player(self, player):

        direction = player.pos - self.pos

        if direction.length() > 0:
            self.angle = math.degrees(math.atan2(-direction.y, direction.x))

        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect(center=self.pos)

#Enemy Attack Method
    def attack(self, player, bullet_group):
        current_time = pygame.time.get_ticks() #Setting time for shooting cooldown

        #Time starts being recorded the first frame enemy enters attack state (It's more of an attack start time than spotted time.)
        if self.spotted_time is None:
            self.spotted_time = current_time #Starting point of time measurement
            return

        #Waiting for reaction delay (to avoid instantly killing player
        if current_time - self.spotted_time < self.reaction_time: #If the time that passed is less than reaction time, enemy doesn't react yet.
            return

        #Shooting after reaction delay (accounting for shooting cooldown)
        if current_time - self.last_shot_time >= self.shoot_cooldown:
            muzzle_pos = self.get_muzzle_world_pos()
            direction = player.pos - muzzle_pos

            bullet = Bullet(muzzle_pos, direction, "enemy")
            bullet_group.add(bullet)

            gunshot_sound_enemy.play()

            self.last_shot_time = current_time

#Gun Muzzle Position
    def get_muzzle_world_pos(self):
        rotated_offset = self.muzzle_offset.rotate(-self.angle)
        muzzle_world_pos = self.pos + rotated_offset #Determines gun muzzle position based on player position and the direction they're facing.

        return muzzle_world_pos

#Update Enemy Class
    def update(self, player, walls, bullet_group):

        self.update_state(player, walls)

        if self.state == "patrol":
            self.patrol(walls)

        elif self.state == "search":
            self.move_toward(self.last_seen_position, walls, stopping_distance = self.personal_space, speed = self.speed)
            self.rotate_to_target(self.last_seen_position)

        elif self.state == "chase" or self.state == "attack":
            self.move_toward(player.pos, walls, self.personal_space)
            self.rotate_to_player(player)        

        self.animation_state()

        if self.state == "attack":
            self.attack(player, bullet_group)   

#Idle state active if none of the if conditions are met.

#--------------------------------------------------------
#Bullet Class

#Bullet Class Setup
class Bullet(pygame.sprite.Sprite):

    def __init__(self, position, direction, owner):
        super().__init__()

        self.owner = owner

        #Temporary Bullet Appearance
        # self.image = pygame.Surface((10, 10), pygame.SRCALPHA)
        # pygame.draw.circle(self.image, (255, 255, 100), (4,4), 4) #Setting color, center point, and circle radius

        #Bullet Appearance
        self.image_raw = pygame.image.load(BASE_DIR / 'Project Folder' / 'Graphics' / 'BULLET2.png').convert_alpha()
        self.image_scaled = pygame.transform.scale(self.image_raw, (30, 20))

        #World Position + Direction
        self.pos = pygame.math.Vector2(position) #Accurate world position
        self.direction = pygame.math.Vector2(direction)

        if self.direction.length() > 0:
            self.direction = self.direction.normalize() #Bullet normalized so that no matter how far the mouse is, the bullet travels a direction with length 1 (multiplied by speed later).

        #Rotation Angle Based on Bullet Direction
        self.angle = math.degrees(math.atan2(-self.direction.y, self.direction.x))
        self.image = pygame.transform.rotate(self.image_scaled, self.angle)

        self.speed = 15

        self.rect = self.image.get_rect(center=self.pos) #Used for drawing/collision

        self.hitbox = pygame.Rect(0, 0, 10, 10) #Hitbox for collision detection
        self.hitbox.center = self.pos

#Update Bullet Class
    def update(self, walls, enemies, player):
        self.pos += self.direction * self.speed #Multiplying a directional unit vector by a scalar speed gives you velocity, a movement vector which is added to the bullet's 2D position vector each frame.

        self.rect.center = (int(self.pos.x), int(self.pos.y))
        self.hitbox.center = (int(self.pos.x), int(self.pos.y))

        for wall in walls:
            if self.hitbox.colliderect(wall.rect):
                self.kill() #If a bullet hits a wall, it's deleted.
                return

        if self.owner == "player":
            for enemy in enemies:
                if self.hitbox.colliderect(enemy.hitbox):
                    enemy.health -= 50
                    self.kill()
                    if enemy.health <= 0:
                        enemy.kill()
                    return
                
        elif self.owner == "enemy":
                if self.hitbox.colliderect(player.hitbox):
                    player.health -= 50
                    self.kill()
                return
#--------------------------------------------------------

#--------------------------------------------------------
#Wall Class

WALL_TILE_SIZE = 40
WALL_TEXTURE_SIZE = 41

class Wall(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        # self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))

        raw_texture = pygame.image.load(BASE_DIR / 'Project Folder' / 'Graphics' / 'greybrick.png').convert_alpha()
        enlarged_texture = pygame.transform.scale(raw_texture, (WALL_TEXTURE_SIZE, WALL_TEXTURE_SIZE))

        self.image = pygame.Surface((WALL_TILE_SIZE, WALL_TILE_SIZE), pygame.SRCALPHA)
        offset_x = (WALL_TILE_SIZE - enlarged_texture.get_width()) // 2
        offset_y = (WALL_TILE_SIZE - enlarged_texture.get_height()) // 2
        self.image.blit(enlarged_texture, (offset_x, offset_y))

        self.rect = self.image.get_rect(topleft=(x,y))
#--------------------------------------------------------

#--------------------------------------------------------
#Restart Game Function

def restart_game():
    global player, player_group, enemy_group, bullet_group

    player = Player()
    player_group = pygame.sprite.GroupSingle()
    player_group.add(player)

    enemy_group = pygame.sprite.Group()

    for obj in enemy_layer:
        angle = float(obj.properties.get("angle", 0))
        enemy = Enemy(obj.x, obj.y, angle, [])
        enemy_group.add(enemy)

    for obj in patrol_layer:
        if hasattr(obj, "points") and obj.points:
            patrol_points = []

            for point_x, point_y in obj.points:
                patrol_points.append((point_x, point_y))

            start_x, start_y = patrol_points[0]
            angle = float(obj.properties.get("angle", 0))

            enemy = Enemy(
                start_x,
                start_y,
                angle,
                patrol_points
            )

            enemy_group.add(enemy)

    bullet_group = pygame.sprite.Group()

#--------------------------------------------------------

#--------------------------------------------------------
#Mouse depending on game state

def set_mouse_for_state():
    if game_state == "playing":
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)
    else:
        pygame.mouse.set_visible(True)
        pygame.event.set_grab(False)        

#--------------------------------------------------------


#-------------------------------------------------------------------------------------------------------------
#Creating the Camera Vector ----------------------------------------------------------------------------------
camera = pygame.math.Vector2(0,0)

#Creating the Player -----------------------------------------------------------------------------------------
player = Player()
player_group = pygame.sprite.GroupSingle()
player_group.add(player)

#Creating Wall Group -----------------------------------------------------------------------------------------
wall_group = pygame.sprite.Group()
# for row_index, row in enumerate(level_map):
#     for col_index, tile in enumerate(row):
#         if tile == "1":
#             wall_group.add(Wall(col_index * WALL_TILE_SIZE, row_index * WALL_TILE_SIZE))

collision_layer = tmx_data.get_layer_by_name("Collision")

for obj in collision_layer:
    wall = pygame.sprite.Sprite()

    wall.rect = pygame.Rect(obj.x, obj.y, obj.width, obj.height) #pygame.Rect with a capital R creates a Rect object.

    wall_group.add(wall)

#Creating the Enemy Group ------------------------------------------------------------------------------------

    #Stationary Enemies
enemy_group = pygame.sprite.Group()
enemy_layer = tmx_data.get_layer_by_name("Enemy Spawns")

for obj in enemy_layer:
    angle = float(obj.properties.get("angle", 0)) #Get the object's angle property. If it doesn't exist, use 0.

    enemy = Enemy(obj.x, obj.y, angle, [])
    enemy_group.add(enemy)

    #Patrolling Enemies
patrol_layer = tmx_data.get_layer_by_name("Patrol Paths")

for obj in patrol_layer:
    if hasattr(obj, "points") and obj.points:
        patrol_points = []

        for point_x, point_y in obj.points:
            # world_x = obj.x + point_x #tiled automatically uses world coordinates
            # world_y = obj.y + point_y
            patrol_points.append((point_x, point_y))

    #Starting the enemy at first point of patrol
        start_x, start_y = patrol_points[0]
        angle = float(obj.properties.get("angle", 0))

        enemy = Enemy(start_x, start_y, angle, patrol_points)
        enemy_group.add(enemy)

#Creating Bullet Group ---------------------------------------------------------------------------------------
bullet_group = pygame.sprite.Group()

#Creating Crosshair ------------------------------------------------------------------------------------------
custom_crosshair = pygame.image.load(BASE_DIR / 'Project Folder' / 'Graphics' / 'aim.png').convert_alpha()
custom_crosshair = pygame.transform.scale(custom_crosshair, (40, 40))

#Creating Floor Tiles ----------------------------------------------------------------------------------------
floor_tile = pygame.image.load(BASE_DIR / 'Project Folder' / 'Graphics' / 'wood.png').convert_alpha()
FLOOR_TILE_SIZE = 130
floor_tile = pygame.transform.scale(floor_tile, (FLOOR_TILE_SIZE, FLOOR_TILE_SIZE))

#Creating Title -----------------------------------------------------------------------------------------------

titlefont = pygame.font.Font(BASE_DIR / 'Project Folder' / 'Font' / 'Onslaughter.ttf', 180)

winfont = pygame.font.Font(BASE_DIR / 'Project Folder' / 'Font' / 'STRIGER.ttf', 180)

gameoverfont = pygame.font.Font(BASE_DIR / 'Project Folder' / 'Font' / 'Onslaughter.ttf', 160)

bodyfont = pygame.font.Font(BASE_DIR / 'Project Folder' / 'Font' / 'Playfair.ttf', 60)

bodyfontsmall = pygame.font.Font(BASE_DIR / 'Project Folder' / 'Font' / 'Helvetica-BoldOblique.ttf', 30)

pausedfont = pygame.font.Font(BASE_DIR / 'Project Folder' / 'Font' / 'Onslaughter.ttf', 160)
pausedbodyfont = pygame.font.Font(BASE_DIR / 'Project Folder' / 'Font' / 'Playfair.ttf', 43)

settingsfont = pygame.font.Font(BASE_DIR / 'Project Folder' / 'Font' / 'Onslaughter.ttf', 100)

title = "SMITE"

title_letters = []

x = 410
y = 165

for letter in title:
    surface = titlefont.render(letter, True, "#f9fcfb")

    rect = surface.get_rect(center = (x,y))

    title_letters.append((surface,rect)) #Blitting each letter individually

    extra_spacing = {
        'S': -50,
        'M': -50,
        'I': 55,
        'T': -60,
        'E': 0
    }

    x += surface.get_width() + extra_spacing.get(letter, 0) #Accounting for each letter's width to add an appropriate gap between it and the next letter.

#--------------------------------
gameover = "GAME OVER"
gameover_letters = []
x = 220
y = 200

for letter in gameover:
    surface = gameoverfont.render(letter, True, "#f9fcfb")

    rect = surface.get_rect(center = (x,y))

    gameover_letters.append((surface,rect)) #Blitting each letter individually

    extra_spacing = {
        'G': -30,
        'A': 13,
        'M': -13,
        'E': -10,
        'O': 13,
        'V': -35,
        'E': -10,
        'R': 10
    }

    x += surface.get_width() + extra_spacing.get(letter, 0) 

#--------------------------------
paused_menu = "PAUSED"
paused_menu_letters = []
x = 350
y = 150

for letter in paused_menu:
    surface = pausedfont.render(letter, True, "#f9fcfb")

    rect = surface.get_rect(center = (x,y))

    paused_menu_letters.append((surface,rect)) #Blitting each letter individually

    extra_spacing = {
        'P': -40,
        'A': 13,
        'U': 0,
        'S': -35,
        'E': 5,
        'D': -35,
    }

    x += surface.get_width() + extra_spacing.get(letter, 0) 
#--------------------------------

#--------------------------------
settings_menu = "SETTINGS"
settings_menu_letters = []
x = 100
y = 100

spacing = [-40, 13, -23, -55, 8, 4, 4, 0]

for i, letter in enumerate(settings_menu):
    surface = settingsfont.render(letter, True, "#f9fcfb")
    rect = surface.get_rect(center=(x,y))
    settings_menu_letters.append((surface,rect))

    x += surface.get_width() + spacing[i]


#--------------------------------

#Creating Buttons -------------------------------------------------------------------------------------------------

#Main Menu --------------------------------------------------------------------------------------------------------
play_button = Button(450, 300, 400, 110,
                     "PLAY",
                     (1, 102, 78))

settings_button = Button(450, 425, 400, 110,
                         "SETTINGS",
                         (70, 70, 90))
quit_button_1 = Button(450, 550, 400, 110,
                     "QUIT",
                     (179, 48, 48))

#Game Over Menu ---------------------------------------------------------------------------------------------------
restart_button = Button(450, 320, 400, 110,
                        "RESTART",
                        (179, 48, 48))

menu_button = Button(280, 445, 750, 110,
                     "RETURN TO MAIN MENU",
                     (179, 48, 48))

quit_button_2 = Button(450, 570, 400, 110,
                     "QUIT",
                     (179, 48, 48))


#Pause Menu -------------------------------------------------------------------------------------------------------
resume_button = Button(360, 250, 550, 90,
                       "RESUME",
                       (1, 102, 78))

restart_button_paused = Button(360, 355, 550, 90,
                        "RESTART",
                        (1, 102, 78))

settings_button_paused = Button(360, 460, 550, 90,
                         "SETTINGS",
                         (70, 70, 90))

menu_button_paused = Button(360, 565, 550, 90,
                     "RETURN TO MAIN MENU",
                     (179, 48, 48))

quit_button_paused = Button(360, 670, 550, 90,
                     "QUIT",
                     (179, 48, 48))

#Settings Page -------------------------------------------------------------------------------------------------------

menu_button_settings = Button(75, 650, 550, 85,
                     "RETURN TO MAIN MENU",
                     (179, 48, 48))

resume_button_settings = Button(75, 550, 550, 85,
                       "RESUME",
                       (1, 102, 78))

#Victory Screen -------------------------------------------------------------------------------------------------------

next_level_button = Button(450, 320, 400, 110,
                        "NEXT LEVEL",
                        "#5E6160")

music_volume_text = bodyfontsmall.render("MUSIC VOLUME", True, "#f9fcfb")
sfx_volume_text = bodyfontsmall.render("SOUND EFFECTS", True, "#f9fcfb")

#Game Loop ----------------------------------------------------------------------------------------------------------------------------

while True:
    shoot_requested = False
    events = pygame.event.get()
#--------------------
    #EVENTS
    for event in events:
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and game_state == "playing": #Left mouse button
                shoot_requested = True
                gunshot_sound.play()  # Play the gunshot sound when shooting
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        # elif event.type == pygame.KEYDOWN:
        #     if event.key == pygame.K_ESCAPE:
        #         pygame.quit()
        #         sys.exit()

        # elif event.type == pygame.WINDOWFOCUSGAINED:
        #     pygame.mouse.set_visible(False)  # Hide the mouse cursor when the window gains focus

        if game_state == "menu":

            if play_button.clicked(event):
                restart_game()
                game_state = "playing"
                set_mouse_for_state()

            if settings_button.clicked(event):
                settings_from = "menu"
                game_state = "settings"
                set_mouse_for_state()
                if resume_button_settings.clicked(event):
                    game_state = "playing"

            if quit_button_1.clicked(event):
                pygame.quit()
                sys.exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if game_state == "playing":
                    game_state = "paused"
                    set_mouse_for_state()
                elif game_state == "paused":
                    game_state = "playing"
                    set_mouse_for_state()

        if game_state == "paused":
            set_mouse_for_state()

            if resume_button.clicked(event):
                game_state = "playing"
            if menu_button_paused.clicked(event):
                game_state = "menu"
                set_mouse_for_state()
            if restart_button_paused.clicked(event):
                restart_game()
                game_state = "playing"
            if settings_button_paused.clicked(event):
                settings_from = "paused"
                game_state = "settings"
                set_mouse_for_state()
            if quit_button_paused.clicked(event):
                pygame.quit()
                sys.exit()

        elif game_state == "settings":
            set_mouse_for_state()

            if menu_button_settings.clicked(event):
                game_state = "menu"
            if resume_button_settings.clicked(event):
                game_state = "playing"

        elif game_state == "gameover":
            set_mouse_for_state()

            if menu_button.clicked(event):
                game_state = "menu"
            if restart_button.clicked(event):
                restart_game()
                game_state = "playing"
            if quit_button_2.clicked(event):
                pygame.quit()
                sys.exit()

        elif game_state == "victory":
            set_mouse_for_state()

            if menu_button.clicked(event):
                game_state = "menu"
            if quit_button_2.clicked(event):
                pygame.quit()
                sys.exit()
            if next_level_button.clicked(event):
                pass

        if game_state == "playing":
            pygame.mouse.set_visible(False)

#--------------------

#--------------------
    #Update Camera Position to Follow Player
    camera.x = player.pos.x - screen.get_width() / 2 #Placing the camera's top left corner at half a screen width left of the player
    camera.y = player.pos.y - screen.get_height() / 2 #Placing the camera's top left corner at half a screen height above the player

    map_width = tmx_data.width * tmx_data.tilewidth
    map_height = tmx_data.height * tmx_data.tileheight

    camera.x = max(0, min(camera.x, map_width - screen.get_width()))
    camera.y = max(0, min(camera.y, map_height - screen.get_height()))

    camera_draw_x = round(camera.x)
    camera_draw_y = round(camera.y)
#--------------------
    def draw_game():
        for layer in tmx_data.visible_layers:
            if hasattr(layer, "tiles"):
                for x, y, image in layer.tiles():
                    screen_x = x * tmx_data.tilewidth - camera_draw_x
                    screen_y = y * tmx_data.tileheight - camera_draw_y

                    screen.blit(image, (screen_x, screen_y))

    #--------------------
        #Rotate Player Using Current Camera Position to Get World Coordinates of Mouse
        if game_state == "playing":
            player.rotate_to_mouse(camera)
    #--------------------

    #--------------------
        #BULLET DISTANCE AND DIRECTION TO MOUSE
        if shoot_requested and game_state == "playing":

            mouse_pos = pygame.math.Vector2(pygame.mouse.get_pos())
            crosshair_world = mouse_pos + camera  #Convert mouse position to world coordinates

            muzzle_pos = player.get_muzzle_world_pos()
            
            direction = crosshair_world - muzzle_pos  #Vector from muzzle towards the mouse

            bullet = Bullet(muzzle_pos, direction, "player")
            bullet_group.add(bullet)
        
        # if player.health <= 0:
        #     game_state = "gameover"    #Dont change game state in draw function
    #--------------------

    #--------------------
        # #Applying Camera Offset to Floor Tiles and Blitting to the Screen
        # floor_offset_x = -camera.x % FLOOR_TILE_SIZE
        # floor_offset_y = -camera.y % FLOOR_TILE_SIZE
        # #You're not creating a gigantic floor image for the whole map. You're just drawing enough repeating tiles to cover the current screen, and shifting their starting position based on the camera.

        # for y in range(int(floor_offset_y - FLOOR_TILE_SIZE), screen.get_height(), FLOOR_TILE_SIZE):
        #     for x in range(int(floor_offset_x - FLOOR_TILE_SIZE), screen.get_width(), FLOOR_TILE_SIZE):
        #         screen.blit(floor_tile, (x, y))
    #--------------------

    #--------------------
        # #Applying Camera Offset to Wall Rects and Blitting to the Screen
        # for wall in wall_group:
        #     wall_screen_rect = wall.rect.copy()
        #     wall_screen_rect.x -= camera_draw_x
        #     wall_screen_rect.y -= camera_draw_y
        #     screen.blit(wall.image, wall_screen_rect)
    #--------------------

    #--------------------
        #Applying Camera Offset to Player Rect and Blitting to the Screen
        player_screen_rect = player.rect.copy()
        player_screen_rect.x -= camera_draw_x
        player_screen_rect.y -= camera_draw_y
        screen.blit(player.image, player_screen_rect)

        # #MUZZLE LOCATI0N TEST
        # muzzle_world = player.get_muzzle_world_pos()
        # muzzle_screen = muzzle_world - camera
        # pygame.draw.circle(
        #     screen,
        #     (255,0,0),
        #     (int(muzzle_screen.x), int(muzzle_screen.y)),
        #     4)
    #--------------------

    #--------------------
        #Applying Camera Offset to Enemy Rect and Blitting to the Screen
        for enemy in enemy_group:
            enemy_screen_rect = enemy.rect.copy()
            enemy_screen_rect.x -= camera_draw_x
            enemy_screen_rect.y -= camera_draw_y
            screen.blit(enemy.image, enemy_screen_rect)


            # enemy_hitbox_screen = enemy.hitbox.copy()
            # enemy_hitbox_screen.x -= camera_draw_x
            # enemy_hitbox_screen.y -= camera_draw_y
            # pygame.draw.rect(screen, (255, 0, 0), enemy_hitbox_screen, 2)
    # #--------------------

    #--------------------
        #Applying Camera Offset to Bullet Rects and Blitting to the Screen (Same as walls)
        for bullet in bullet_group:
            bullet_screen_rect = bullet.rect.copy()
            bullet_screen_rect.x -= camera_draw_x #Subtracting camera to get screen bullet position from world bullet position.
            bullet_screen_rect.y -= camera_draw_y
            screen.blit(bullet.image, bullet_screen_rect)
    #--------------------

    #--------------------
        #Crosshair
        mouse_pos = pygame.mouse.get_pos()
        custom_crosshair_rect = custom_crosshair.get_rect(center=mouse_pos)

        if game_state == "playing":
            screen.blit(custom_crosshair, custom_crosshair_rect)
        # pygame.draw.rect(screen, (255, 0, 0), player.hitbox, 2)  #Draw the hitbox for debugging
    
#--------------------

#--------------------
    #GAME STATE
    #UPDATE
    if game_state == "playing":
        player_group.update(wall_group)
        enemy_group.update(player, wall_group, bullet_group)
        bullet_group.update(wall_group, enemy_group, player)

        if player.health <= 0:
            game_state = "gameover"
        elif len(enemy_group) == 0:
            game_state = "victory"

    #DRAW
    if game_state == "menu":
        screen.fill("#1E1C1C")

        for surface, rect in title_letters:
            screen.blit(surface,rect)

        play_button.draw(screen, bodyfont)
        settings_button.draw(screen, bodyfont)
        quit_button_1.draw(screen, bodyfont)

    elif game_state == "playing":
        draw_game()

    elif game_state == "paused":
        draw_game()

        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        screen.blit(overlay, (0, 0))

        for surface, rect in paused_menu_letters:
            screen.blit(surface,rect)

        resume_button.draw(screen, pausedbodyfont)
        settings_button_paused.draw(screen, pausedbodyfont)
        restart_button_paused.draw(screen, pausedbodyfont)
        menu_button_paused.draw(screen, pausedbodyfont)
        quit_button_paused.draw(screen, pausedbodyfont)

    elif game_state == "settings":
        screen.fill("#1E1C1C")
        pygame_widgets.update(events)
        sfx_volume = sfx_slider.getValue()
        music_volume = music_slider.getValue()

        pygame.mixer.music.set_volume(music_volume / 100)
        gunshot_sound.set_volume(sfx_volume / 100)
        gunshot_sound_enemy.set_volume(sfx_volume / 100)

        for surface, rect in settings_menu_letters:
            screen.blit(surface,rect)

        menu_button_settings.draw(screen, pausedbodyfont)

        if settings_from == "paused":
            resume_button_settings.draw(screen, pausedbodyfont)

        screen.blit(music_volume_text, (75, 200))
        screen.blit(sfx_volume_text, (75, 325))

    elif game_state == "victory":
        screen.fill("#1E1C1C")

        victory_text = titlefont.render("YOU WIN!", True, "#00bd10")
        victory_rect = victory_text.get_rect(center=(screen.get_width() // 2, screen.get_height() // 4))
        screen.blit(victory_text, victory_rect)

        menu_button.draw(screen, bodyfont)
        quit_button_2.draw(screen, bodyfont)
        next_level_button.draw(screen, bodyfont)

    elif game_state == "gameover":
        screen.fill("#1E1C1C")

        for surface, rect in gameover_letters:
            screen.blit(surface,rect)

        restart_button.draw(screen, bodyfont)
        menu_button.draw(screen, bodyfont)
        quit_button_2.draw(screen, bodyfont)
#--------------------
    pygame.display.update()
    clock.tick(60)