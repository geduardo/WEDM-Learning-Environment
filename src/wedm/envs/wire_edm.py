# src/edm_env/envs/wire_edm.py
from __future__ import annotations

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from ..core.state import EDMState
from ..modules.dielectric import DielectricModule
from ..modules.ignition import IgnitionModule
from ..modules.material import MaterialRemovalModule
from ..modules.mechanics import MechanicsModule
from ..modules.wire import WireModule


class WireEDMEnv(gym.Env):
    """Main-cut Wire-EDM environment (1 µs base-step, 1 ms control-step)."""

    metadata = {"render_modes": ["human"], "render_fps": 300}

    def __init__(self, *, render_mode: str | None = None):
        super().__init__()
        self.render_mode = render_mode

        # ── sim parameters ───────────────────────────────────────────
        self.dt = 1                # µs
        self.servo_interval = 1_000

        # workpiece / wire constants
        self.workpiece_height = 10.0     # mm
        self.wire_diameter = 0.25        # mm

        # RNG
        self.np_random = np.random.default_rng()

        # global state
        self.state = EDMState()

        # modules
        self.ignition = IgnitionModule(self)
        self.material = MaterialRemovalModule(self)
        self.dielectric = DielectricModule(self)
        self.wire = WireModule(self)
        self.mechanics = MechanicsModule(self)

        # ── action space ─────────────────────────────────────────────
        self.action_space = spaces.Dict(
            {
                "servo": spaces.Box(low=-1.0, high=1.0, shape=(1,), dtype=np.float32),
                "generator_control": spaces.Dict(
                    {
                        "target_voltage": spaces.Box(0.0, 200.0, (1,), np.float32),
                        "peak_current": spaces.Box(0.0, 100.0, (1,), np.float32),
                        "ON_time": spaces.Box(0.0, 5.0, (1,), np.float32),
                        "OFF_time": spaces.Box(0.0, 100.0, (1,), np.float32),
                    }
                ),
            }
        )

        # observation space placeholder (define as needed)
        self.observation_space = spaces.Dict({})

    # --------------------------------------------------------------------- #
    # Gym API
    # --------------------------------------------------------------------- #
    def reset(self, *, seed: int | None = None, options=None):
        super().reset(seed=seed)
        self.state = EDMState()
        return self._get_obs(), {}

    def step(self, action):
        is_ctrl_step = self.state.time_since_servo >= self.servo_interval

        if is_ctrl_step:
            self._apply_action(action)
            self.state.time_since_servo = 0

        # physics advance 1 µs
        self.ignition.update(self.state)
        self.material.update(self.state)
        self.dielectric.update(self.state)
        self.wire.update(self.state)

        if self.state.is_wire_broken:
            return None, 0.0, True, False, {"wire_broken": True}

        self.mechanics.update(self.state)

        # time bookkeeping
        self.state.time += self.dt
        self.state.time_since_servo += self.dt
        self.state.time_since_open_voltage += self.dt

        if self.state.spark_status[0] == 1:
            self.state.time_since_spark_ignition += self.dt
            self.state.time_since_spark_end = 0
        else:
            self.state.time_since_spark_end += self.dt
            self.state.time_since_spark_ignition = 0

        terminated = self._check_termination()
        obs = self._get_obs() if is_ctrl_step else None
        reward = self._calc_reward() if is_ctrl_step else 0.0

        info = {
            "wire_broken": self.state.is_wire_broken,
            "target_reached": self.state.is_target_distance_reached,
            "spark_state": int(self.state.spark_status[0]),
            "time": self.state.time,
            "control_step": is_ctrl_step,
        }
        return obs, reward, terminated, False, info

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _apply_action(self, action):
        self.state.target_delta = float(action["servo"][0])
        gc = action["generator_control"]
        self.state.target_voltage = float(gc["target_voltage"][0])
        self.state.peak_current = float(gc["peak_current"][0])
        self.state.ON_time = float(gc["ON_time"][0])
        self.state.OFF_time = float(gc["OFF_time"][0])

    def _check_termination(self) -> bool:
        if self.state.wire_position > self.state.workpiece_position + 100:
            self.state.is_wire_broken = True
            return True
        if self.state.workpiece_position >= self.state.target_position:
            self.state.is_target_distance_reached = True
            return True
        return False

    def _get_obs(self):
        # TODO: design vector/Dict obs
        return {}

    def _calc_reward(self):
        # TODO: implement proper reward
        return 0.0
