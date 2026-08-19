import pygame
import random
from sys import exit


pygame.init()
screen = pygame.display.set_mode((1200,800))
clock = pygame.time.Clock()
i = 0

health_bar_surf = pygame.image.load("Images/health_bar_3_1.png").convert()
health_bar_surf_rect =health_bar_surf.get_rect(midbottom = (900,50))

boss_surf = pygame.image.load("Images/boss_1.png").convert_alpha()
boss_rect = boss_surf.get_rect(midbottom = ( 600,200))
boss_surf_hurt = pygame.image.load("Images/boss_1_hit.png").convert_alpha()

background_surf = pygame.image.load("Images/background_inf_1.png").convert()
background_rect = background_surf.get_rect(topleft=(0,-2400))

player_surf = pygame.image.load("Images/character_fit.png").convert_alpha()
player_rect =player_surf.get_rect(midbottom= (600,800))

asteroid_surf = pygame.image.load("Images/asteroid.png").convert_alpha()
asteroid_rect = asteroid_surf.get_rect(midbottom=(600,200))

asteroid_small = pygame.image.load("Images/asteroid_cracked_1.png").convert_alpha()
asteroid_small_rect = asteroid_small.get_rect(midbottom=(200,200))

laser = pygame.image.load("Images/laser.png").convert_alpha()
boss_laser_rect = laser.get_rect(midtop = boss_rect.midtop)


shield_surf = pygame.image.load("Images/shield.png").convert_alpha()
shield_surf = pygame.transform.smoothscale(shield_surf, (240, 240))
shield_count = 1              # player starts with one shield charge
shield_active = False
shield_duration = 3000        # ms of immunity once activated
shield_end_time = 0

try:
    font_obj = pygame.font.Font("font/Pixeltype.ttf", 50)
except FileNotFoundError:
    font_obj = pygame.font.Font(None, 50)
game_over_font = font_obj.render("GAME OVER", False, "Black")
game_over_font_rect = game_over_font.get_rect(midbottom=(600,400))
kills = 0
kills_font = font_obj.render(f"kills:{kills}", False, "White")
kills_font_rect = kills_font.get_rect(midbottom=(100,300))

# Shield counter sits directly under the health bar, same font/style as the kills counter
shield_font_rect = font_obj.render(f"shields:{shield_count}", False, "White").get_rect(midbottom=(100,350))

obstacle_event = pygame.USEREVENT + 1
pygame.time.set_timer(obstacle_event, 700)

explosion_timer = pygame.USEREVENT + 2
delta_horizontal = 0

# ---- Player laser list (replaces the old single laser_rect / truth flag) ----
player_lasers = []
laser_speed = 60
laser_cooldown = 150          # ms between shots, lower = faster spam
last_laser_time = 0

boss_timer = pygame.USEREVENT + 3
pygame.time.set_timer(boss_timer,1000)

boss_laser = pygame.USEREVENT + 4
pygame.time.set_timer(boss_laser, 2500)

def Movement():
    global player_rect, delta_horizontal
    player_rect.left = player_rect.left + delta_horizontal
    if player_rect.right >=1200:
        delta_horizontal = delta_horizontal * -1
    elif player_rect.left <=0:
        delta_horizontal = delta_horizontal * -1


def FireLaser():
    """Spawns a new laser at the player's position and adds it to the list."""
    global player_lasers, last_laser_time
    now = pygame.time.get_ticks()
    if now - last_laser_time >= laser_cooldown:
        new_laser = laser.get_rect(midbottom = player_rect.midtop)
        player_lasers.append(new_laser)
        last_laser_time = now


def MoveAndDrawPlayerLasers():
    """Moves every laser in the list up the screen, draws it, and removes it once off-screen."""
    global player_lasers
    for player_laser in player_lasers:
        player_laser.top -= laser_speed
        screen.blit(laser, player_laser)
    player_lasers = [pl for pl in player_lasers if pl.bottom > -50]


def ActivateShield():
    """Spends one shield charge to grant temporary immunity, if the player has one and isn't already shielded."""
    global shield_count, shield_active, shield_end_time
    if shield_count > 0 and not shield_active:
        shield_count -= 1
        shield_active = True
        shield_end_time = pygame.time.get_ticks() + shield_duration


def UpdateShield():
    """Turns the shield off once its duration expires, and draws the overlay while active."""
    global shield_active
    if shield_active:
        if pygame.time.get_ticks() >= shield_end_time:
            shield_active = False
        else:
            shield_rect = shield_surf.get_rect(center = player_rect.center)
            screen.blit(shield_surf, shield_rect)


obstacle_list=[]
game_state = True

def AsteroidSpawn():
    global obstacle_list, player_lasers, game_state, kills, kills_font, explosion_timer, x, y, boss_state, shield_count
    if obstacle_list:
        for count in range(len(obstacle_list) - 1, -1, -1):
            obstacle_list[count].bottom = obstacle_list[count].bottom + 6
            screen.blit(asteroid_small,obstacle_list[count])

            hit_laser = None
            for player_laser in player_lasers:
                if player_laser.colliderect(obstacle_list[count]):
                    hit_laser = player_laser
                    break

            if hit_laser is not None:
                x, y ,w ,w2 = obstacle_list[count]
                del obstacle_list[count]
                player_lasers.remove(hit_laser)
                pygame.time.set_timer(explosion_timer, 50)
                kills = kills + 1
                if kills % 10 == 0:
                    boss_state = True
                    boss_rect.midbottom = (600, 200)
                    shield_count += 1
                continue

            if player_rect.colliderect(obstacle_list[count]) and not shield_active:
                game_state =  False
