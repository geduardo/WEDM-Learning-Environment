import numpy as np
import pygame

import sys
from collections import deque

import gymnasium as gym
from gymnasium import spaces

class WireEDMEnv(gym.Env):    
    metadata = {"render_modes": ["human"], "render_fps": 300}
    
    """A class representing a simulated environment for wire erosion. All units are in micrometers and microseconds."""
    
    def __init__(self, render_mode = None, servo_interval = 1000, min_step_size = 1, max_steps = 1, crater_diameter = 100, 
                 crater_depth = 5,pulse_duration = 2 , dissipation_time = 100, break_timeout = 60*10**6, rest_time = 10,
                 workpiece_height = 10000, unwinding_speed = 0.17, target_distance =  10000, 
                 wire_start=50, workpiece_start=100, max_time_steps = 1000):
        
        """
        Initialize the environment with the given parameters.
        :param servo_interval: Time between motor movements.
        :param pulse_duration: Duration of the electric pulse delivered by the generator after the breakdown of the dielectric.
        :param dissipation_time: Time it takes of a spark to dissipate 
        :param break_timeout: Time down after wire break.
        :param rest_time: Time down after end of spark.
        :param min_step_size: Minimum step size for motor movements.
        :param max_steps: Maximum number of steps for motor movements.
        :param workpiece_height: Height of the workpiece.
        :param unwinding_speed: Speed at which the wire unwinds.
        :param target_distance: Target distance for the wire to reach.
        :param wire_start: The initial position of the wire. Default is 0.
        :param workpiece_start: The initial position of the workpiece. Default is 100.
        """
        
        # Constants for the environment
            ## Environment constants
        self.workpiece_start = workpiece_start
        self.wire_start = wire_start
        self.target_distance = target_distance
        self.workpiece_height = workpiece_height
        self.max_steps = max_steps
            ## Process constants
        self.break_timeout = break_timeout
        self.rest_time = rest_time
        self.servo_interval = servo_interval
        self.dissipation_time = dissipation_time
        self.crater_depth = crater_depth
        self.crater_diameter = crater_diameter
        self.heat_affected_zone = 2*self.crater_diameter
        self.min_step_size = min_step_size
        self.time_step_count = 0
        self.max_time_steps = max_time_steps
        
            ## Technology constants
        self.unwinding_speed = unwinding_speed
        self.pulse_duration = pulse_duration
            ## Derived
        self.workpiece_distance_increment = self.crater_depth * self.crater_diameter / self.workpiece_height
        # Physical variables
        
        self.workpiece_position = workpiece_start
        self.wire_position = wire_start
        self.sparks = []

        # Auxiliary variables for the simulation
        self.time_counter = 0
        self.time_counter_global = 0
        self.is_wire_broken = False
        self.is_wire_colliding = False
        self.is_target_distance_reached = False
        self.sparks_frame = []
        self.initial_gap = self.workpiece_start - self.wire_start
        self.average_gap = deque([0]*self.initial_gap, maxlen=1000)
        self.average_speed = deque([0]*1000, maxlen=1000)
        self.t1 = 0
        self.t2 = 1
        self.history = []
        self.FPS = -1
        self.clock = None
        self.t1 = pygame.time.get_ticks()
        self.lambda_cache = {}  # create a cache to avoid recalculating the lambda parameter
        
        # Pygame related attributes
        
        assert render_mode is None or render_mode in self.metadata["render_modes"]
        self.render_mode = render_mode
        if self.render_mode == "human":
            self.window_width = 1280
            self.window_height = 720
            self.wire_width = 300 # wire width in pixels
            self.wire_height = self.window_height
            self.workpiece_width = self.window_width - self.workpiece_position
            self.vertical_downscale = 0.05
            self.workpiece_height_render = self.workpiece_height * self.vertical_downscale            
            self.window = None
            self.clock = None
        
        # Gymasium variables
        # We have 2*max_steps + 1 possible actions. This can be encoded as a discrete space with 2*max_steps + 1 elements.
        self.action_space = spaces.Discrete(2*max_steps + 1)
        # Our observation space is just a single integer number, this is: self.spark_counter (number of sparks in the last servo_interval microseconds)
        self.observation_space = spaces.Box(low=0, high=np.inf, shape=(1,), dtype=np.float32)
        # Dictionary to map actions to motor steps
        self._action_to_motor_step = lambda action: (1, action - self.max_steps) if action > self.max_steps else (-1, self.max_steps - action)
        self.truncated = False
        
    def _add_spark(self, position):
        self.sparks.append((position, self.dissipation_time))

    def _get_obs(self):
        """
        Get the current observation of the environment.

        :return: The current observation of the environment.
        """
        return np.array([self.spark_counter], dtype=np.float32)

        
    def _get_lambda(self, wire_position, workpiece_position):
        """
        Calculate the lambda parameter of the exponential distribution based
        on empirical interpolation.

        :param wire_position: Wire position. type: int
        :param workpiece_position: Workpiece position. type: int
        :return: Lambda parameter.
        """
        d = wire_position - workpiece_position

        # Check if we have already computed the value for this distance
        if d in self.lambda_cache:
            return self.lambda_cache[d]

        # Compute the value and store it in the cache
        lambda_value = np.log(2)/(0.48*d*d -3.69*d + 14.05) # Empirical interpolation of the lambda parameter
        self.lambda_cache[d] = lambda_value

        return lambda_value
        
    def _get_spark_conditional_probability(self, lambda_param, time_from_voltage_rise):
        """ Calculate the conditional probability of sparking at a given microsecond,
        given that it has not sparked yet since the last voltage rise."""
        
        # In the case of the exponential distribution, the conditional
        # probability is just lambda
        return lambda_param

    def _get_wire_break_conditional_probability(self):
        """
        Calculate the conditional probability of the wire breaking after a spark.
        """
        
        # get the positions of the sparks in the wire
        positions = [spark[0] for spark in self.sparks]
        positions_sorted = np.sort(positions)
        # get the distances between the sparks
        distances = np.diff(positions_sorted)
        # get the number of colliding sparks
        sparks_collisions = np.sum(distances < self.heat_affected_zone)
        if sparks_collisions >= 2:
            return 1
        else:
            return 0
        
    
    def _generate_sparks(self):
        """
        Generate sparks in the wire based on the conditional probability of
        sparking at a given microsecond.
        """
        # sample spark
        if np.random.rand() < self._get_spark_conditional_probability(self._get_lambda(self.wire_position, self.workpiece_position), self.time_counter):
            self.time_counter = 0
            self.time_counter_global += 1
            self.spark_counter += 1
            self.workpiece_position += self.workpiece_distance_increment
            spark_y = np.random.randint(0, self.workpiece_height)
            spark_x = (self.wire_position + self.workpiece_position)/2
            self._add_spark(spark_y)
            self.sparks_frame.append((spark_x , spark_y))  # Add spark to the list of sparks in the current frame
            # Check if the wire is broken
            self.is_wire_broken = np.random.rand() < self._get_wire_break_conditional_probability()
            
            if self.is_wire_broken:
                print("Wire broken!")
            
            self.is_wire_colliding = self.wire_position >= self.workpiece_position
            if self.is_wire_colliding:
                print("Collision!")

            self.is_target_distance_reached = self.workpiece_position >= self.target_distance
            if self.is_target_distance_reached:
                print("Target distance reached!")

            # After a spark, the voltage is down for rest_time + self.pulse_duration microseconds
            for _ in range(self.rest_time + self.pulse_duration):
                self.time_counter_global += 1

        else:
            self.time_counter += 1
            self.time_counter_global += 1
        
    def _unwind_wire(self):
        """
        Unwind the wire by the unwinding speed. This affects the position of the sparks in the wire.
        """
        # add delta to all the spark positions
        new_sparks = []
        for spark in self.sparks:
            new_spark = (spark[0] - self.unwinding_speed, spark[1] - 1)
            if new_spark[0] >= 0 and new_spark[1] >= 0:
                new_sparks.append(new_spark)
        self.sparks = new_sparks
            
    def _move_motor(self, motor_step):
        """
        Move the motor in the desired direction and number of steps.

        :param action: Tuple containing the direction and number of steps.
        """
        direction, number_of_steps = motor_step
        
        # Move the motor in the desired direction and number of steps
        for _ in range(number_of_steps):
            self.wire_position = self.wire_position + direction * self.min_step_size
            # Generate during motor movement (we assume that the motor is always
            # moving at 1 micrometer/microsecond) #CHECK THIS # TODO
            self._generate_sparks()
            self._unwind_wire()
        
    def is_done(self):
        """
        Check if the environment has reached a termination condition.

        :return: True if the wire is broken or the target distance has been reached, False otherwise.
        """
        return self.is_wire_broken or self.is_target_distance_reached or self.is_wire_colliding
    
    def step(self, action):
        """
        Execute a step in the environment based on the given action.

        :param action: Tuple containing the direction and number of steps.
        :raises ValueError: If the action is not a tuple.
        """
        # Reset the spark counter
        self.sparks_frame = []
        self.spark_counter = 0
        motor_step = self._action_to_motor_step(action)
        old_wire_position = self.wire_position
        self._move_motor(motor_step)
        new_wire_position = self.wire_position
        new_workpiece_position = self.workpiece_position
        gap = new_workpiece_position - new_wire_position
        self.average_gap.append(gap)
        speed = new_wire_position - old_wire_position
        self.average_speed.append(speed)
        
        # After the motor movement, sample sparks each microsecond until the
        # next motor movement
        
        for _ in range(self.servo_interval):
            self._generate_sparks()
            self._unwind_wire()
            if self.is_done():
                break
        
        observation = self._get_obs()
        info = self.get_info()
        if self.render_mode == "human":
            self._render_frame()

        action_reward  = motor_step[0]*motor_step[1]
        
        reward = action_reward - 1000*self.is_wire_broken - 1000*self.is_wire_colliding
        
        self.time_step_count += 1
        
        if self.time_step_count > self.max_time_steps:
            self.truncated = True
             
        terminated = self.is_done()
        
        return observation, reward, terminated, self.truncated, info
                
    def reset(self,seed=None, options=None):
        super().reset(seed=seed)
        self.workpiece_position = self.workpiece_start
        self.wire_position = self.wire_start
        self.time_counter = 0
        self.time_counter_global = 0
        self.spark_counter = 0
        self.time_step_count= 0
        self.sparks_positions = np.full(self.dissipation_time, -1, dtype=np.float64)
        self.current_spark_index = 0
        self.sparks_frame = []
        self.is_wire_broken = False
        self.is_wire_colliding = False
        self.is_target_distance_reached = False
        self.average_gap = deque([0]*self.initial_gap, maxlen=1000)
        self.average_speed = deque([0]*1000, maxlen=1000)
        self.truncated = False
        
        observation = self._get_obs()
        info = self.get_info()
        
        if self.render_mode == "human":
            self._render_frame()
        
        return observation, info
    
        
    def get_info(self):
        """
        Get the current state of the environment.

        :return: A dictionary containing the workpiece_position, wire_position, time_counter,
                 time_counter_global, spark_list and is_wire_broken values of the environment.
        """
        return {
            "workpiece_position": self.workpiece_position,
            "wire_position": self.wire_position,
            "time_counter": self.time_counter,
            "time_counter_global": self.time_counter_global,
            "is_wire_broken": self.is_wire_broken,
        }
        
    def _render_frame(self):
        if self.window is None and self.render_mode == "human":
            pygame.init()
            pygame.display.init()
            self.window = pygame.display.set_mode((self.window_width, self.window_height))
            
        if self.clock is None and self.render_mode == "human":
            self.clock = pygame.time.Clock()
            
        self.window.fill((50, 50, 50))
        # note that the wire position is the position of the right end of the wire
        wire_rect = pygame.Rect(self.wire_position - self.wire_width, 0, self.wire_width, self.wire_height)
        pygame.draw.rect(self.window, (200, 100, 0), wire_rect)

        workpiece_rect = pygame.Rect(self.workpiece_position, self.window_height/2 - self.workpiece_height_render/2, self.workpiece_width, self.workpiece_height_render)        
        
        pygame.draw.rect(self.window, (150, 150, 150), workpiece_rect)
        
        for x, y in self.sparks_frame:
            spark_height =  5 
            spark_width = abs(self.workpiece_position - self.wire_position)  # Width of the spark is the distance between the wire and the workpiece
            spark_rect = pygame.Rect(x - spark_width/2, self.window_height/2 - self.workpiece_height_render/2 + y*self.vertical_downscale - spark_height/2, spark_width, spark_height)
            pygame.draw.ellipse(self.window, (255, 255, 255), spark_rect.inflate(20, 20))
            pygame.draw.ellipse(self.window, (250, 250, 255), spark_rect.inflate(18, 18))
            pygame.draw.ellipse(self.window, (245, 245, 255), spark_rect.inflate(16, 16))
            pygame.draw.ellipse(self.window, (240, 240, 255), spark_rect.inflate(14, 14))
            pygame.draw.ellipse(self.window, (235, 235, 255), spark_rect.inflate(12, 12))
            pygame.draw.ellipse(self.window, (230, 230, 255), spark_rect.inflate(10, 10))
            pygame.draw.ellipse(self.window, (225, 225, 255), spark_rect.inflate(8, 8))
            pygame.draw.ellipse(self.window, (220, 220, 255), spark_rect.inflate(6, 6))
            pygame.draw.ellipse(self.window, (215, 215, 255), spark_rect.inflate(4, 4))
            pygame.draw.ellipse(self.window, (210, 210, 255), spark_rect.inflate(2, 2))
            pygame.draw.ellipse(self.window, (205, 205, 255), spark_rect)
        
        #draw FPS in the upper left corner
        
        self.clock.tick(self.metadata["render_fps"])
        font = pygame.font.SysFont('Arial', 20)
        
        t2 = pygame.time.get_ticks()
        
        fps = 1000/(t2 - self.t1)
        text = font.render('FPS: ' + str(int(fps)), True, (255, 255, 255))
        self.window.blit(text, (0, 0))
        self.t1 = t2
        
        #now the same but with the distance between the wire and the workpiece
        average_gap = sum(self.average_gap)/len(self.average_gap)
        text2 = font.render('Gap distance (um): ' + str(int(average_gap)), True, (255, 255, 255))
        position2 = (0, 20)
        self.window.blit(text2, position2)
        
        # now the same but with the average speed of the wire
        average_speed = sum(self.average_speed)/len(self.average_speed)
        average_speed = average_speed * 60
        position4 = (0, 40)
        text4 = font.render('Average speed (mm/min):  ' + str(int(average_speed)), True, (255, 255, 255))
        self.window.blit(text4, position4)
        pygame.display.update()
        self.check_for_events()
        
    def check_for_events(self):
        for event in pygame.event.get():  
            if event.type == pygame.QUIT: 
                pygame.quit()
                sys.exit()
                
    def close(self):
        if self.window is not None:
            pygame.quit()
            sys.exit()