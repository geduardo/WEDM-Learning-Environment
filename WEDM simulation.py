import numpy as np
from collections import deque

class Environment:
    """A class representing a simulated environment for wire erosion. All units are in micrometers and microseconds."""

    def __init__(self, time_between_movements, max_step_size, min_step_size, workpiece_distance_increment, spark_ignition_time, T_timeout, T_rest, h, v_u, renewal_time, target_distance, start_position_wire=0, start_position_workpiece=100):
        """
        Initialize the environment with the given parameters.

        :param time_between_movements: Time between motor movements.
        :param max_step_size: Maximum step size for motor movements.
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
        self.workpiece_position = start_position_workpiece
        self.wire_position = start_position_wire
        self.time_between_movements = time_between_movements
        self.max_step_size = max_step_size
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
    
    def _get_conditional_probability_of_sparking_at_given_microsecond(self, lambda_param, time_from_voltage_rise):
        """ Calculate the conditional probability of sparking at a given microsecond,
        given that it has not sparked yet since the last voltage rise."""
        
        # In the case of the exponential distribution, the conditional
        # probability is just lambda
        return lambda_param
    
    
    def _sample_ignition_delay_time(self, wire_position, workpiece_position):
        """
        Sample ignition delay time based on the distance between the wire and the workpiece.

        :param wire_position: Wire position.
        :param workpiece_position: Workpiece position.
        :return: Ignition delay time in microseconds.
        """
        lambda_param = self._get_lambda(wire_position, workpiece_position)
        t_d = int(np.random.exponential(scale=1 / lambda_param))
        return t_d

    def _sample_wire_break(self):
        """
        TODO
        """

    def _move_motor(self, action):
        """
        Move the motor in the desired direction and number of steps.

        :param action: Tuple containing the direction and number of steps.
        """
        direction, number_of_steps = action
        self.wire_position += direction * number_of_steps * self.min_step_size    
        self.time_counter = 0

    def _generate_sparks(self):
        """
        Generate sparks in the wire based on the ignition delay time and wire break probability.
        """
        
        while self.time_counter < self.time_between_movements:
            ignition_delay_time = self._sample_ignition_delay_time()
            
            # Update the time counters and sparks_list during ignition delay
            if self.time_counter + ignition_delay_time > self.time_between_movements:
                ignition_delay_time = self.time_between_movements - self.time_counter

            self.time_counter += ignition_delay_time
            self.time_counter_global += ignition_delay_time
            self.sparks_list.extend([0] * ignition_delay_time)

            self._sample_wire_break()
            if self.is_wire_broken:
                break

            self.time_counter += self.spark_ignition_time
            self.time_counter_global += self.spark_ignition_time
            self.sparks_list.append(1)
            self.sparks_list.extend([0] * (self.spark_ignition_time - 1))

            self.workpiece_position += self.workpiece_distance_increment

    def step(self, action):
        """
        Execute a step in the environment based on the given action.

        :param action: Tuple containing the direction and number of steps.
        :raises ValueError: If the action is not a tuple.
        """
        if not isinstance(action, tuple):
            raise ValueError("The action must be a tuple.")
        self._move_motor(action)
        self._generate_sparks()

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
        self.workpiece_position = 3/self.k_param
        self.wire_position = 0
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
            "time_counter": self.time_counter,
            "time_counter_global": self.time_counter_global,
            "is_wire_broken": self.is_wire_broken
        }