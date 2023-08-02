import numpy as np
import pygame
import sys
from collections import deque
import gymnasium as gym
from gymnasium import spaces

class WireEdmEnv(gym.Env):    
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
        
            ## Derived constants
        self.workpiece_distance_increment = self.crater_depth * self.crater_diameter / self.workpiece_height
        
        # Physical variables
        
        self.workpiece_position = workpiece_start
        self.wire_position = wire_start
        self.sparks_positions = deque([-1] * self.dissipation_time, maxlen=self.dissipation_time)

        # Auxiliary variables for the simulation
        self.time_counter = 0
        self.time_counter_global = 0
        self.is_wire_broken = False
        self.is_wire_colliding = False
        self.is_target_distance_reached = False
        self.spark_counter = 0
        self.display = None
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
        # Gymasium variables
        
        # We have 2*max_steps + 1 possible actions. This can be encoded as a discrete space with 2*max_steps + 1 elements.
        self.action_space = spaces.Discrete(2*max_steps + 1)
        
        # Our observation space is just a single integer number, this is,
        # self.spark_counter (number of sparks in the last servo_interval microseconds)
        self.observation_space = spaces.Box(low=0, high=np.inf, shape=(1,), dtype=np.float32)
        
        # Dictionary to map actions to motor steps
        self._action_to_motor_step = lambda action: (1, action - self.max_steps) if action > self.max_steps else (-1, self.max_steps - action)
        
        self.truncated = False
        
        assert render_mode is None or render_mode in self.metadata["render_modes"]
        self.render_mode = render_mode
        
        
        """
        If human-rendering is used, `self.window` will be a reference
        to the window that we draw to. `self.clock` will be a clock that is used
        to ensure that the environment is rendered at the correct framerate in
        human-mode. They will remain `None` until human-mode is used for the
        first time.
        """
        self.window = None
        self.clock = None
        
    def _get_obs(self):
        """
        Get the current observation of the environment.

        :return: The current observation of the environment.
        """
        return self.spark_counter
        
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
        # in self.sparks_positions

        # filter out -1 and sort the positions
        relevant_sparks = sorted(spark for spark in self.sparks_positions if spark != -1)

        # count the number of sparks within range
        sparks_in_range = sum(abs(relevant_sparks[i] - relevant_sparks[i+1]) < self.heat_affected_zone for i in range(len(relevant_sparks) - 1))

        # check if wire breaks
        if sparks_in_range >= 2:
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
            
            self.sparks_positions.append(spark_y)
            
            self.sparks_frame.append((spark_x , spark_y))  # Add spark to the list of sparks in the current frame
            
            # Check if the wire is broken
            self.is_wire_broken = np.random.rand() < self._get_wire_break_conditional_probability()
            
            if self.is_wire_broken:
                print(self.sparks_positions)
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
                self.sparks_positions.append(-1) # -1 means no spark


        else:
            self.time_counter += 1
            self.time_counter_global += 1
            self.sparks_positions.append(-1) # -1 means no spark
        
    def _unwind_wire(self):
        """
        Unwind the wire by the unwinding speed. This affects the position of the sparks in the wire.
        """       
        # add delta to all the spark positions
        for i in range(len(self.sparks_positions)):
            if self.sparks_positions[i] != -1:
                self.sparks_positions[i] += self.unwinding_speed 
            if self.sparks_positions[i] > self.workpiece_height:
                self.sparks_positions[i] = -1
            
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
    
    def _render_frame(self):
        self.display.draw()

    def reset(self): # TODO CHECK THE SEED RESET
        
        self.workpiece_position = self.workpiece_start
        self.wire_position = self.wire_start
        self.time_counter = 0
        self.time_counter_global = 0
        self.spark_counter = 0
        self.time_step_count= 0
        self.sparks_positions = deque([-1] * self.dissipation_time, maxlen=self.dissipation_time)
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
        

