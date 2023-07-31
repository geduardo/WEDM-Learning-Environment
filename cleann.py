import sys
import time
from collections import deque
import numpy as np
import pygame

class Environment:

    def __init__(self, time_between_movements, min_step_size, workpiece_distance_increment, crater_diameter, spark_ignition_time, heat_dissipation_time, T_timeout, T_rest, piece_height, unwinding_speed, target_distance, start_position_wire=0, start_position_workpiece=100):
        self.start_position_workpiece = start_position_workpiece
        self.start_position_wire = start_position_wire
        self.time_between_movements = time_between_movements
        self.min_step_size = min_step_size
        self.workpiece_distance_increment = workpiece_distance_increment
        self.piece_height = piece_height
        self.unwinding_speed = unwinding_speed
        self.renewal_time = int(self.piece_height / self.unwinding_speed)
        self.T_timeout = T_timeout
        self.T_rest = T_rest
        self.target_distance = target_distance
        self.crater_diameter = crater_diameter
        self.workpiece_position = start_position_workpiece
        self.wire_position = start_position_wire
        self.spark_ignition_time = spark_ignition_time
        self.heat_dissipation_time = heat_dissipation_time
        self.time_counter = 0
        self.time_counter_global = 0
        self.sparks_list = deque([0] * self.renewal_time, maxlen=self.renewal_time)
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
        self.display = display

    def _get_lambda(self, wire_position, workpiece_position):
        d = wire_position - workpiece_position
        return np.log(2) / (0.48 * d * d - 3.69 * d + 14.05)

    def _get_spark_conditional_probability(self, lambda_param, time_from_voltage_rise):
        return lambda_param

    def _get_wire_break_conditional_probability(self):
        relevant_sparks = sorted((spark for spark in self.sparks_positions_list if spark != -1))
        sparks_in_range = sum((abs(relevant_sparks[i] - relevant_sparks[i + 1]) < self.crater_diameter for i in range(len(relevant_sparks) - 1)))
        if sparks_in_range >= 3:
            return 1
        else:
            return 0

    def _generate_sparks(self):
        if np.random.rand() < self._get_spark_conditional_probability(self._get_lambda(self.wire_position, self.workpiece_position), self.time_counter):
            self.sparks_list.append(1)
            self.spark_counter += 1
            self.workpiece_position += self.workpiece_distance_increment
            spark_y = np.random.randint(0, self.piece_height)
            self.sparks_positions_list.append(spark_y)
            self.sparks.append(((self.wire_position + self.workpiece_position) / 2, spark_y, 2000))
            self.time_counter = 0
            self.time_counter_global += 1
            self.is_wire_broken = np.random.rand() < self._get_wire_break_conditional_probability()
            
            if self.is_wire_broken:
                print('Wire broken!')
            self.is_wire_colliding = self.wire_position >= self.workpiece_position
            if self.is_wire_colliding:
                print('Collision!')
            self.is_target_distance_reached = self.workpiece_position >= self.target_distance
            if self.is_target_distance_reached:
                print('Target distance reached!')
                print('It took ', self.time_counter_global / 1000000, ' seconds to reach the target distance.')
            for _ in range(self.T_rest + self.spark_ignition_time):
                self.time_counter_global += 1
                self.sparks_list.append(0)
                self.sparks_positions_list.append(-1)
        else:
            self.sparks_list.append(0)
            self.sparks_positions_list.append(-1)
            self.time_counter += 1
            self.time_counter_global += 1
        if self.time_counter_global % 1667 == 0 and self.display is not None:
            self.display.clock.tick(60)
            self.t2 = time.time()
            self.display.draw()
            self.FPS = 1 / (self.t2 - self.t1)
            self.t1 = time.time()
        self.sparks = [(x, y, lifespan - 1) for (x, y, lifespan) in self.sparks if lifespan > 1]

    def _move_motor(self, action):
        (direction, number_of_steps) = action
        for _ in range(number_of_steps):
            self.wire_position = self.wire_position + direction * self.min_step_size
            self._generate_sparks()

    def is_done(self):
        return self.is_wire_broken or self.is_target_distance_reached or self.is_wire_colliding

    def step(self, action):
        self.spark_counter = 0
        if not isinstance(action, tuple):
            raise ValueError('The action must be a tuple.')
        self._move_motor(action)
        for _ in range(self.time_between_movements):
            self._generate_sparks()
            if self.is_done():
                break

    def reset(self):
        self.workpiece_position = self.start_position_workpiece
        self.wire_position = self.start_position_wire
        self.time_counter = 0
        self.time_counter_global = 0
        self.sparks_list = deque([0] * self.renewal_time, maxlen=self.renewal_time)
        self.is_wire_broken = False

    def get_environment_state(self):
        return {'workpiece_position': self.workpiece_position, 'wire_position': self.wire_position, 'sparks_list': self.sparks_list, 'time_counter': self.time_counter, 'time_counter_global': self.time_counter_global, 'is_wire_broken': self.is_wire_broken}

