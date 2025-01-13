import numpy as np
import gymnasium as gym
from gymnasium import spaces
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
import numpy as np

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
    target_current: Optional[float] = None
    
    # Workpiece state variables
    
    workpiece_position: float = 0 # Current position of the workpiece
    
    # Wire state variables
    wire_position: float = 0.0 # Current position of the wire
    wire_velocity: float = 0.0 # Current velocity of the wire
    wire_unwinding_velocity = 0.2 # Unwinding velocity of the wire in micrometers per microsecond (microns/μs -- mm/ms .. m/s)
    
    crater_dtype = np.dtype([
        ('radius', 'f4'),          # float32 for crater radius
        ('y_position', 'f4'),      # float32 for y-axis position
        ('time_formed', 'i4'),     # int32 for timestamp
        ('depth', 'f4'),           # float32 for crater depth
    ])
    
    craters_on_wire: np.ndarray = field(default_factory=lambda: np.array([], dtype=crater_dtype)) # List of craters on the wire (position, time, crater size, etc.)
    
    wire_average_temperature: float = 0.0 # Average temperature of the wire across the length
    
    
    # Spark state variables
    
    # Tuple to track current spark status (state, y-location, duration)
    # state: 0=No event, 1=Spark formation, -1=Short circuit
    # y_location: Position along wire length where spark is occurring (None if no spark)
    # duration: How many timesteps the current spark state has existed
    spark_status: Tuple[int, Optional[float], int] = (0, None, 0)
    
    # Wire state
    wire_velocity: float = 0.0
    sparks_on_wire: List[Tuple[float, int]] = field(default_factory=list)
    average_temperature: float = 0.0
    
    # Dielectric state variables
    
    dielectric_conductivity: float = 0.0 # Conductivity of the dielectric
    dielectric_temperature: float = 0.0 # Temperature of the dielectric
    
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
        
        # First check for short circuits
        if state.is_wire_colliding:
            state.spark_status = (-1, state.wire_position, 0)  # Short circuit
            state.voltage = 0
            state.current = state.target_current
            return
        
        # If there's no voltage applied, no ignition can occur
        if state.target_voltage == 0:
            state.spark_status = (0, None, 0)  # No spark
            state.voltage = 0
            state.current = 0
            return

        # Unpack current spark status
        spark_state, spark_location, spark_duration = state.spark_status
        
        # If there's already a spark, maintain it until current is cut
        if spark_state == 1:
            if state.target_current:
                state.spark_status = (1, spark_location, spark_duration + 1)
                state.voltage = state.target_voltage * 0.3  # Voltage drop during discharge
                state.current = state.target_current
            else:
                state.spark_status = (0, None, 0)  # Spark ends when current is cut
                state.voltage = state.target_voltage
                state.current = 0
            return
    
    # Calculate probability of new spark formation
    p_ignition = self._get_spark_conditional_probability(state)
    
    # Sample from probability distribution
    if self.env.np_random.random() < p_ignition:
        # Ignition occurs - randomly choose location along wire height
        spark_location = self.env.np_random.uniform(0, self.env.workpiece_height)
        state.spark_status = (1, spark_location, 0)
        state.voltage = state.target_voltage * 0.3  # Voltage drops during discharge
        state.current = state.target_current
    else:
        # No ignition
        state.spark_status = (0, None, 0)
        state.voltage = state.target_voltage
        state.current = 0
    
    def _get_spark_conditional_probability(self, state):
        """ Calculate the conditional probability of sparking at a given microsecond,
        given that it has not sparked yet since the last voltage rise."""

        # In the case of the exponential distribution, the conditional
        # probability is just lambda
        return self._get_lambda(state)
    
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
    def update(self, state):
        # Check if there's a new spark (spark_status[0] == 1 and spark_status[2] == 0)
        spark_state, _, spark_duration = state.spark_status
        if spark_state == 1 and spark_duration == 0:
            # Add a small random amount to workpiece position when new spark occurs
            # This simulates material removal at spark location
            removal_amount = 0.001  # 1 micron per spark
            state.workpiece_position += removal_amount

class DielectricModule(EDMModule):
    def update(self, state):
        # Your dielectric logic
        # For the moment leave blank
        pass

class WireModule(EDMModule):
    def update(self, state):
        # Wire position depends on servo action, but leave blank for now
        pass
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
        
        self.action_space = spaces.Dict({
            'servo': spaces.Box(
                low=np.array([-1.0]),  # Placeholder values
                high=np.array([1.0]),
                dtype=np.float32
            ),
            'voltage_control': spaces.Box(
                low=np.array([0.0]),
                high=np.array([200.0]),  # Placeholder max voltage
                dtype=np.float32
            ),
            'current_control': spaces.Box(
                low=np.array([0.0]),
                high=np.array([100.0]),  # Placeholder max current
                dtype=np.float32
            )
        })
        
        self.previous_target_current = 0 # Store previous target current for reward calculation
        
        # Import modules here to avoid circular imports
        import gymnasium as gym
        from gymnasium import spaces
        import numpy as np
        from .edm_state import EDMState
        from . import update_ignition
        from . import update_material_removal
        from . import update_dielectric
        from . import update_wire
        from . import update_mechanics
        
        self._update_ignition = update_ignition.update_ignition
        self._update_material_removal = update_material_removal.update_material_removal
        self._update_dielectric = update_dielectric.update_dielectric
        self._update_wire = update_wire.update_wire
        self._update_mechanics = update_mechanics.update_mechanics
        
def step(self, action):
    # Track if this is a control step (every 1ms / 1000μs)
    is_control_step = self.state.time_since_servo >= self.servo_interval
    
    # Only process actions on control steps
    if is_control_step:
        self.state.target_delta = action['servo'][0]
        self.state.target_voltage = action['voltage_control'][0]
        self.state.target_current = action['current_control'][0]
        self.state.time_since_servo = 0  # Reset timer
    
    # Sequential process updates
    self._update_ignition()
    self._update_material_removal()
    self._update_dielectric()
    self._update_wire()
    if self.state.is_wire_broken:
        # If the wire is broken, return immediately
        return None, 0, True, False, {'wire_broken': True}
    self._update_mechanics()
    
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
        self.previous_target_current = target_current  # Store for next timestep
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