class Display:
    def __init__(self, environment):
        self.environment = environment
        self.win_width = 1280
        self.win_height = 720
        self.wire_width = 300 # wire width in pixels
        self.wire_height = self.win_height
        self.workpiece_width = self.win_width - self.environment.workpiece_position
        self.vertical_downscale = 0.05
        self.workpiece_height = self.environment.workpiece_height * self.vertical_downscale
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

        workpiece_rect = pygame.Rect(self.environment.workpiece_position, self.win_height/2 - self.workpiece_height/2, self.workpiece_width, self.workpiece_height)        
        
        pygame.draw.rect(self.screen, (150, 150, 150), workpiece_rect)
        
        for x, y in self.environment.sparks_frame:
            spark_height =  5
            spark_width = abs(self.environment.workpiece_position - self.environment.wire_position)  # Width of the spark is the distance between the wire and the workpiece
            spark_rect = pygame.Rect(x - spark_width/2, self.win_height/2 - self.workpiece_height/2 + y*self.vertical_downscale - spark_height/2, spark_width, spark_height)
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
        
        
        self.clock.tick(self.environment.metadata["render_fps"])
        font = pygame.font.SysFont('Arial', 20)
        
        t2 = pygame.time.get_ticks()
        
        fps = 1000/(t2 - self.environment.t1)
        text = font.render('FPS: ' + str(int(fps)), True, (255, 255, 255))
        self.screen.blit(text, (0, 0))
        self.environment.t1 = t2
        
        #now the same but with the distance between the wire and the workpiece
        average_gap = sum(self.environment.average_gap)/len(self.environment.average_gap)
        text2 = font.render('Gap distance (um): ' + str(int(average_gap)), True, (255, 255, 255))
        position2 = (0, 20)
        self.screen.blit(text2, position2)
        
        # now the same but with the average speed of the wire
        average_speed = sum(self.environment.average_speed)/len(self.environment.average_speed)
        average_speed = average_speed * 60
        position4 = (0, 40)
        text4 = font.render('Average speed (mm/min):  ' + str(int(average_speed)), True, (255, 255, 255))
        self.screen.blit(text4, position4)
        

        pygame.display.update()
        self.check_for_events()
                    
    def check_for_events(self):
        for event in pygame.event.get():  
            if event.type == pygame.QUIT: 
                pygame.quit()
                sys.exit()
            
class Q_learning_actor:
    def __init__(self, env, learning_rate = 0.01, initial_epsilon = 1, epsilon_decay = 0.99, min_epsilon = 0.01, gamma = 0.99):
        self.learning_rate = learning_rate
        self.env = env
        self.epsilon = initial_epsilon
        self.epsilon_decay = epsilon_decay
        self.min_epsilon = min_epsilon
        self.gamma = gamma
        self.q_table = {}
        
    def get_action(self, obs: int) -> int:
        
        if np.random.random() < self.epsilon or obs not in self.q_table:
            # Explore
            return np.random.randint(0, 2*self.env.max_steps + 1)
        else:
            return int(np.argmax(self.q_table[obs]))
        
    def update(self, obs: int, action: int, reward: float, terminated: bool, next_obs: int):
        if obs not in self.q_table:
            self.q_table[obs] = np.zeros(2*self.env.max_steps + 1)
        if next_obs not in self.q_table:
            self.q_table[next_obs] = np.zeros(2*self.env.max_steps + 1)
        self.q_table[obs][action] += self.learning_rate * (reward + self.gamma * np.max(self.q_table[next_obs]) - self.q_table[obs][action])
        
    def decay_epsilon(self):
        self.epsilon = max(self.epsilon * self.epsilon_decay, self.min_epsilon)

class PID_actor:
    def __init__(self, env):
        self.environment = env
        
    
    def get_action(self, obs: int) -> int:
        if obs < 5:
            return 2
        else:
            return 0
        
    def update(self, obs: int, action: int, reward: float, terminated: bool, next_obs: int):
        pass
    def decay_epsilon(self):
        pass
        
def main():
    # Initializing Environment
    env = WireEdmEnv()
    # # Initializing Display and setting it for the Environment
    # display = Display(env)
    # env.set_display(display)
    
    N_episodes = 2000
    agent = Q_learning_actor(env)
    agent = PID_actor(env)
    reward_list = []
    for episode in range(N_episodes):
        obs, info = env.reset()
        done = False
        total_reward = 0
        while not done:
            action = agent.get_action(obs)
            next_obs, reward, terminated, truncated, info = env.step(action)
            total_reward += reward
            agent.update(obs, action, reward, terminated, next_obs)
            
            done = terminated or truncated
            
            obs = next_obs
        reward_list.append(total_reward)

        # for i in sorted(agent.q_table):
        #     motion = np.argmax(agent.q_table[i])
        #     if motion > env.max_steps:
        #         motion_str = "Right"
        #     if motion < env.max_steps:
        #         motion_str = "Left"
        #     if motion == env.max_steps:
        #         motion_str = "Still"
        #     print(i, motion_str)
        
        print ("Episode: ", episode, "Total reward: ", total_reward)
        agent.decay_epsilon()
        
    # save reward list as a csv file
    np.savetxt("reward_list_PID_3.csv", reward_list, delimiter=",")
    
    # save q_table as a pickle file
    import pickle
    with open("q_table_PID_QL.pickle", "wb") as f:
        pickle.dump(agent.q_table, f)
        f.close()
    
if __name__ == '__main__':
    
    main()
