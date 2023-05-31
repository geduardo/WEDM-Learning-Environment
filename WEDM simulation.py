import pygame
import sys
import numpy as np
from collections import deque


class Environment:
    """A class representing a simulated environment for wire erosion. All units are in micrometers and microseconds."""

    def __init__(self, time_between_movements, min_step_size, workpiece_distance_increment, crater_diameter, spark_ignition_time, T_timeout, T_rest, piece_height, unwinding_speed, target_distance, start_position_wire=0, start_position_workpiece=100):
        """
        Initialize the environment with the given parameters.

        :param time_between_movements: Time between motor movements.
        :param min_step_size: Minimum step size for motor movements.
        :param workpiece_distance_increment: Workpiece distance increment after each spark.
        :param spark_ignition_time: Time it takes from origination to extinction of a spark.
        :param T_timeout: Time down after wire break.
        :param T_rest: Time down after end of spark.
        :param piece_height: Height of the workpiece.
        :param unwinding_speed: Speed at which the wire unwinds.
        :param target_distance: Target distance for the wire to reach.
        :param start_position_wire: The initial position of the wire. Default is 0.
        :param start_position_workpiece: The initial position of the workpiece. Default is 100.
        """
        
        # Constants for the environment
        self.start_position_workpiece = start_position_workpiece
        self.start_position_wire = start_position_wire
        self.time_between_movements = time_between_movements        
        self.min_step_size = min_step_size        
        self.workpiece_distance_increment = workpiece_distance_increment        
        self.piece_height = piece_height
        self.unwinding_speed = unwinding_speed
        self.renewal_time = int(self.piece_height/self.unwinding_speed)
        self.T_timeout = T_timeout
        self.T_rest = T_rest
        self.target_distance = target_distance
        self.crater_diameter = crater_diameter
        
        # Physical variables for the simulation
        self.workpiece_position = start_position_workpiece
        self.wire_position = start_position_wire
        self.spark_ignition_time = spark_ignition_time
        
        # Auxiliary variables for the simulation
        self.time_counter = 0
        self.time_counter_global = 0
        self.sparks_list = deque([0] * self.renewal_time, maxlen=self.renewal_time)
        self.is_wire_broken = False
        self.spark_counter = 0
        self.display = None
    
    def set_display(self, display):
        """
        Set the display for the environment.

        :param display: The display to be set.
        """
        self.display = display
        
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

    def _generate_sparks(self):
        """
        Generate sparks in the wire based on the conditional probability of
        sparking at a given microsecond.
        """
        # sample spark
        if np.random.rand() < self._get_spark_conditional_probability(self._get_lambda(self.wire_position, self.workpiece_position), self.time_counter):
            self.sparks_list.append(1)
            self.spark_counter += 1
            self.workpiece_position += self.workpiece_distance_increment
            # Print ignition delay time
            print("Ignition delay time: ", self.time_counter)
            self.time_counter = 0
            self.time_counter_global += 1
            
            # Check if the wire is broken
            self.is_wire_broken = np.random.rand() < self._get_wire_break_conditional_probability(sum(self.sparks_list))
            if self.is_wire_broken:
                print("Wire broken!")
            
            if self.wire_position >= self.workpiece_position:
                print("Collision!")
             
            # After a spark, the voltage is down for T_rest microseconds
            for _ in range(self.T_rest):
                self.time_counter_global += 1
                self.sparks_list.append(0)
        else:
            self.sparks_list.append(0)
            self.time_counter += 1
            self.time_counter_global += 1
        
        self.display.draw()
            
    def _move_motor(self, action):
        """
        Move the motor in the desired direction and number of steps.

        :param action: Tuple containing the direction and number of steps.
        """
        direction, number_of_steps = action
        
        # Move the motor in the desired direction and number of steps
        for _ in range(number_of_steps):
            self.wire_position = self.wire_position + direction * self.min_step_size
            # Generate during motor movement (we assume that the motor is always
            # moving at 1 micrometer/microsecond) #CHECK THIS #TODO
            self._generate_sparks()
        
    def is_done(self):
        """
        Check if the environment has reached a termination condition.

        :return: True if the wire is broken or the target distance has been reached, False otherwise.
        """
        return self.is_wire_broken or self.workpiece_position >= self.target_distance or self.wire_position >= self.workpiece_position
    
    def step(self, action):
        """
        Execute a step in the environment based on the given action.

        :param action: Tuple containing the direction and number of steps.
        :raises ValueError: If the action is not a tuple.
        """
        # Reset the spark counter
        self.spark_counter = 0
        # Check if the action is valid
        if not isinstance(action, tuple):
            raise ValueError("The action must be a tuple.")
        # Move the motor
        self._move_motor(action)
        
        # After the motor movement, sample sparks each microsecond until the
        # next motor movement
        for _ in range(self.time_between_movements):
            self._generate_sparks()
            if self.is_done():
                break
        print("Sparks in step: ", self.spark_counter)


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
        

class Display:
    def __init__(self, environment):
        self.environment = environment
        self.win_width = 800
        self.win_height = 600
        self.wire_width = 10 # wire width in pixels
        self.wire_height = self.win_height
        self.workpiece_width = self.win_width - self.environment.workpiece_position
        self.workpiece_height = 100
        self.init_pygame()

    def init_pygame(self):
        pygame.init()
        self.screen = pygame.display.set_mode((self.win_width, self.win_height))
        pygame.display.set_caption('Wire EDM Simulation')

    def draw(self):
        self.screen.fill((0, 0, 0))
        wire_rect = pygame.Rect(self.environment.wire_position, 0, self.wire_width, self.wire_height)
        pygame.draw.rect(self.screen, (200, 100, 0), wire_rect)

        workpiece_rect = pygame.Rect(self.environment.workpiece_position, self.win_height/2, self.workpiece_width, self.workpiece_height)
        pygame.draw.rect(self.screen, (200, 200, 200), workpiece_rect)
        pygame.display.update()
        

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    self.environment.step((-1, 1))
                elif event.key == pygame.K_RIGHT:
                    self.environment.step((1, 1))
                    
    def run(self):
        while not self.environment.is_done():
            self.handle_events()

            
def main():

    time_between_movements = 10000  # in microseconds
    min_step_size = 1  # in micrometers
    workpiece_distance_increment = 0.1  # in micrometers
    crater_diameter = 0.1  # in micrometers
    spark_ignition_time = 50  # in microseconds
    T_timeout = 5000  # in microseconds
    T_rest = 10  # in microseconds
    piece_height = 20000  # in micrometers
    unwinding_speed = 5  # in micrometers per microsecond
    target_distance = 10000  # in micrometers
    start_position_wire = 90  # in micrometers
    start_position_workpiece = 100  # in micrometers

    # Initializing Environment
    env = Environment(time_between_movements, min_step_size, workpiece_distance_increment, crater_diameter,
                    spark_ignition_time, T_timeout, T_rest, piece_height, unwinding_speed, target_distance,
                    start_position_wire, start_position_workpiece)

    # Initializing Display and setting it for the Environment
    display = Display(env)
    env.set_display(display)
    display.run()

if __name__ == '__main__':
    main()
