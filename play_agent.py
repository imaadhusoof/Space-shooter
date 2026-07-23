# Watch the trained agent play, rendered with the real game sprites.
# Run with:  py -3.13 play_agent.py

import numpy as np
import pygame
import tensorflow as tf
from sys import exit

from space_env import SpaceShooterEnv, SCREEN_W, SCREEN_H

MODEL_PATH = "dqn_space_shooter.keras"

pygame.init()
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("DQN agent")
clock = pygame.time.Clock()

background_surf = pygame.image.load("Images/background_inf_1.png").convert()
background_top = -2400
player_surf = pygame.image.load("Images/character_fit.png").convert_alpha()
asteroid_small = pygame.image.load("Images/asteroid_cracked_1.png").convert_alpha()
laser = pygame.image.load("Images/laser.png").convert_alpha()
try:
    font_obj = pygame.font.Font("font/Pixeltype.ttf", 50)
except FileNotFoundError:
    font_obj = pygame.font.Font(None, 50)

model = tf.keras.models.load_model(MODEL_PATH)
env = SpaceShooterEnv()
obs = env.reset()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

    q = model(obs[np.newaxis], training=False)[0]
    action = int(np.argmax(q))
    obs, reward, done = env.step(action)

    background_top = background_top + 20
    if background_top == -1200:
        background_top = -2400
    screen.blit(background_surf, (0, background_top))

    screen.blit(player_surf, env.player_rect)
    if env.laser_active:
        screen.blit(laser, env.laser_rect)
    for asteroid in env.asteroids:
        screen.blit(asteroid_small, asteroid)

    kills_font = font_obj.render(f"kills:{env.kills}", False, "White")
    screen.blit(kills_font, kills_font.get_rect(midbottom=(100, 300)))
    score_font = font_obj.render(str(env.frames // 60), False, "White")
    screen.blit(score_font, score_font.get_rect(midbottom=(100, 100)))

    if done:
        obs = env.reset()

    clock.tick(60)
    pygame.display.update()
