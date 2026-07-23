# DQN training for the space shooter agent.
# Run with:  py -3.13 train_agent.py
# Saves the network to dqn_space_shooter.keras every 25 episodes.

import random
from collections import deque

import numpy as np
import tensorflow as tf

from space_env import SpaceShooterEnv

EPISODES = 400
GAMMA = 0.99
BATCH_SIZE = 64
BUFFER_SIZE = 100_000
WARMUP_STEPS = 1_000            # random steps before learning starts
TRAIN_EVERY = 4                 # learn every N env steps
TARGET_UPDATE_EVERY = 1_000     # steps between target-network syncs
EPSILON_START = 1.0
EPSILON_END = 0.05
EPSILON_DECAY_STEPS = 50_000
LEARNING_RATE = 1e-3
MODEL_PATH = "dqn_space_shooter.keras"


def build_model():
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(SpaceShooterEnv.obs_size,)),
        tf.keras.layers.Dense(128, activation="relu"),
        tf.keras.layers.Dense(128, activation="relu"),
        tf.keras.layers.Dense(SpaceShooterEnv.n_actions),
    ])
    return model


def main():
    env = SpaceShooterEnv()
    model = build_model()
    target_model = build_model()
    target_model.set_weights(model.get_weights())
    optimizer = tf.keras.optimizers.Adam(LEARNING_RATE)
    buffer = deque(maxlen=BUFFER_SIZE)
    total_steps = 0

    @tf.function
    def train_step(states, actions, rewards, next_states, dones):
        next_q = tf.reduce_max(target_model(next_states), axis=1)
        targets = rewards + GAMMA * next_q * (1.0 - dones)
        with tf.GradientTape() as tape:
            q_values = model(states)
            action_q = tf.reduce_sum(
                q_values * tf.one_hot(actions, SpaceShooterEnv.n_actions), axis=1)
            loss = tf.keras.losses.huber(targets, action_q)
        grads = tape.gradient(loss, model.trainable_variables)
        optimizer.apply_gradients(zip(grads, model.trainable_variables))
        return loss

    for episode in range(1, EPISODES + 1):
        obs = env.reset()
        episode_reward = 0.0
        done = False

        while not done:
            epsilon = max(EPSILON_END,
                          EPSILON_START - total_steps / EPSILON_DECAY_STEPS)
            if total_steps < WARMUP_STEPS or random.random() < epsilon:
                action = random.randrange(SpaceShooterEnv.n_actions)
            else:
                q = model(obs[np.newaxis], training=False)[0]
                action = int(np.argmax(q))

            next_obs, reward, done = env.step(action)
            buffer.append((obs, action, reward, next_obs, float(done)))
            obs = next_obs
            episode_reward += reward
            total_steps += 1

            if total_steps >= WARMUP_STEPS and total_steps % TRAIN_EVERY == 0:
                batch = random.sample(buffer, BATCH_SIZE)
                states, actions, rewards, next_states, dones = map(np.array, zip(*batch))
                train_step(states.astype(np.float32),
                           actions.astype(np.int32),
                           rewards.astype(np.float32),
                           next_states.astype(np.float32),
                           dones.astype(np.float32))

            if total_steps % TARGET_UPDATE_EVERY == 0:
                target_model.set_weights(model.get_weights())

        print(f"episode {episode:4d}  reward {episode_reward:7.2f}  "
              f"kills {env.kills:3d}  survived {env.frames:4d} frames  "
              f"epsilon {epsilon:.2f}")

        if episode % 25 == 0:
            model.save(MODEL_PATH)
            print(f"  saved model to {MODEL_PATH}")

    model.save(MODEL_PATH)
    print(f"done - final model saved to {MODEL_PATH}")


if __name__ == "__main__":
    main()
