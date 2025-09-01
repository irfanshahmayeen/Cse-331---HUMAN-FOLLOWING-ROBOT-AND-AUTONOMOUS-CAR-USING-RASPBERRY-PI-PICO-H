from machine import Pin, PWM
import utime

# Motor setup
Motor1_In1 = Pin(1, Pin.OUT)
Motor1_In2 = Pin(2, Pin.OUT)
Motor1_EN = PWM(Pin(0, Pin.OUT))
Motor2_In1 = Pin(4, Pin.OUT)
Motor2_In2 = Pin(5, Pin.OUT)
Motor2_EN = PWM(Pin(3, Pin.OUT))
Motor3_In1 = Pin(27, Pin.OUT)
Motor3_In2 = Pin(26, Pin.OUT)
Motor3_EN = PWM(Pin(28, Pin.OUT))
Motor4_In1 = Pin(21, Pin.OUT)
Motor4_In2 = Pin(20, Pin.OUT)
Motor4_EN = PWM(Pin(22, Pin.OUT))

# Set PWM frequency
Motor1_EN.freq(1000)
Motor2_EN.freq(1000)
Motor3_EN.freq(1000)
Motor4_EN.freq(1000)

# Ultrasonic sensor setup
trigger = Pin(17, Pin.OUT)
echo = Pin(16, Pin.IN)

# Servo setup
Mid = 1500000
Min = 1000000
Max = 2000000
servo = PWM(Pin(15))
servo.freq(50)
servo.duty_ns(Mid)

# Following parameters
TARGET_DISTANCE = 30  # Target following distance in cm
DISTANCE_TOLERANCE = 5  # Acceptable range around target distance
MAX_SPEED = 50000
FOLLOW_SPEED = 30000
TURNING_SPEED = 25000

def forward(speed):
    Motor1_In1.high()
    Motor1_In2.low()
    Motor2_In1.low()
    Motor2_In2.high()
    Motor3_In1.low()
    Motor3_In2.high()
    Motor4_In1.high()
    Motor4_In2.low()
    
    Motor1_EN.duty_u16(speed)
    Motor2_EN.duty_u16(speed)
    Motor3_EN.duty_u16(speed)
    Motor4_EN.duty_u16(speed)

def back(speed):
    Motor1_In1.low()
    Motor1_In2.high()
    Motor2_In1.high()
    Motor2_In2.low()
    Motor3_In1.high()
    Motor3_In2.low()
    Motor4_In1.low()
    Motor4_In2.high()
    
    Motor1_EN.duty_u16(speed)
    Motor2_EN.duty_u16(speed)
    Motor3_EN.duty_u16(speed)
    Motor4_EN.duty_u16(speed)
    
def right(speed):
    Motor1_In1.low()
    Motor1_In2.high()
    Motor2_In1.low()
    Motor2_In2.high()
    Motor3_In1.low()
    Motor3_In2.high()
    Motor4_In1.low()
    Motor4_In2.high()
    
    Motor1_EN.duty_u16(speed)
    Motor2_EN.duty_u16(speed)
    Motor3_EN.duty_u16(speed)
    Motor4_EN.duty_u16(speed)
    
def left(speed):
    Motor1_In1.high()
    Motor1_In2.low()
    Motor2_In1.high()
    Motor2_In2.low()
    Motor3_In1.high()
    Motor3_In2.low()
    Motor4_In1.high()
    Motor4_In2.low()
    
    Motor1_EN.duty_u16(speed)
    Motor2_EN.duty_u16(speed)
    Motor3_EN.duty_u16(speed)
    Motor4_EN.duty_u16(speed)

def stop():
    Motor1_In1.low()
    Motor1_In2.low()
    Motor2_In1.low()
    Motor2_In2.low()
    Motor3_In1.low()
    Motor3_In2.low()
    Motor4_In1.low()
    Motor4_In2.low()

def ultra():
    trigger.low()
    utime.sleep_us(2)
    trigger.high()
    utime.sleep_us(5)
    trigger.low()
    
    while echo.value() == 0:
        off = utime.ticks_us()
    
    while echo.value() == 1:
        on = utime.ticks_us()
        
    timepassed = on - off
    distance = (timepassed * 0.0343) / 2
    
    print(f"{distance:.1f} cm")
    return distance

def scan_for_object():
    """Scan the area and find the closest object"""
    # Check left
    servo.duty_ns(Min)
    utime.sleep(0.3)
    left_distance = ultra()
    
    # Check center
    servo.duty_ns(Mid)
    utime.sleep(0.3)
    center_distance = ultra()
    
    # Check right
    servo.duty_ns(Max)
    utime.sleep(0.3)
    right_distance = ultra()
    
    # Return to center position
    servo.duty_ns(Mid)
    
    # Return all distances and position of closest object
    min_distance = min(left_distance, center_distance, right_distance)
    
    if min_distance == left_distance:
        return {"left": left_distance, "center": center_distance, "right": right_distance, "position": "left"}
    elif min_distance == right_distance:
        return {"left": left_distance, "center": center_distance, "right": right_distance, "position": "right"}
    else:
        return {"left": left_distance, "center": center_distance, "right": right_distance, "position": "center"}

def follow_object():
    """Main function for object following behavior"""
    try:
        while True:
            scan_result = scan_for_object()
            
            # Print debug information
            print(f"Left: {scan_result['left']:.1f} cm, Center: {scan_result['center']:.1f} cm, Right: {scan_result['right']:.1f} cm")
            print(f"Closest object at: {scan_result['position']}")
            
            # Get the distance of the closest object
            if scan_result['position'] == 'left':
                closest_distance = scan_result['left']
            elif scan_result['position'] == 'right':
                closest_distance = scan_result['right']
            else:
                closest_distance = scan_result['center']
            
            # If no object is detected within the sensing range, stop
            if closest_distance > 150:
                print("No object detected within range, stopping")
                stop()
                continue
            
            # Follow object based on position and distance
            if scan_result['position'] == 'center':
                # If centered, adjust distance
                if abs(closest_distance - TARGET_DISTANCE) <= DISTANCE_TOLERANCE:
                    # At perfect following distance, stop
                    print("At target distance, stopping")
                    stop()
                elif closest_distance > TARGET_DISTANCE:
                    # Too far, move forward
                    print("Object centered but too far, moving forward")
                    forward(FOLLOW_SPEED)
                else:
                    # Too close, move backward
                    print("Object centered but too close, moving backward")
                    back(FOLLOW_SPEED)
            elif scan_result['position'] == 'left':
                # Turn left to center the object
                print("Object on left, turning left")
                left(TURNING_SPEED)
                utime.sleep(0.2)
            elif scan_result['position'] == 'right':
                # Turn right to center the object
                print("Object on right, turning right")
                right(TURNING_SPEED)
                utime.sleep(0.2)
            
            # Small delay between iterations
            utime.sleep(0.1)
            
    except KeyboardInterrupt:
        stop()
        print("Program stopped by user")

# Start following
if _name_ == "_main_":
    print("Object following mode activated")
    print(f"Target following distance: {TARGET_DISTANCE} cm")
    follow_object()
