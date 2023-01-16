#!/usr/bin/env python

import carb
from pegasus_isaac.logic.vehicles.vehicle import Vehicle
from pegasus_isaac.mavlink_interface import MavlinkInterface
from pegasus_isaac.logic.sensors import Barometer, IMU, Magnetometer, GPS

from omni.isaac.core.controllers import BaseController

class Quadrotor(Vehicle):

    def __init__(
        self, 
        stage_prefix: str="quadrotor",  
        usd_file: str="",
        world=None,
        init_pos=[0.0, 0.0, 0.07], 
        init_orientation=[0.0, 0.0, 0.0, 1.0]
    ):
        
        # Initiate the Vehicle
        super().__init__(stage_prefix, usd_file, world, init_pos, init_orientation)

        # Create the sensors that a quadrotor typically has
        self._barometer = Barometer(altitude_home=488.0)                # Check
        self._imu = IMU()                                               # Check
        self._magnetometer = Magnetometer(47.397742, 8.545594)          # Check
        self._gps = GPS(47.397742, 8.545594, origin_altitude=488.0)     # Check
        
        # Create a mavlink interface for getting data
        self._mavlink = MavlinkInterface('tcpin:localhost:4560')
        
        # Add callbacks to the physics engine to update the sensors every timestep
        self._world.add_physics_callback(self._stage_prefix + "/barometer", self.update_barometer_sensor)
        self._world.add_physics_callback(self._stage_prefix + "/imu", self.update_imu_sensor)
        self._world.add_physics_callback(self._stage_prefix + "/magnetometer", self.update_magnetometer_sensor)
        self._world.add_physics_callback(self._stage_prefix + "/gps", self.update_gps_sensor)

        # Add a callback to start/stop the mavlink streaming once the play/stop button is hit
        self._world.add_timeline_callback(self._stage_prefix + "/start_stop_sim", self.sim_start_stop)

        self.total_time = 0

    def update_barometer_sensor(self, dt: float):
        self._mavlink.update_bar_data(self._barometer.update(self._state, dt))

    def update_imu_sensor(self, dt: float):
        self._mavlink.update_imu_data(self._imu.update(self._state, dt))

    def update_magnetometer_sensor(self, dt: float):
        self._mavlink.update_mag_data(self._magnetometer.update(self._state, dt))

    def update_gps_sensor(self, dt: float):
        self._mavlink.update_gps_data(self._gps.update(self._state, dt))

    def sim_start_stop(self, event):
        """
        Callback that is called every time there is a timeline event such as starting/stoping the simulation
        """
        
        # If the start/stop button was pressed, then start/stop mavlink communication
        if self._world.is_playing():
            self._mavlink.start_stream()
            pass

        if self._world.is_stopped():
            self._mavlink.stop_stream()
            pass

    def apply_forces(self, dt: float):
        """
        Method that computes and applies the forces to the vehicle in
        simulation based on the motor speed. This method must be implemented
        by a class that inherits this type
        """

        self._mavlink.mavlink_update()

        # Get the force to apply to the body frame from mavlink
        forces_z = self._mavlink._rotor_data.input_force_reference

        # Get the articulation corresponding to the vehicle
        #articulation = self._world.dc_interface.get_articulation(self._stage_prefix + "/vehicle/body")
        #dof_ptr = self._world.dc_interface.find_articulation_dof(articulation, "rotor0/RevoluteJoin")
        #carb.log_warn(dof_ptr)

        #kp = 0.5
        #kd = 1.0
        #z_ref = 3.0
        #x_ref = 4.0
        #y_ref = 0.0
        
        # Get the body of the vehicle
        body = self._world.dc_interface.get_rigid_body(self._stage_prefix  + "/vehicle/body")

        self._world.dc_interface.apply_body_force(body, carb._carb.Float3([0.0, 0.0, forces_z[0]]), carb._carb.Float3([ 0.13, -0.22, 0.023]), False)
        self._world.dc_interface.apply_body_force(body, carb._carb.Float3([0.0, 0.0, forces_z[1]]), carb._carb.Float3([-0.13,  0.20, 0.023]), False)
        self._world.dc_interface.apply_body_force(body, carb._carb.Float3([0.0, 0.0, forces_z[2]]), carb._carb.Float3([ 0.13,  0.22, 0.023]), False)
        self._world.dc_interface.apply_body_force(body, carb._carb.Float3([0.0, 0.0, forces_z[3]]), carb._carb.Float3([-0.13, -0.20, 0.023]), False)

        #carb.log_warn(self._state.position[0])

        #if self.total_time > 3.0:
        #    self._world.dc_interface.apply_body_force(body, carb._carb.Float3([
        #        2.0 * (x_ref - self._state.position[0]) + kd * (0-0 - self._state.linear_velocity[0]),
        #        kp * (y_ref - self._state.position[1]) + kd * (0-0 - self._state.linear_velocity[1]),
        #        kp * (z_ref - self._state.position[2]) + kd * (0-0 - self._state.linear_velocity[2]) + (9.81 * 1.5)]), carb._carb.Float3([0.0, 0.0, 0.0]), False)

        # Apply force to each rotor
        #for i in range(4):

            # Get the rotor frame interface of the vehicle (this will be the frame used to get the position, orientation, etc.)
        #    rotor = self._world.dc_interface.get_rigid_body(self._stage_prefix  + "/vehicle/rotor" + str(i))

            # Apply the force in Z on the rotor frame
        #    self._world.dc_interface.apply_body_force(rotor, carb._carb.Float3([0.0, 0.0, forces_z[i]]), carb._carb.Float3([ 0.0, 0.0, 0.0]), False)

        self.total_time += dt