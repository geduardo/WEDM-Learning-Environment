import numpy as np
import gymnasium as gym
from gymnasium import spaces
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
import numpy as np
import time


crater_dtype = np.dtype([
('radius', 'f4'),          # float32 for crater radius
('y_position', 'f4'),      # float32 for y-axis position
('time_formed', 'i4'),     # int32 for timestamp
('depth', 'f4'),           # float32 for crater depth
])
    
@dataclass
class EDMState:
    # Time tracking
    time: int = 0 # Current time from start of simulation
    time_since_servo: int = 0 # Time since last servo action
    time_since_open_voltage: int = 0  # Time since last voltage was applied
    time_since_spark_ignition: int = 0 # Time since last spark was ignited
    time_since_spark_end: int = 0 # Time since last spark ended
    
    
    # Electrical state variables
    voltage: Optional[float] = None
    current: Optional[float] = None
    
    # Generator control state variables
    target_voltage: Optional[float] = None
    peak_current: Optional[float] = None
    OFF_time: Optional[float] = None
    ON_time: Optional[float] = None

    # Workpiece state variables
    
    workpiece_position: float = 0 # Current position of the workpiece
    
    # Wire state variables
    wire_position: float = 0.0 # Current position of the wire
    wire_velocity: float = 0.0 # Current velocity of the wire
    wire_unwinding_velocity = 0.2 # Unwinding velocity of the wire in micrometers per microsecond (microns/μs -- mm/ms .. m/s)
    wire_temperature: np.ndarray = field(default_factory=lambda: np.array([], dtype=np.float32))
    time_in_critical_temp: int = 0
    
    
    # Spark state variables
    
    # Tuple to track current spark status (state, y-location, duration)
    # state: 0=No event, 1=Spark formation, -1=Short circuit, -2=Rest period
    # y_location: Position along wire length where spark is occurring (None if no spark)
    # duration: How many timesteps the current spark state has existed
    
    spark_status: List[Optional[float]] = field(default_factory=lambda: [0, None, 0])

    
    # Dielectric state variables
    
    dielectric_conductivity: float = 0.0 # Conductivity of the dielectric
    dielectric_temperature: float = 0.0 # Temperature of the dielectric
    debris_concentration: float = 0.0 # Concentration of debris in the dielectric
    dielectric_flow_rate: float = 0.0 # Flow rate of the dielectric
    ionized_channel: Optional[Tuple[float, int]] = None # (y_location, time_remaining) or None
    
    # Servo state variables
    
    target_delta: float = 0.0 # Target change in position for the servo in the linear axis. This is the main servo control signal.
    
    # Process state
    is_wire_broken: bool = False
    is_wire_colliding: bool = False
    is_target_distance_reached: bool = False


class EDMModule:
    """Base class for all EDM simulation modules"""
    def __init__(self, env):
        self.env = env

    def update(self, state: EDMState) -> None:
        pass
    
class IgnitionModule(EDMModule):
    def __init__(self, env):
        super().__init__(env)
        self.lambda_cache = {}  # Cache for lambda values
        
    def update(self, state: EDMState) -> None:
        # Quick return for physical short circuit
        if state.wire_position >= state.workpiece_position:
            state.spark_status = [-1, None, 0]
            state.voltage = 0
            state.current = state.peak_current
            return

        # Cache frequently accessed values
        spark_state, spark_location, spark_duration = state.spark_status
        target_voltage = state.target_voltage
        peak_current = state.peak_current
        ON_time = state.ON_time if state.ON_time is not None else 3
        OFF_time = state.OFF_time if state.OFF_time is not None else 80
        
        # Handle active spark
        if spark_state == 1:
            spark_duration += 1
            if spark_duration >= ON_time:
                state.spark_status = [-2, None, 0]  # Start rest period
                state.current = state.voltage = 0
            else:
                state.spark_status = [1, spark_location, spark_duration]
                state.current = peak_current
                state.voltage = target_voltage * 0.3
            return
            
        # Handle rest period
        if spark_state == -2:
            spark_duration += 1
            if spark_duration >= OFF_time + ON_time:
                state.spark_status = [0, None, 0]
                state.voltage = target_voltage
                state.current = 0
            else:
                state.spark_status = [-2, None, spark_duration]
            return
            
        # Handle no spark condition
        if spark_state == 0:
            state.voltage = target_voltage
            state.current = 0
            
            if self.env.np_random.random() < self._get_lambda(state):
                spark_location = self.env.np_random.uniform(0, self.env.workpiece_height)
                state.spark_status = [1, spark_location, 0]
                state.voltage = target_voltage * 0.3
                state.current = peak_current
    
    def _get_lambda(self, state):
        gap_distance = abs(state.workpiece_position - state.wire_position)
        # Check cache first
        if gap_distance in self.lambda_cache:
            return self.lambda_cache[gap_distance]
        # Calculate new lambda value and cache it
        lambda_value = np.log(2)/(0.48*gap_distance*gap_distance - 3.69*gap_distance + 14.05)
        self.lambda_cache[gap_distance] = lambda_value
        
        return lambda_value

