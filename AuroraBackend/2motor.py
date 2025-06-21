import RPi.GPIO as GPIO
from time import sleep

# Left motor connections
left_direction_pin = 20
left_pulse_pin = 21
# Right motor connections
right_direction_pin = 19
right_pulse_pin = 26

# Define motor directions
cw_direction = 0  # Clockwise (for one motor)
ccw_direction = 1  # Counter-clockwise (for one motor)

# Set up GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(left_direction_pin, GPIO.OUT)
GPIO.setup(left_pulse_pin, GPIO.OUT)
GPIO.setup(right_direction_pin, GPIO.OUT)
GPIO.setup(right_pulse_pin, GPIO.OUT)

def set_motor_speed(pulse_pin, speed_percentage):
    # Calculate the pulse delay for the speed based on percentage (0-100%)
    max_delay = 0.005  # Adjust the max speed (lower this value for faster movement)
    delay = max_delay * (1 - (speed_percentage / 100))
    return delay

def move_motors(left_dir, right_dir, speed_percentage):
    GPIO.output(left_direction_pin, left_dir)
    GPIO.output(right_direction_pin, right_dir)
    delay = set_motor_speed(left_pulse_pin, speed_percentage)
    
    while True:  # Keep motors running until a new command is issued
        GPIO.output(left_pulse_pin, GPIO.HIGH)
        GPIO.output(right_pulse_pin, GPIO.HIGH)
        sleep(delay)
        GPIO.output(left_pulse_pin, GPIO.LOW)
        GPIO.output(right_pulse_pin, GPIO.LOW)
        sleep(delay)

# Main control loop
try:
    while True:
        command = input("Enter command (w = forward, s = backward, a = left, d = right, q = quit): ")
        speed = float(input("Enter speed (0-100): "))
        
        if command == 'w':
            move_motors(cw_direction, ccw_direction, speed)  # Forward: left motor CW, right motor CCW
        elif command == 's':
            move_motors(ccw_direction, cw_direction, speed)  # Backward: left motor CCW, right motor CW
        elif command == 'a':
            move_motors(ccw_direction, ccw_direction, speed)  # Turn left: both motors CCW
        elif command == 'd':
            move_motors(cw_direction, cw_direction, speed)  # Turn right: both motors CW
        elif command == 'q':
            break
        else:
            print("Invalid command")
        
        GPIO.cleanup()  # Clean up GPIO after every movement

except KeyboardInterrupt:
    pass
finally:
    GPIO.cleanup()
