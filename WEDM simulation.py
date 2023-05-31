import pygame
import sys
import numpy as np
from collections import deque


class Environment:
    """A class representing a simulated environment for wire erosion. All units are in micrometers and microseconds."""

    def __init__(self, time_between_movements, min_step_size, workpiece_distance_increment, spark_ignition_time, T_timeout, T_rest, h, v_u, renewal_time, target_distance, start_position_wire=0, start_position_workpiece=100):
        """
        Initialize the environment with the given parameters.

        :param time_between_movements: Time between motor movements.
        :param min_step_size: Minimum step size for motor movements.
        :param workpiece_distance_increment: Workpiece distance increment after each spark.
        :param spark_ignition_time: Time it takes from origination to extinction of a spark.
        :param h: Height of the workpiece.
        :param v_u: Voltage applied to the wire.
        :param renewal_time: Time for the wire to be renewed.
        :param target_distance: Target distance for the wire to reach.
        :param T_timeout: Time down after wire break.
        :param T_rest: Time down after end of spark.
        """
        self.start_position_workpiece = start_position_workpiece
        self.start_position_wire = start_position_wire
        self.workpiece_position = start_position_workpiece
        self.wire_position = start_position_wire
        self.time_between_movements = time_between_movements
        self.min_step_size = min_step_size
        self.workpiece_distance_increment = workpiece_distance_increment
        self.spark_ignition_time = spark_ignition_time
        self.h = h
        self.v_u = v_u
        self.renewal_time = renewal_time
        self.time_counter = 0
        self.time_counter_global = 0
        self.sparks_list = deque([0] * self.renewal_time, maxlen=self.renewal_time)
        self.is_wire_broken = False
        self.target_distance = target_distance
        self.T_timeout = T_timeout
        self.T_rest = T_rest
        self.spark_counter = 0
    def _get_lambda(self, wire_position, workpiece_position):
        """
        Calculate the lambda parameter of the exponential distribution based
        on empirical interpolation.

        :param wire_position: Wire position.
        :param workpiece_position: Workpiece position.
        :return: Lambda parameter.
        """
        d = wire_position - workpiece_position
        return np.log(2)/(0.48*d*d -3.69*d + 14.05) # Empirical interpolation of the lambda parameter
    
    def _get_spark_conditional_probability(self, lambda_param, time_from_voltage_rise):
        """ Calculate the conditional probability of sparking at a given microsecond,
        given that it has not sparked yet since the last voltage rise."""
        
        # In the case of the exponential distribution, the conditional
        # probability is just lambda
        return lambda_param

    def _get_wire_break_conditional_probability(self, number_of_sparks_on_wire):
        """ Calculate the conditional probability of the wire breaking after a
        spark."""
        
        # FOR TESTING PURPOSES ONLY: the probablity of the wire breaking is
        # proportional to the number of sparks on the wire
        return number_of_sparks_on_wire/100000

    def _move_motor(self, action):
        """
        Move the motor in the desired direction and number of steps.

        :param action: Tuple containing the direction and number of steps.
        """
        direction, number_of_steps = action
        for _ in range(number_of_steps):
            self.wire_position += direction * self.min_step_size
            self._generate_sparks()

    def step(self, action):
        """
        Execute a step in the environment based on the given action.

        :param action: Tuple containing the direction and number of steps.
        :raises ValueError: If the action is not a tuple.
        """
        self.spark_counter = 0
        if not isinstance(action, tuple):
            raise ValueError("The action must be a tuple.")
        self._move_motor(action)
        for _ in range(self.time_between_movements):
            self._generate_sparks()
            if self.is_done():
                break
        print("Sparks in step: ", self.spark_counter)

    def is_done(self):
        """
        Check if the environment has reached a termination condition.

        :return: True if the wire is broken or the target distance has been reached, False otherwise.
        """
        return self.is_wire_broken or self.workpiece_position >= self.target_distance

    def reset(self):
        """
        Reset the environment to its initial state.
        """
        self.workpiece_position = self.start_position_workpiece
        self.wire_position = self.start_position_wire
        self.time_counter = 0
        self.time_counter_global = 0
        self.sparks_list = deque([0] * self.renewal_time, maxlen=self.renewal_time)
        self.is_wire_broken = False
        
    def get_environment_state(self):
        """
        Get the current state of the environment.

        :return: A dictionary containing the workpiece_position, wire_position, time_counter,
                 time_counter_global, spark_list and is_wire_broken values of the environment.
        """
        return {
            "workpiece_position": self.workpiece_position,
            "wire_position": self.wire_position,
            "sparks_list": self.sparks_list,
            "time_counter": self.time_counter,
            "time_counter_global": self.time_counter_global,
            "is_wire_broken": self.is_wire_broken
        }
        

