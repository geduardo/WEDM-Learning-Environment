# src/edm_env/modules/mechanics.py
from __future__ import annotations

from ..core.module import EDMModule
from ..core.state import EDMState


class MechanicsModule(EDMModule):
    """Optimized servo axis with configurable position or velocity control modes."""

    def __init__(self, env, control_mode: str = "position"):
        super().__init__(env)

        # Validate control mode
        if control_mode not in ["position", "velocity"]:
            raise ValueError(
                f"control_mode must be 'position' or 'velocity', got {control_mode}"
            )

        self.control_mode = control_mode

        # Pre-compute constants for performance
        self.dt = env.dt * 1e-6  # Pre-compute dt
        self.omega_n = 200.0  # rad s⁻¹
        self.zeta = 0.55  # damping ratio (only used for position control)
        self.max_accel = 3.0e5  # [µm s⁻²]
        self.max_jerk = 1.0e8  # [µm s⁻³]
        self.max_speed = 3.0e4  # [µm s⁻¹]

        # Pre-compute control law constants
        if self.control_mode == "position":
            self.damping_coeff = -2.0 * self.zeta * self.omega_n  # -220.0
            self.stiffness_coeff = -(self.omega_n**2)  # -40000.0

        # Pre-compute jerk limiting
        self.max_jerk_dt = self.max_jerk * self.dt  # Pre-compute for performance

        self.prev_accel = 0.0

        # Method dispatch: set up control law computation during init
        if self.control_mode  == "position":
            self._compute_nominal_accel = self._compute_position_accel
        else:  # velocity
            self._compute_nominal_accel = self._compute_velocity_accel

    def _compute_position_accel(self, state: EDMState, x: float, v: float) -> float:
        """Optimized position control using pre-computed coefficients."""
        x_error = x - (x + state.target_delta)  # x - x_target
        return self.damping_coeff * v + self.stiffness_coeff * x_error

    def _compute_velocity_accel(self, state: EDMState, x: float, v: float) -> float:
        """Optimized velocity control."""
        v_error = v - state.target_delta
        return -self.omega_n * v_error

    def update(self, state: EDMState) -> None:
        x = state.wire_position
        v = state.wire_velocity

        # Compute nominal acceleration using dispatched method
        a_nom = self._compute_nominal_accel(state, x, v)

        # Scalar clipping (faster than numpy for single values)
        if a_nom > self.max_accel:
            a_nom = self.max_accel
        elif a_nom < -self.max_accel:
            a_nom = -self.max_accel

        # Jerk limiting with scalar operations
        da = a_nom - self.prev_accel
        if da > self.max_jerk_dt:
            da = self.max_jerk_dt
        elif da < -self.max_jerk_dt:
            da = -self.max_jerk_dt

        a = self.prev_accel + da
        self.prev_accel = a

        # Update velocity with scalar clipping
        v += a * self.dt
        if v > self.max_speed:
            v = self.max_speed
        elif v < -self.max_speed:
            v = -self.max_speed

        # Update position
        x += v * self.dt

        # Update state
        state.wire_velocity = v
        state.wire_position = x