# Add other modules similarly
class MaterialRemovalModule(EDMModule):
    # TODO: Add crater formation and removal rate based on spark energy
    def update(self, state):
        # Only remove material if there is an active spark that just started
        if state.spark_status[0] == 1 and state.spark_status[2] == 0:
            # Remove a constant amount of material by moving the workpiece position
            # away from the wire by a small fixed increment
            removal_rate = 0.05  # mm per spark
            state.workpiece_position += removal_rate

class DielectricModule(EDMModule):
    def __init__(self, env):
        super().__init__(env)
        # Dielectric state variables
        self.dielectric_temp = 293.15  # Dielectric temperature in K
        self.debris_concentration = 0.0  # Debris concentration (0-1) 
        self.flow_rate = 1.0  # Normalized flow rate (0-1)
        self.ionized_channel = None  # (y_location, time_remaining) or None
        
        # Model parameters
        self.beta = 1e-3  # Debris concentration increase per mm^3 of crater volume
        self.gamma = 5e-4  # Base debris decay rate per microsecond at flow_rate=1
        self.tau_deionization = 6  # Deionization time in microseconds
        
    def update(self, state):
        # Update dielectric temperature
        state.dielectric_temperature = self.dielectric_temp
        
        # Handle debris concentration
        # Add debris if there was a spark that just started
        if state.spark_status[0] == 1 and state.spark_status[2] == 0:
            # Get crater volume from material removal module (placeholder value for now)
            crater_volume = 0.1  # mm^3
            self.debris_concentration = min(1.0, 
                self.debris_concentration + self.beta * crater_volume)
            
            # Create new ionized channel
            self.ionized_channel = (state.spark_status[1], self.tau_deionization)
            
        # Update ionized channel state
        if self.ionized_channel:
            y_loc, time_remaining = self.ionized_channel
            if time_remaining > 0:
                self.ionized_channel = (y_loc, time_remaining - 1)
            else:
                self.ionized_channel = None
                
        # Clear debris based on flow rate (exponential decay)
        self.debris_concentration *= (1 - self.gamma * self.flow_rate)
        self.debris_concentration = max(0.0, self.debris_concentration)
        
        # Update state variables
        state.debris_concentration = self.debris_concentration
        state.flow_rate = self.flow_rate
        state.ionized_channel = self.ionized_channel
        
        

