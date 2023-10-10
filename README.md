![image](https://github.com/geduardo/WEDM-minimal-simulation/assets/48300381/042f8ab7-87b2-430e-9d5a-143c95bf69e3)

# Wire EDM Gymnasium environments


This repository contains a Python package that implements a simplified stochastic simulation of a 1D Wire Electrical Discharge Machining (Wire EDM) process.

Designed for compatibility with the [Gymnasium](https://gymnasium.farama.org/) library—formerly known as OpenAI Gym—this package facilitates the efficient testing of existing reinforcement learning algorithms and various control strategies specific to the Wire EDM process.

Additionally, the package provides a basic visualization feature using `pygame`, in line with common practices in other Gymnasium environments.

## Installation

Requirements:

- Python 3.10 (it may work with other versions, but it has not been tested. Pygame sometimes has issues with Python versions)
- Latest version of [pip](https://pip.pypa.io/en/stable/installing/)
- [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)

1. Clone this repository to your local machine:

    ```bash
    git clone https://github.com/geduardo/WEDM-minimal-simulation
    cd WEDM-minimal-simulation
    ```

2. Optionally, create a virtual environment for the project:

    ```bash
    python -m venv myvenv
    source myvenv/bin/activate
    ```

3. Install the package using `pip`:

    ```bash
    pip install -e edm_environments
    ```

After you have installed the package, you can create an instance of the environment via the `gym.make()` function:

```python
import edm_environments
import gymnasium as gym
env = gym.make('edm_environments/WireEDM-v0', render_mode='human')
```

To test that the installation was successful, you can run the following script:

```python
import edm_environments
import gymnasium as gym
env = gym.make('edm_environments/WireEDM-v0', render_mode='human', fps=60)
observation, info = env.reset()
for _ in range(1000):
    action = env.action_space.sample()  # agent policy that uses the observation and info
    observation, reward, terminated, truncated, info = env.step(action)

    if terminated or truncated:
        observation, info = env.reset()

env.close()
```

This should open a window with a visualization of the simulation with a duration of 1000 random motor actions.

## License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE.md) file for details.
