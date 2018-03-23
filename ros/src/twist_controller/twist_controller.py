
GAS_DENSITY = 2.858
ONE_MPH = 0.44704


class Controller(object):
    def __init__(self,
            vehicle_mass=None,
            fuel_capacity=None,
            brake_deadband=None,
            decel_limit=None,
            accel_limit=None,
            wheel_radius=None,
            wheel_base=None,
            steer_ratio=None,
            max_lat_accel=None,
            max_steer_angle=None):

        # TODO: Implement
        self.throttle =  None
        self.steer = None
        self.brake = None

        self.vehicle_mass = vehicle_mass
        self.fuel_capacity = fuel_capacity
        self.brake_deadband = brake_deadband
        self.decel_limit = decel_limit
        self.accel_limit = accel_limit
        self.wheel_radius = wheel_radius
        self.wheel_base = wheel_base
        self.steer_ratio = steer_ratio
        self.max_lat_accel = max_lat_accel
        self.max_steer_angle = max_steer_angle

    def control(self, *args, **kwargs):
        # TODO: Change the arg, kwarg list to suit your needs
        # Return throttle, brake, steer
        # return 1., 0., 0.

        # TODO: Replace test controls with control mechanism
        self._test_control()

        return self.throttle, self.brake, self.steer

    def _test_control(self):
        import random
        self.throttle = 1.
        self.brake = 0.
        self.steer = random.random() * 10
        # rospy.logwarn("setting test control: t{} {} {}")
