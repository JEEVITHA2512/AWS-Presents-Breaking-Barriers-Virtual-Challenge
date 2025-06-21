from gpiozero import DigitalOutputDevice
from time import sleep

# Left motor connections
left_direction_pin = DigitalOutputDevice(20)
left_pulse_pin = DigitalOutputDevice(21)

# Right motor connections
right_direction_pin = DigitalOutputDevice(19)
right_pulse_pin = DigitalOutputDevice(26)

# Define motor directions
cw_direction = 0  # Clockwise
ccw_direction = 1  # Counter-clockwise

def set_motor_speed(pulse_pin, speed_percentage):
    max_delay = 0.005
    delay = max_delay * (1 - (speed_percentage / 100))
    return delay

def move_motors(left_dir, right_dir, speed_percentage):
    left_direction_pin.value = left_dir
    right_direction_pin.value = right_dir
    delay = set_motor_speed(left_pulse_pin, speed_percentage)
    
    while True:
        left_pulse_pin.on()
        right_pulse_pin.on()
        sleep(delay)
        left_pulse_pin.off()
        right_pulse_pin.off()
        sleep(delay)

try:
    while True:
        command = input("Enter command (w = forward, s = backward, a = left, d = right, q = quit): ")
        speed = float(input("Enter speed (0-100): "))
        
        if command == 'w':
            move_motors(cw_direction, ccw_direction, speed)
        elif command == 's':
            move_motors(ccw_direction, cw_direction, speed)
        elif command == 'a':
            move_motors(ccw_direction, ccw_direction, speed)
        elif command == 'd':
            move_motors(cw_direction, cw_direction, speed)
        elif command == 'q':
            break
        else:
            print("Invalid command")

except KeyboardInterrupt:
    pass
finally:
    print("Program ended.")