class PygameEnvironment(Environment):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scale_factor = 1  # scale from micrometers to pixels
        self.win_width = 800
        self.win_height = 600
        self.wire_width = 10
        self.wire_height = self.win_height
        self.workpiece_width = self.win_width - self.workpiece_position * self.scale_factor
        self.workpiece_height = 100
        self.sparks_visual = []  # store the visual representation of sparks
        self.init_pygame()

    def init_pygame(self):
        pygame.init()
        self.screen = pygame.display.set_mode((self.win_width, self.win_height))
        pygame.display.set_caption('Wire Erosion Environment')

    def draw(self):
        self.screen.fill((0, 0, 0))
        wire_rect = pygame.Rect(self.wire_position * self.scale_factor, 0, self.wire_width, self.wire_height)
        pygame.draw.rect(self.screen, (200, 100, 0), wire_rect)

        workpiece_rect = pygame.Rect(self.workpiece_position * self.scale_factor, self.win_height/2, self.workpiece_width, self.workpiece_height)
        pygame.draw.rect(self.screen, (200, 200, 200), workpiece_rect)

        for spark in self.sparks_visual:
            spark_brightness = spark[2]
            if spark_brightness > 0:
                # the spark position in x is just in between the wire and the
                # workpiece
                spark_position_x = spark[0]
                # the postion in the y axis is stored when the spark is generated 
                spark_position_y = spark[1]
                pygame.draw.line(self.screen, (255, 255, 0, spark_brightness), (self.wire_position * self.scale_factor + self.wire_width/2, spark_position_y), (self.workpiece_position * self.scale_factor, spark_position_y), 2)
                spark[2] -= 10  # decrease the spark's brightness

        pygame.display.flip()
        
    
    def _generate_sparks(self):
        """
        Generate sparks in the wire based on the conditional probability of
        sparking at a given microsecond.
        """
        # sample spark
        if np.random.rand() < self._get_spark_conditional_probability(self._get_lambda(self.wire_position, self.workpiece_position), self.time_counter):
            spark_position_x = (self.wire_position * self.scale_factor  + self.workpiece_position * self.scale_factor)/2 + self.wire_width/2
            spark_position_y = np.random.randint(self.win_height/2, self.win_height/2 + self.workpiece_height)
            spark_position = [spark_position_x, spark_position_y, 255]  # append the position of the spark and its initial brightness
            self.sparks_visual.append(spark_position)
            self.sparks_list.append(1)
            self.spark_counter += 1
            self.workpiece_position += self.workpiece_distance_increment
            self.time_counter = 0
            self.time_counter_global += 1
            self.is_wire_broken = np.random.rand() < self._get_wire_break_conditional_probability(sum(self.sparks_list))
            if self.is_wire_broken:
                print("Wire broken!")
            for _ in range(self.T_rest):
                self.time_counter_global += 1
                self.sparks_list.append(0)
        else:
            self.sparks_list.append(0)
            self.time_counter += 1
            self.time_counter_global += 1


    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    self.step((-1, 1))
                elif event.key == pygame.K_RIGHT:
                    self.step((1, 1))

    def _move_motor(self, action):
        """
        Move the motor in the desired direction and number of steps.

        :param action: Tuple containing the direction and number of steps.
        """
        direction, number_of_steps = action
        for _ in range(number_of_steps):
            self.wire_position = self.wire_position + direction * self.min_step_size
            self._generate_sparks()
        print("Distance to workpiece: ", -self.wire_position + self.workpiece_position)
        
    def run(self):
        while not self.is_done():
            self.draw()
            self.handle_events()
            pygame.time.delay(100)  # Adding delay for easier observation

            
            
time_between_movements = 1000  # microseconds
min_step_size = 1         # micrometers
workpiece_distance_increment = 0.1  # micrometers
spark_ignition_time = 1     # microseconds
T_timeout = 1               # microseconds
T_rest = 1                  # microseconds
h = 100                     # micrometers
v_u = 5                     # Volts
renewal_time = 100000           # microseconds
target_distance = 1000      # micrometers

env = PygameEnvironment(time_between_movements, min_step_size, workpiece_distance_increment, spark_ignition_time, T_timeout, T_rest, h, v_u, renewal_time, target_distance)
env.run()