class WireModule(EDMModule):
    def __init__(self, env):
        super().__init__(env)
        
        # Thermal model parameters
        self.segment_length = 0.2  # Fixed segment length (0.1 mm = 100 microns)
        self.wire_length = env.workpiece_height  # mm
        self.n_segments = int(self.wire_length / self.segment_length)  # Number of segments based on fixed length
        self.wire_radius = env.wire_diameter / 2  # mm
        
        # Initialize the wire temperature array with the correct number of segments
        if len(env.state.wire_temperature) == 0:  # Only initialize if not already set
            env.state.wire_temperature = np.full(self.n_segments, 293.15, dtype=np.float32)
        
        # Material properties (brass example)
        self.rho = 8400  # kg/m³ density
        self.cp = 377  # J/kg·K specific heat
        self.k = 120  # W/m·K thermal conductivity
        self.melting_point = 1180  # K (907°C)
        self.rho_electrical = 6.4e-8  # Ohm·m at 20°C
        self.alpha_resistivity = 0.0039  # Temperature coefficient
        
        # Heat transfer parameters
        self.h_convection = 3000  # W/m²K convection coefficient
        self.eta_plasma = 0.1  # Plasma energy transfer efficiency
        
        # Break detection parameters
        self.critical_temp = 100  # K - sustained temperature threshold
        self.critical_duration = 1e6  # μs (1s) at critical_temp
        
        # Precompute constant terms during initialization
        self.delta_y = self.segment_length * 1e-3  # Convert to meters once
        self.S_wire = np.pi * (self.wire_radius * 1e-3)**2  # Cross-sectional area
        self.A_wire = 2 * np.pi * (self.wire_radius * 1e-3) * self.delta_y  # Surface area
        self.conduction_coeff = (self.k * self.S_wire) / self.delta_y
        
        # Preallocate arrays for thermal calculations
        self.T_prev = np.empty(self.n_segments, dtype=np.float32)
        self.T_next = np.empty(self.n_segments, dtype=np.float32)
        self.q_plasma = np.zeros(self.n_segments, dtype=np.float32)
        self.q_joule = np.zeros(self.n_segments, dtype=np.float32)

        self.thermal_denominator = 1 / (self.rho * self.cp * self.S_wire * self.delta_y)
        self.convection_coeff_base = self.h_convection * self.A_wire
        self.transport_coeff = self.rho * self.cp * 1e-3 * self.S_wire / self.delta_y
        self.joule_const = (self.rho_electrical * self.delta_y) / (2 * self.S_wire)

    def update(self, state: EDMState) -> None:
        if state.is_wire_broken:
            return
        
        # Pre-fetch temperature array
        T = state.wire_temperature
        current = state.current if state.current is not None else 0.0
        
        # Boundary conditions
        T_prev = np.empty(self.n_segments, dtype=np.float32)
        T_prev[1:] = T[:-1]
        T_prev[0] = 293.15
        
        T_next = np.empty(self.n_segments, dtype=np.float32)
        T_next[:-1] = T[1:]
        T_next[-1] = 293.15

        # Plasma heating
        q_plasma = np.zeros(self.n_segments, dtype=np.float32)
        if state.spark_status[0] == 1 and state.spark_status[1] is not None:
            segment_idx = int(state.spark_status[1] // self.segment_length)
            if 0 <= segment_idx < len(T):
                q_plasma[segment_idx] = self.eta_plasma * state.voltage * current

        # Joule heating
        current_sq = current ** 2
        q_joule = current_sq * self.joule_const * (1 + self.alpha_resistivity * (T - 293.15))

        # Heat terms calculation
        h_effective = self.h_convection * (1 + 0.5 * state.wire_unwinding_velocity)
        
        dT_dt = (
            q_plasma + 
            q_joule +
            self.conduction_coeff * (T_prev - 2*T + T_next) -
            (h_effective * self.convection_coeff_base) * (T - state.dielectric_temperature) +
            self.transport_coeff * state.wire_unwinding_velocity * (T_next - T)
        ) * self.thermal_denominator

        # Temperature updates
        np.add(T, dT_dt * 1e-6, out=T)
        state.wire_average_temperature = (T[0] + T[-1] + 2*T[len(T)//2])/4  # 3-point approximation

class MechanicsModule(EDMModule):
    def update(self, state):
        # For the moment leave blank
        pass



class WireEDMEnv(gym.Env):    
    metadata = {"render_modes": ["human"], "render_fps": 300}
    
    def __init__(self, render_mode=None):
        self.render_mode = render_mode
        # Simulation parameters
        ## Internal timestep parameters
        self.dt = 1 # Base timestep (1μs)
        self.servo_interval = 1000 # Servo interval (1ms)
        
        ## Process configuration
        ### Workpiece physical properties
        self.workpiece_height = 10 # Height of workpiece (mm)
        self.workpiece_material = 'steel' # Material of workpiece
        #...
        
        ### Wire physical properties
        self.wire_material = 'brass'
        self.wire_diameter = 0.25 # Diameter of wire (mm)
        #...
        
        ### Dielectric physical properties
        self.dielectric_material = 'deionized water'
        
        self.state = EDMState() # Initialize state of the simulation
        
        self.ignition_module = IgnitionModule(self)
        self.material_removal_module = MaterialRemovalModule(self)
        self.dielectric_module = DielectricModule(self)
        self.wire_module = WireModule(self)
        self.mechanics_module = MechanicsModule(self)
        
        self.action_space = spaces.Dict({
            'servo': spaces.Box(
                low=np.array([-1.0]),
                high=np.array([1.0]),
                dtype=np.float32
            ),
            'generator_control': spaces.Dict({
                'target_voltage': spaces.Box(
                    low=np.array([0.0]),
                    high=np.array([200.0]),  # Placeholder max voltage
                    dtype=np.float32
                ),
                'peak_current': spaces.Box(
                    low=np.array([0.0]),
                    high=np.array([100.0]),  # Placeholder max current
                    dtype=np.float32
                ),
                 'ON_time': spaces.Box(
                    low=np.array([0.0]),
                    high=np.array([5.0]),  # Placeholder max on time
                    dtype=np.float32
                ),
                 'OFF_time': spaces.Box(
                    low=np.array([0.0]),
                    high=np.array([100.0]),  # Placeholder max off time
                    dtype=np.float32
                )
            })
        })
    
    def _check_termination(self):
        # Check for wire breakage
        if self.state.wire_position > self.workpiece_height:
            self.state.is_wire_broken = True
            return True
        
        # Check for target distance reached
        if self.state.workpiece_position >= self.state.target_delta:
            self.state.is_target_distance_reached = True
            return True
        
        return False
    
    def _get_obs(self):
        return None
        
    def _calculate_reward(self):
        return 0
    
    def step(self, action):
        # Track if this is a control step (every 1ms / 1000μs)
        is_control_step = self.state.time_since_servo >= self.servo_interval
        
        # Only process actions on control steps
        if is_control_step:
            self.state.target_delta = action['servo'][0]
            self.state.target_voltage = action['generator_control']['target_voltage'][0]
            self.state.peak_current = action['generator_control']['peak_current'][0]
            self.state.ON_time = action['generator_control']['ON_time'][0]  # Add these two lines
            self.state.OFF_time = action['generator_control']['OFF_time'][0]
            self.state.time_since_servo = 0  # Reset timer
        
        # Sequential process updates
        self.ignition_module.update(self.state)
        self.material_removal_module.update(self.state)
        self.dielectric_module.update(self.state)
        self.wire_module.update(self.state)
        if self.state.is_wire_broken:
            # If the wire is broken, return immediately
            return None, 0, True, False, {'wire_broken': True}
        self.mechanics_module.update(self.state)
        
        # Update time trackers
        self.state.time += self.dt
        self.state.time_since_servo += self.dt
        self.state.time_since_open_voltage += self.dt
        
        if self.state.spark_status[0] == 1:
            self.state.time_since_spark_ignition += self.dt
            self.state.time_since_spark_end = 0
        else:
            self.state.time_since_spark_end += self.dt
            self.state.time_since_spark_ignition = 0
        
        # Only return meaningful observations and calculate rewards on control steps
        if is_control_step:
            observation = self._get_obs()
            reward = self._calculate_reward()
            self.previous_target_current = self.state.peak_current
        else:
            observation = None
            reward = 0
        
        terminated = self._check_termination()
        truncated = False
        
        info = {
            'wire_broken': self.state.is_wire_broken,
            'target_reached': self.state.is_target_distance_reached,
            'spark_status': self.state.spark_status[0],
            'time': self.state.time,
            'is_control_step': is_control_step
        }
        
        return observation, reward, terminated, truncated, info

import matplotlib.pyplot as plt
import time
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter

env = WireEDMEnv()
env.state.workpiece_position = 10
env.state.wire_position = 0
env.state.target_voltage = 80
env.state.peak_current = 300
env.state.OFF_time = 80

voltage_history = []
current_history = []
time_history = []
temperature_history = []
wire_temperature_evolution = []

start_time = time.time()
for i in range(1000000): # 1 seconds of simulation at 1us timesteps
    action = {
        'servo': np.array([0.0], dtype=np.float32),
        'generator_control': {
            'target_voltage': np.array([80.0], dtype=np.float32),
            'peak_current': np.array([300.0], dtype=np.float32),
            'ON_time': np.array([2.0], dtype=np.float32),
            'OFF_time': np.array([5.0], dtype=np.float32)
        }
    }
    env.step(action)
    voltage_history.append(env.state.voltage)
    current_history.append(env.state.current)
    time_history.append(env.state.time)
    temperature_history.append(env.state.wire_average_temperature)
    wire_temperature_evolution.append(env.state.wire_temperature.copy())
end_time = time.time()
print(f"Simulation took {end_time - start_time} seconds")
