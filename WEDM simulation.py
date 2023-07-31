import sys
import time
from collections import deque

import numpy as np
import pygame


class Environment:
    """A class representing a simulated environment for wire erosion. All units are in micrometers and microseconds."""

    def __init__(self, time_between_movements, min_step_size, workpiece_distance_increment, 
                 crater_diameter, spark_ignition_time, heat_dissipation_time, T_timeout, T_rest, 
                 piece_height, unwinding_speed, target_distance, start_position_wire=99, 
                 start_position_workpiece=100):
        """
        Initialize the environment with the given parameters.

        :param time_between_movements: Time between motor movements.
        :param min_step_size: Minimum step size for motor movements.
        :param workpiece_distance_increment: Workpiece distance increment after each spark.
        :param spark_ignition_time: Time it takes from origination to extinction of a spark.
        :param heat_dissipation_time: Time it takes of a spark to dissipate 
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
        self.spark_ignition_time = spark_ignition_time
        self.heat_dissipation_time = heat_dissipation_time # Time that the heat of a spark is in the wire
        
        
        # Physical variables for the simulation
        
        self.workpiece_position = start_position_workpiece
        self.wire_position = start_position_wire

        # Auxiliary variables for the simulation
        
        self.time_counter = 0
        self.time_counter_global = 0
        self.sparks_positions_list = deque([-1] * self.heat_dissipation_time, maxlen=self.heat_dissipation_time)
        self.is_wire_broken = False
        self.is_wire_colliding = False
        self.is_target_distance_reached = False
        self.spark_counter = 0
        self.display = None
        self.sparks = []
        self.t1 = 0
        self.t2 = 1
        self.history = []
        self.FPS = -1
        
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

    def _get_wire_break_conditional_probability(self):
        """ Calculate the conditional probability of the wire breaking after a
        spark."""

        # If there are 5 sparks at a distance less than 100 micrometers, the
        # the wire breaks. We calculate the distance between the sparks
        # in self.sparks_positions_list

        # filter out -1 and sort the positions
        relevant_sparks = sorted(spark for spark in self.sparks_positions_list if spark != -1)

        # count the number of sparks within range
        sparks_in_range = sum(abs(relevant_sparks[i] - relevant_sparks[i+1]) < self.crater_diameter for i in range(len(relevant_sparks) - 1))

        # check if wire breaks
        if sparks_in_range >= 3:
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

            self.spark_counter += 1
            self.workpiece_position += self.workpiece_distance_increment
            
            # self.display.spark_sound.play()
            spark_y = np.random.randint(0, self.piece_height)
            self.sparks_positions_list.append(spark_y)
            self.sparks.append(((self.wire_position + self.workpiece_position)/2 , spark_y, 2000))  # Each spark bright lasts for 2000 microseconds
            
            self.time_counter = 0
            self.time_counter_global += 1
            
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
                print("It took ", self.time_counter_global/1000000, " seconds to reach the target distance.")
             
            # After a spark, the voltage is down for T_rest + self.spark_ignition_time microseconds
            for _ in range(self.T_rest + self.spark_ignition_time):
                self.time_counter_global += 1
                self.sparks_positions_list.append(-1) # -1 means no spark
        else:
            
            self.sparks_positions_list.append(-1) # -1 means no spark
            self.time_counter += 1
            self.time_counter_global += 1
        
        
        if self.time_counter_global % 1667 == 0 and self.display is not None: # at 1667 microseconds, a frame is drawn. If fps§ = 60, then 1s real time = 0.1 s (simulation time)
            self.display.clock.tick(60) # make sure the game runs at 60 fps
            self.t2 = time.time()
            self.display.draw()
            self.FPS = 1/(self.t2 - self.t1)
            self.t1 = time.time()
            
        self.sparks = [(x, y, lifespan-1) for x, y, lifespan in self.sparks if lifespan > 1]
        
        
    def unwind_wire(self):
        """
        Unwind the wire by the unwinding speed. This affects the position of the sparks in the wire.
        """       
        # add delta to all the spark positions
        for i in range(len(self.sparks_positions_list)):
            if self.sparks_positions_list[i] != -1:
                self.sparks_positions_list[i] += self.unwinding_speed 
            if self.sparks_positions_list[i] > self.piece_height:
                self.sparks_positions_list[i] = -1
            
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
            # moving at 1 micrometer/microsecond) #CHECK THIS # TODO
            self._generate_sparks()
            self.unwind_wire()
        
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
            self.unwind_wire()
            if self.is_done():
                break

    def reset(self):
        """
        Reset the environment to its initial state.
        """
        self.workpiece_position = self.start_position_workpiece
        self.wire_position = self.start_position_wire
        self.time_counter = 0
        self.time_counter_global = 0
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
            "time_counter": self.time_counter,
            "time_counter_global": self.time_counter_global,
            "is_wire_broken": self.is_wire_broken
        }
        

class Display:
    def __init__(self, environment):
        self.environment = environment
        self.win_width = 400
        self.win_height = 400
        self.wire_width = 100 # wire width in pixels
        self.wire_height = self.win_height
        self.workpiece_width = self.win_width - self.environment.workpiece_position
        self.init_pygame()

    def init_pygame(self):
        pygame.init()
        self.screen = pygame.display.set_mode((self.win_width, self.win_height))
        pygame.display.set_caption('Wire EDM Simulation')
        # make sure the game will run at 60 fps maximum
        self.clock = pygame.time.Clock()

    def draw(self):
        self.screen.fill((50, 50, 50))
        # note that the wire position is the position of the right end of the wire
        wire_rect = pygame.Rect(self.environment.wire_position - self.wire_width, 0, self.wire_width, self.wire_height)
        pygame.draw.rect(self.screen, (200, 100, 0), wire_rect)

        workpiece_rect = pygame.Rect(self.environment.workpiece_position, self.win_height/2 - self.environment.piece_height/2, self.workpiece_width, self.environment.piece_height)
        pygame.draw.rect(self.screen, (150, 150, 150), workpiece_rect)
        
        for x, y, _ in self.environment.sparks:
            spark_height =  10
            spark_width = abs(self.environment.workpiece_position - self.environment.wire_position)  # Width of the spark is the distance between the wire and the workpiece
            spark_rect = pygame.Rect(x - spark_width/2, self.win_height/2 - self.environment.piece_height/2 + y - spark_height/2, spark_width, spark_height)
            pygame.draw.ellipse(self.screen, (255, 255, 255), spark_rect.inflate(20, 20))
            pygame.draw.ellipse(self.screen, (250, 250, 255), spark_rect.inflate(18, 18))
            pygame.draw.ellipse(self.screen, (245, 245, 255), spark_rect.inflate(16, 16))
            pygame.draw.ellipse(self.screen, (240, 240, 255), spark_rect.inflate(14, 14))
            pygame.draw.ellipse(self.screen, (235, 235, 255), spark_rect.inflate(12, 12))
            pygame.draw.ellipse(self.screen, (230, 230, 255), spark_rect.inflate(10, 10))
            pygame.draw.ellipse(self.screen, (225, 225, 255), spark_rect.inflate(8, 8))
            pygame.draw.ellipse(self.screen, (220, 220, 255), spark_rect.inflate(6, 6))
            pygame.draw.ellipse(self.screen, (215, 215, 255), spark_rect.inflate(4, 4))
            pygame.draw.ellipse(self.screen, (210, 210, 255), spark_rect.inflate(2, 2))
            pygame.draw.ellipse(self.screen, (205, 205, 255), spark_rect)
        
        #draw FPS in the upper left corner
        
        font = pygame.font.SysFont('Arial', 20)
        # render text
        text = font.render('FPS: ' + str(int(self.environment.FPS)), True, (255, 255, 255))
        # position where the text will be drawn
        position = (0, 0)  # upper-left corner
         # draw text on the screen
        self.screen.blit(text, position)

        pygame.display.update()

    # def human_actor(self):
    #     if pygame.event.get(pygame.QUIT):
    #         pygame.quit()
    #         sys.exit()
    #     pygame.event.pump()
    #     keys = pygame.key.get_pressed()
    #     if keys[pygame.K_LEFT]:
    #         self.environment.step((-1, 1))
    #     elif keys[pygame.K_RIGHT]:
    #         self.environment.step((1, 1))
    #     else: 
    #         self.environment.step((1, 0)) # no key pressed, continue
    #         # simulation with no movement
    
    def PID_actor(self):
        if self.environment.spark_counter < 3:
            self.environment.step((1, 1))
        else:
            self.environment.step((-1, 1))
                    
    def run(self):
        while not self.environment.is_done():
            # self.human_actor()
            self.PID_actor()
            self.environment.history.append(self.environment.get_environment_state())
            
def main():
    time_between_movements = 1000  # in microseconds
    min_step_size = 1 # in micrometers
    workpiece_distance_increment = 0.05  # in micrometers
    crater_diameter = 50  # in micrometers
    spark_ignition_time = 3  # in microseconds
    heat_dissipation_time = 100 # in microseconds
    T_timeout = 5000  # in microseconds
    T_rest = 10  # in microseconds
    piece_height = 400  # in micrometers
    unwinding_speed = 0.17  # in micrometers per microsecond
    target_distance = 1500  # in micrometers
    start_position_wire = 90  # in micrometers
    start_position_workpiece = 100  # in micrometers
    # Initializing Environment
    env = Environment(time_between_movements, min_step_size, workpiece_distance_increment, crater_diameter,
                    spark_ignition_time, heat_dissipation_time, T_timeout, T_rest, piece_height, unwinding_speed, target_distance,
                    start_position_wire, start_position_workpiece)

    # Initializing Display and setting it for the Environment
    display = Display(env)
    env.set_display(display)
    display.run()
    # Print average distance between workpiece and wire, but only for wire_position > start_workpiece_position
    print("Average distance between workpiece and wire: ", sum([state["workpiece_position"] - state["wire_position"] for state in env.history if state["wire_position"] > start_position_workpiece])/len([state["workpiece_position"] - state["wire_position"] for state in env.history if state["wire_position"] > start_position_workpiece]))

if __name__ == '__main__':
    
    main()
