# Headless version of the space shooter for reinforcement learning.
# Mirrors the numbers and collision rules from "space shooter woo.py"
# (asteroid phase only - the agent's goal is breaking asteroids + surviving).

import random
import pygame
import numpy as np

SCREEN_W = 1200
SCREEN_H = 800
PLAYER_SIZE = (200, 200)        # character_fit.png
ASTEROID_SIZE = (130, 130)      # asteroid_cracked_1.png
LASER_SIZE = (97, 121)          # laser.png
PLAYER_SPEED = 15
ASTEROID_SPEED = 6
LASER_SPEED = 30
SPAWN_EVERY = 30                # frames; the game spawns every 500ms at 60fps
MAX_ASTEROIDS_SEEN = 5          # how many nearest asteroids the agent can see
MAX_STEPS = 1800                # 30 seconds per episode at 60fps


class SpaceShooterEnv:
    # actions: 0 = stay, 1 = left, 2 = right, 3 = shoot
    n_actions = 4
    obs_size = 4 + 3 * MAX_ASTEROIDS_SEEN

    def reset(self):
        self.player_rect = pygame.Rect(0, 0, *PLAYER_SIZE)
        self.player_rect.midbottom = (600, SCREEN_H)
        self.laser_rect = pygame.Rect(0, 0, *LASER_SIZE)
        self.laser_active = False
        self.asteroids = []
        self.frames = 0
        self.kills = 0
        return self.observe()

    def step(self, action):
        reward = 0.01           # small bonus for staying alive
        done = False

        # player movement (clamped to the screen like the wall bounce)
        if action == 1:
            self.player_rect.left = max(0, self.player_rect.left - PLAYER_SPEED)
        elif action == 2:
            self.player_rect.right = min(SCREEN_W, self.player_rect.right + PLAYER_SPEED)
        elif action == 3 and not self.laser_active:
            self.laser_active = True
            self.laser_rect.midbottom = self.player_rect.midtop

        # laser flies up, same reset rule as the game (top < -200)
        if self.laser_active:
            self.laser_rect.top = self.laser_rect.top - LASER_SPEED
            if self.laser_rect.top < -200:
                self.laser_active = False

        # spawn asteroids on the same schedule as the game
        self.frames += 1
        if self.frames % SPAWN_EVERY == 0:
            asteroid = pygame.Rect(0, 0, *ASTEROID_SIZE)
            asteroid.midbottom = (random.randrange(0, SCREEN_W), 0)
            self.asteroids.append(asteroid)

        # asteroids fall; same collision rules as the game
        for asteroid in self.asteroids[:]:
            asteroid.bottom = asteroid.bottom + ASTEROID_SPEED
            if self.laser_active and self.laser_rect.collidepoint(asteroid.midbottom):
                self.asteroids.remove(asteroid)
                self.kills += 1
                reward += 1.0
                continue
            if self.player_rect.colliderect(asteroid):
                reward = -5.0
                done = True
            elif asteroid.top > SCREEN_H:
                self.asteroids.remove(asteroid)

        if self.frames >= MAX_STEPS:
            done = True

        return self.observe(), reward, done

    def observe(self):
        obs = np.zeros(self.obs_size, dtype=np.float32)
        obs[0] = self.player_rect.centerx / SCREEN_W
        obs[1] = 1.0 if self.laser_active else 0.0
        if self.laser_active:
            obs[2] = self.laser_rect.centerx / SCREEN_W
            obs[3] = self.laser_rect.bottom / SCREEN_H
        # the lowest (most dangerous) asteroids first
        nearest = sorted(self.asteroids, key=lambda a: -a.bottom)[:MAX_ASTEROIDS_SEEN]
        for slot, asteroid in enumerate(nearest):
            base = 4 + slot * 3
            obs[base] = 1.0
            obs[base + 1] = (asteroid.centerx - self.player_rect.centerx) / SCREEN_W
            obs[base + 2] = asteroid.bottom / SCREEN_H
        return obs
