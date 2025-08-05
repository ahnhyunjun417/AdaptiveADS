from __future__ import print_function

import carla
import time
import math

from agents.navigation.basic_agent import BasicAgent
from srunner.autoagents.autonomous_agent import AutonomousAgent
from srunner.scenariomanager.carla_data_provider import CarlaDataProvider

def get_entry_point():
    return 'NpcAgent'


class NpcAgent(AutonomousAgent):
    def setup(self, path_to_conf_file):
        self._route_assigned = False
        self._agent = None
        self._driver_monitoring_data = None
        self._abnormal_action_start_time = 0
        self._emergency_stop_target = None

    def sensors(self):
        sensors = [
            {'type': 'sensor.camera.rgb', 'x': 0.7, 'y': -0.4, 'z': 1.60, 'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0,
             'width': 300, 'height': 200, 'fov': 100, 'id': 'Left'},
            {'type': 'sensor.camera.dms', 'x': 0.0, 'y': 0.0, 'z': 0.0, 'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0,
             'width': 300, 'height': 200, 'fov': 90, 'id': 'DMS'},
        ]

        return sensors

    def run_step(self, input_data, timestamp):
        """
        Execute one step of navigation.
        """
        control = carla.VehicleControl()
        control.steer = 0.0
        control.throttle = 0.0
        control.brake = 0.0
        control.hand_brake = False
        
        if not self._agent:
            hero_actor = None
            for actor in CarlaDataProvider.get_world().get_actors():
                if 'role_name' in actor.attributes and actor.attributes['role_name'] == 'hero':
                    hero_actor = actor
                    break
            if hero_actor:
                self._agent = BasicAgent(hero_actor)

            return control

        if self._driver_monitoring_data is not None:
            driver_state = self.driver_state_detection(self._driver_monitoring_data)
            if driver_state['abnormal']:
                abnormal_action = driver_state['control']
                if abnormal_action is not None:
                    return abnormal_action
            else:
                self._abnormal_action_start_time = None
                self._emergency_stop_target = None
        
        if not self._route_assigned:
            if self._global_plan:
                plan = []

                for transform, road_option in self._global_plan_world_coord:
                    wp = CarlaDataProvider.get_map().get_waypoint(transform.location)
                    plan.append((wp, road_option))

                self._agent._local_planner.set_global_plan(plan)  # pylint: disable=protected-access
                self._route_assigned = True
        
        else:
            control = self._agent.run_step()
        
        return control
    
    def driver_state_detection(self, driver_monitoring_data):
        driver_state = {}
        driver_state['abnormal'] = True
        driver_state['control'] = None

        tag = driver_monitoring_data[0]
        if tag == 'drowsiness':
            driver_state['control'] = self.drowsiness_control()
        elif tag == 'distracted':
            driver_state['control'] = self.distracted_control()
        else:
            driver_state['abnormal'] = False
            driver_state['control'] = None

        return driver_state

    def distracted_control(self, speed_limit=3.0):
        ## speed limit is in m/s
        control = carla.VehicleControl()
        control.steer = 0.0
        control.throttle = 0.0
        control.brake = 0.0
        control.hand_brake = False

        current_speed = self.get_speed()
        speed_error = speed_limit - current_speed
        if speed_error < 0:
            control.brake = min(abs(speed_error) * 0.5, 1.0)
            return control

        return None

    def drowsiness_control(self):
        control = carla.VehicleControl()
        control.steer = 0.0
        control.throttle = 0.0
        control.brake = 0.2
        control.hand_brake = False
        
        if self._abnormal_action_start_time is None:
            self._abnormal_action_start_time = time.time()
            
        elif (time.time() - self._abnormal_action_start_time) > 3.0:
            if self._emergency_stop_target is None:
                self.set_emergency_target_location()

            ## Velocity calculation
            current_speed = self.get_speed()

            ## Distance from current location to target location
            current_location = self._agent._vehicle.get_location()
            distance = current_location.distance(self._emergency_stop_target)
            
            if current_speed < 1.0 and distance < 1.5: ## Stop the vehicle when it satisfies two conditions
                control.throttle = 0.0
                control.brake = 1.0
            else:
                control.steer = self.compute_steer(current_location, self._emergency_stop_target)
            
            return control
        
        return None
    
    def get_speed(self):
        current_velocity = self._agent._vehicle.get_velocity()
        speed = (current_velocity.x ** 2 + current_velocity.y ** 2 + current_velocity.z ** 2) ** 0.5
        return speed

    def set_emergency_target_location(self):
        current_location = self._agent._vehicle.get_location()
        waypoint = self._agent._map.get_waypoint(current_location)
        self._emergency_stop_target = waypoint.transform.location + waypoint.transform.get_right_vector() * 3.0

    def compute_steer(self, current, target):
        dx = target.x - current.x
        dy = target.y - current.y
        angle = math.atan2(dy, dx)
        yaw = math.radians(self._agent._vehicle.get_transform().rotation.yaw)

        return max(min((angle - yaw) * 0.5, 0.5), -1.0)
