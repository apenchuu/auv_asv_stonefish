#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray
import sys
import select
import termios
import tty

settings = termios.tcgetattr(sys.stdin)

msg = """
Control Your Blueboat!
---------------------------
Moving around:
        w
   a    s    d

SPACE : stop
q : quit

CTRL-C to quit
"""

class TeleopBlueboat(Node):
    def __init__(self):
        super().__init__('teleop_blueboat')
        self.publisher_ = self.create_publisher(Float64MultiArray, '/blueboat/setpoint/pwm', 10)
        self.speed = 1.0
        
        # Initial states
        self.cmd_starboard = 0.0 # Thruster 0 (Physically Left side based on Y=0.4)
        self.cmd_port = 0.0      # Thruster 1 (Physically Right side based on Y=-0.4)
        
        self.print_instructions()

    def print_instructions(self):
        print(msg)

    def getKey(self):
        tty.setraw(sys.stdin.fileno())
        rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
        if rlist:
            key = sys.stdin.read(1)
        else:
            key = ''
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
        return key

    def run(self):
        try:
            while True:
                key = self.getKey()
                if not key:
                    continue

                if key == 'w':
                    # Forward
                    self.cmd_starboard = self.speed
                    self.cmd_port = self.speed
                    print("\rForward", end="")
                elif key == 's':
                    # Backward
                    self.cmd_starboard = -self.speed
                    self.cmd_port = -self.speed
                    print("\rBackward", end="")
                elif key == 'a':
                    # Turn Left (CCW) -> Right Fwd (Port), Left Back (Starboard)
                    self.cmd_starboard = -self.speed
                    self.cmd_port = self.speed
                    print("\rLeft", end="")
                elif key == 'd':
                    # Turn Right (CW) -> Left Fwd (Starboard), Right Back (Port)
                    self.cmd_starboard = self.speed
                    self.cmd_port = -self.speed
                    print("\rRight", end="")
                elif key == ' ':
                    self.cmd_starboard = 0.0
                    self.cmd_port = 0.0
                    print("\rStop", end="")
                elif key == 'q':
                    break
                elif key == '\x03': # Ctrl-C
                    break
                
                # Publish
                msg_data = Float64MultiArray()
                msg_data.data = [float(self.cmd_starboard), float(self.cmd_port)]
                self.publisher_.publish(msg_data)
                
        except Exception as e:
            print(e)

        finally:
            msg_data = Float64MultiArray()
            msg_data.data = [0.0, 0.0]
            self.publisher_.publish(msg_data)
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)

def main(args=None):
    rclpy.init(args=args)
    teleop = TeleopBlueboat()
    teleop.run()
    teleop.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