class Display:

    def __init__(self, environment):
        self.environment = environment
        self.win_width = 1000
        self.win_height = 800
        self.wire_width = 100
        self.wire_height = self.win_height
        self.workpiece_width = self.win_width - self.environment.workpiece_position
        self.init_pygame()
        
    def init_pygame(self):
        pygame.init()
        self.screen = pygame.display.set_mode((self.win_width, self.win_height))
        pygame.display.set_caption('Wire EDM Simulation')
        self.clock = pygame.time.Clock()

    def draw(self):
        self.screen.fill((50, 50, 50))
        wire_rect = pygame.Rect(self.environment.wire_position - self.wire_width, 0, self.wire_width, self.wire_height)
        pygame.draw.rect(self.screen, (200, 100, 0), wire_rect)
        workpiece_rect = pygame.Rect(self.environment.workpiece_position, self.win_height / 2 - self.environment.piece_height / 2, self.workpiece_width, self.environment.piece_height)
        pygame.draw.rect(self.screen, (150, 150, 150), workpiece_rect)
        for (x, y, _) in self.environment.sparks:
            spark_height = 10
            spark_width = abs(self.environment.workpiece_position - self.environment.wire_position)
            spark_rect = pygame.Rect(x - spark_width / 2, self.win_height / 2 - self.environment.piece_height / 2 + y - spark_height / 2, spark_width, spark_height)
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
        font = pygame.font.SysFont('Arial', 20)
        text = font.render('FPS: ' + str(int(self.environment.FPS)), True, (255, 255, 255))
        position = (0, 0)
        self.screen.blit(text, position)
        pygame.display.update()

    def PID_actor(self):
        if self.environment.spark_counter < 3:
            self.environment.step((1, 1))
        else:
            self.environment.step((-1, 1))

    def run(self):
        while not self.environment.is_done():
            for event in pygame.event.get():  # this line will get all events in the event queue
                if event.type == pygame.QUIT:  # if the event is a QUIT event, then you will stop the game loop
                    pygame.quit()
                    sys.exit()
            self.PID_actor()
            self.environment.history.append(self.environment.get_environment_state())


def main():
    time_between_movements = 1000
    min_step_size = 1
    workpiece_distance_increment = 0.05
    crater_diameter = 50
    spark_ignition_time = 3
    heat_dissipation_time = 100
    T_timeout = 5000
    T_rest = 10
    piece_height = 400
    unwinding_speed = 1000
    target_distance = 1500
    start_position_wire = 20
    start_position_workpiece = 300
    env = Environment(time_between_movements, min_step_size, workpiece_distance_increment, crater_diameter, spark_ignition_time, heat_dissipation_time, T_timeout, T_rest, piece_height, unwinding_speed, target_distance, start_position_wire, start_position_workpiece)
    display = Display(env)
    env.set_display(display)
    display.run()
    print('Average distance between workpiece and wire: ', sum([state['workpiece_position'] - state['wire_position'] for state in env.history if state['wire_position'] > start_position_workpiece]) / len([state['workpiece_position'] - state['wire_position'] for state in env.history if state['wire_position'] > start_position_workpiece]))
if __name__ == '__main__':
    main()