game_reset_time = 0

def Score():
    global score
    score = (pygame.time.get_ticks() - game_reset_time) //1000
    score_font =font_obj.render(str(score), False,"White")
    score_font_rect = score_font.get_rect(midbottom=(100,100))
    screen.blit(score_font,score_font_rect)
explosion_state = False

boss_horizontal = 16
boss_state = False
boss_laser_state = False
boss_hp_max = 15
boss_hp = boss_hp_max
boss_hurt_frames = 0
boss_laser_speed = 18
def Boss():
    global kills, boss_horizontal, boss_timer, boss_rect, boss_laser_state
    global boss_hp, boss_state, boss_hurt_frames, player_lasers, game_state, x, y
    # spawn the boss, spawn the health bar have it move around randomly, have it shoot lasers randomly,
    # have it turn red when damage, reduce hp when damaged
    boss_rect.left = boss_rect.left + boss_horizontal
    if boss_rect.right >= 1200:
        boss_horizontal = boss_horizontal * -1
    elif boss_rect.left <= 0:
        boss_horizontal = boss_horizontal * -1

    hit_laser = None
    for player_laser in player_lasers:
        if player_laser.colliderect(boss_rect):
            hit_laser = player_laser
            break

    if hit_laser is not None:
        boss_hp = boss_hp - 1
        boss_hurt_frames = 8
        player_lasers.remove(hit_laser)
        if boss_hp <= 0:
            boss_state = False
            boss_laser_state = False
            x, y = boss_rect.left, boss_rect.top
            pygame.time.set_timer(explosion_timer, 50)
            boss_rect.midbottom = (600, 200)
            boss_hp = boss_hp_max
            return

    if boss_hurt_frames > 0:
        screen.blit(boss_surf_hurt, boss_rect)
        boss_hurt_frames = boss_hurt_frames - 1
    else:
        screen.blit(boss_surf, boss_rect)

    if boss_laser_state:
        screen.blit(laser, boss_laser_rect)
        boss_laser_rect.top = boss_laser_rect.top + boss_laser_speed
        if player_rect.colliderect(boss_laser_rect) and not shield_active:
            game_state = False
        if boss_laser_rect.top > 800:
            boss_laser_state = False

    hp_width = int(health_bar_surf.get_width() * boss_hp / boss_hp_max)
    screen.blit(health_bar_surf, health_bar_surf_rect, (0, 0, hp_width, health_bar_surf.get_height()))


while True:
    for event in pygame.event.get():
        if event.type ==pygame.QUIT:
            pygame.quit()
            exit()

        if event.type == pygame.KEYDOWN:
            if event.key ==pygame.K_RIGHT:
                delta_horizontal = 15
            if event.key ==pygame.K_LEFT:
                delta_horizontal = -15
            if event.key ==pygame.K_s:
                ActivateShield()
        if event.type == obstacle_event:
            if boss_state == False:
                obstacle_list.append(asteroid_small.get_rect(midbottom=(random.randrange(0,1200),0)))
        if event.type == explosion_timer:
            explosion_state= True
        if event.type == boss_timer:
            random_direction = random.randrange(0, 2)
            if random_direction == 1:
                boss_horizontal = 10
            else:
                boss_horizontal = -10
        if event.type == boss_laser and boss_state:
            if boss_laser_state == False:
                boss_laser_state = True
                boss_laser_rect.midtop = boss_rect.midbottom
            pygame.time.set_timer(boss_laser, random.randrange(1000, 1900))




    if game_state:

        background_rect.top = background_rect.top +20
        if background_rect.top ==-1200:
            background_rect.top=-2400
        screen.blit(background_surf, background_rect)

        Score()
        Movement()
        screen.blit(player_surf,player_rect)
        #screen.blit(asteroid_surf,asteroid_rect)

        # Holding space fires continuously, gated by laser_cooldown so it doesn't spam every single frame
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            FireLaser()

        MoveAndDrawPlayerLasers()
        UpdateShield()

        if boss_state == False: AsteroidSpawn()
        kills_font = font_obj.render(f"kills:{kills}", False, "White")

        screen.blit(kills_font,kills_font_rect)

        shield_font = font_obj.render(f"shields:{shield_count}", False, "White")
        screen.blit(shield_font, shield_font_rect)

        if boss_state:
            Boss()
        if explosion_state:
            explosion = pygame.image.load("Images/explosion" + str(i + 1) + ".png")
            screen.blit(explosion, (x, y))
            print(i)
            i = i + 1
            if i == 7:
                i = 0
                pygame.time.set_timer(explosion_timer, 40000000)
            explosion_state = False
    else:
        screen.fill("White")
        kills = 0
        game_reset_time = pygame.time.get_ticks()
        screen.blit(game_over_font,game_over_font_rect)
        game_over_score = font_obj.render(f"{score}", False,"Black")
        game_over_score_rect = game_over_score.get_rect(midbottom=(600,100))
        screen.blit(game_over_score,game_over_score_rect)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            score = 0
            game_state = True
            obstacle_list.clear()
            player_rect.midbottom=(600,800)
            boss_state = False
            boss_hp = boss_hp_max
            boss_rect.midbottom = (600, 200)
            boss_laser_state = False
            player_lasers.clear()
            shield_count = 1
            shield_active = False

    clock.tick(60)
    pygame.display.update()