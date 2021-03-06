#!/usr/bin/env python

import rospy
from std_msgs.msg import Bool
from dbw_mkz_msgs.msg import ThrottleCmd, SteeringCmd, BrakeCmd, SteeringReport
from geometry_msgs.msg import TwistStamped
import math
import csv

from twist_controller import Controller


#: bool: if True, write select attributes to csv file.
WRITE_CSV_LOG = False



'''
You can build this node only after you have built (or partially built) the `waypoint_updater` node.

You will subscribe to `/twist_cmd` message which provides the proposed linear and angular velocities.
You can subscribe to any other message that you find important or refer to the document for list
of messages subscribed to by the reference implementation of this node.

One thing to keep in mind while building this node and the `twist_controller` class is the status
of `dbw_enabled`. While in the simulator, its enabled all the time, in the real car, that will
not be the case. This may cause your PID controller to accumulate error because the car could
temporarily be driven by a human instead of your controller.

We have provided two launch files with this node. Vehicle specific values (like vehicle_mass,
wheel_base) etc should not be altered in these files.

We have also provided some reference implementations for PID controller and other utility classes.
You are free to use them or build your own.

Once you have the proposed throttle, brake, and steer values, publish it on the various publishers
that we have created in the `__init__` function.

'''



class DBWNode(object):
    def __init__(self):
        rospy.init_node('dbw_node', log_level=rospy.INFO)

        vehicle_mass = rospy.get_param('~vehicle_mass', 1736.35)
        fuel_capacity = rospy.get_param('~fuel_capacity', 13.5)
        brake_deadband = rospy.get_param('~brake_deadband', .1)
        decel_limit = rospy.get_param('~decel_limit', -5)
        accel_limit = rospy.get_param('~accel_limit', 1.)
        # Distance from front tires to rear tires
        wheel_radius = rospy.get_param('~wheel_radius', 0.2413)
        # Ratio between turn of steering wheel and turn of wheel
        wheel_base = rospy.get_param('~wheel_base', 2.8498)
        steer_ratio = rospy.get_param('~steer_ratio', 14.8)
        max_lat_accel = rospy.get_param('~max_lat_accel', 3.)
        max_steer_angle = rospy.get_param('~max_steer_angle', 8.)

        self.steer_pub = rospy.Publisher('/vehicle/steering_cmd',
                                         SteeringCmd, queue_size=1)
        self.throttle_pub = rospy.Publisher('/vehicle/throttle_cmd',
                                            ThrottleCmd, queue_size=1)
        self.brake_pub = rospy.Publisher('/vehicle/brake_cmd',
                                         BrakeCmd, queue_size=1)

        # TODO: Create `Controller` object
        self.controller = Controller(
            vehicle_mass,
            wheel_radius,
            accel_limit,
            decel_limit,
            wheel_base,
            steer_ratio,
            0.1,
            max_lat_accel,
            max_steer_angle)

        # TODO: Subscribe to all the topics you need to

        # Made up of a Header (with a time stamp, and frame_id), and Twist
        # (linear and angular velocity vectors)
        rospy.Subscriber('/twist_cmd', TwistStamped, self.proposed_cb)
        rospy.Subscriber('/current_velocity', TwistStamped, self.current_cb)
        # Simulator Publishes wheter or not the drive by wire is enabled (only
        # publish if it is)
        rospy.Subscriber('/vehicle/dbw_enabled', Bool, self.dbw_enabled_cb)

        self.proposed_linear_vel = None
        self.proposed_angular_vel = None
        # self.proposed_time = None

        self.current_linear_vel = None
        self.current_anuglar_vel = None

        # obtain current time from /twist_cmd.header.nsecs (or secs)
        # the time stamp in /current_velocity is empty
        self._time_nsecs = None

        self.dbw_enabled = False

        if WRITE_CSV_LOG:
            # NOTE: this file is created at  /home/<user>/.ros/log/
            rospy.loginfo("writing csv log at : {}".format("/home/<user>/.ros/log/log.csv"))
            self._logfile = open("log/log.csv", "w")
            fieldnames = ["time_nsecs",
                          "current_linear_vel",
                          "proposed_angular_vel",
                          "proposed_linear_vel",
                          "throttle", "brake", "steering",
                          "throttle_p",
                          "throttle_i",
                          "throttle_d"]

            self._logwriter = csv.DictWriter(self._logfile,
                                             fieldnames=fieldnames)
            self._logwriter.writeheader()

        self.loop()

    def loop(self):
        rate = rospy.Rate(50)  # 50Hz

        while not rospy.is_shutdown():
            # TODO: Get predicted throttle, brake, and steering using `twist_controller`
            # You should only publish the control commands if dbw is enabled

            if (self.proposed_linear_vel is not None
                    and self.proposed_angular_vel is not None
                    and self.current_linear_vel is not None):

                throttle, brake, steering = self.controller.control(
                    self.proposed_linear_vel,
                    self.proposed_angular_vel,
                    self.current_linear_vel,
                    self.dbw_enabled)

                if self.dbw_enabled:
                    self.publish(throttle, brake, steering)
                    if WRITE_CSV_LOG:
                        self._logwriter.writerow(
                            {"time_nsecs": self._time_nsecs,
                             "current_linear_vel": self.current_linear_vel,
                             "proposed_linear_vel": self.proposed_linear_vel,
                             "proposed_angular_vel": self.proposed_angular_vel,
                             "throttle": throttle,
                             "brake": brake,
                             "steering": steering,
                             "throttle_p": self.controller.throttle_pid.last_error,
                             "throttle_i": self.controller.throttle_pid.int_val,
                             "throttle_d": self.controller.throttle_pid.derivative,})

            rate.sleep()

        if WRITE_CSV_LOG:
            self._logfile.close()

    def publish(self, throttle, brake, steer):
        tcmd = ThrottleCmd()
        tcmd.enable = True
        tcmd.pedal_cmd_type = ThrottleCmd.CMD_PERCENT
        tcmd.pedal_cmd = throttle
        self.throttle_pub.publish(tcmd)

        scmd = SteeringCmd()
        scmd.enable = True
        scmd.steering_wheel_angle_cmd = steer
        self.steer_pub.publish(scmd)

        bcmd = BrakeCmd()
        bcmd.enable = True
        bcmd.pedal_cmd_type = BrakeCmd.CMD_TORQUE
        bcmd.pedal_cmd = brake
        self.brake_pub.publish(bcmd)

    def proposed_cb(self, msg):
        self.proposed_linear_vel = msg.twist.linear.x
        self.proposed_angular_vel = msg.twist.angular.z
        # self.proposed_time = msg.header.stamp
        self._time_nsecs = msg.header.stamp.nsecs

    def current_cb(self, msg):
        self.current_linear_vel = msg.twist.linear.x
        # self.current_angular_vel = msg.twist.angular.z
        # self.current_time = msg.header.stamp

    def dbw_enabled_cb(self, msg):
        self.dbw_enabled = msg.data


if __name__ == '__main__':
    DBWNode()
