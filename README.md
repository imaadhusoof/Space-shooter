# Space Shooter

A vertical-scrolling space shooter I made in pygame. It also has a reinforcement learning agent, a Deep Q-Network (DQN) built in TensorFlow, that learns to play it. You can play the game in your browser at [imaadhusoof.com](https://imaadhusoof.com).

## The game

You fly a ship along the bottom of the screen and shoot asteroids that fall from the top. Asteroids spawn every 700 ms at random positions and fall at a steady speed. If one hits you, it's game over. Your score is how many seconds you survive, and kills are tracked separately.

The ship doesn't stop moving. The arrow keys set its direction, and it bounces off the edges of the screen. Holding space fires continuously, with a 150 ms cooldown between shots, and each laser is tracked in a list so several can be on screen at once.

Every 10 kills a boss spawns and the asteroids stop. The boss moves side to side across the screen, flashes red when you hit it, and fires lasers down at you at random intervals of 1 to 1.9 seconds. It has 15 HP, shown by a health bar at the top of the screen.

You start with one shield charge and get another each time a boss appears. Pressing S uses a charge and makes you immune to everything for 3 seconds.

**Controls:** left and right arrows to steer, hold space to shoot, S for a shield, and space to restart after a game over.

For the browser version, I compiled the game to WebAssembly with pygbag. The browser version of pygame doesn't support `pygame.time.set_timer()`, so that build checks elapsed time with `pygame.time.get_ticks()` every frame instead, and runs the main loop as an async function.

## The DQN agent

`space_env.py` is a headless version of the game for training. It uses the same screen size, speeds, sprite hitboxes and collision rules as the real game, but only covers the asteroid phase (no boss or shield) and allows one laser at a time. Each episode is capped at 1,800 frames, which is 30 seconds at 60 fps.

- **Actions:** stay, move left, move right, or shoot.
- **Observation:** 19 values. These are the player's x position, whether a laser is active, and the laser's position, plus the five lowest asteroids. For each asteroid it gets a presence flag, its horizontal distance from the player and its height, all normalised to the screen size.
- **Rewards:** +0.01 for every frame survived, +1 for each asteroid destroyed, and −5 for getting hit, which also ends the episode.

`train_agent.py` trains the DQN. The network has two hidden layers of 128 units with ReLU, and outputs one Q-value per action. It uses:

- a replay buffer of 100k transitions, with batches of 64
- a separate target network, synced every 1,000 steps
- Huber loss with the Adam optimiser (learning rate 1e-3) and a discount factor of 0.99
- ε-greedy exploration, with ε decaying linearly from 1.0 to 0.05 over 50k steps after 1,000 random warm-up steps

The agent trains every 4 environment steps, for 400 episodes, and saves a checkpoint every 25 episodes.

`play_agent.py` loads the trained model (`dqn_space_shooter.keras`, included in the repo) and shows it playing with the real game sprites.

## Running it

```
pip install -r requirements.txt
python "space shooter woo.py"
```

To train the agent yourself or watch the included model play:

```
python train_agent.py
python play_agent.py
```
