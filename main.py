import time
from ai_camera import IMX500Detector
from gpiozero import DistanceSensor, Button, LED
import pyttsx4
import I2C_LCD_driver
import RPi.GPIO as GPIO

# Initialize hardware
sensor = DistanceSensor(echo=24, trigger=23, max_distance=2)  # 5 meters max
engine = pyttsx4.init()
mylcd = I2C_LCD_driver.lcd()
button1 = Button(20)
led1 = LED(21)

# Camera setup
print("Starting camera...")
camera = IMX500Detector()
camera.start(show_preview=True)
print("Camera started with live preview.")

# Constants
DETECTION_CONFIDENCE_THRESHOLD = 0.60
ULTRASONIC_TRIGGER_DISTANCE_INCHES = 20

# Mode state: 0 = Blind Mode (speaker), 1 = Deaf Mode (LCD)
mode = 0  # default to Blind Mode

# Utility functions
def speak(text):
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"Speech error: {e}")

def display_lcd(line1, line2=""):
    try:
        mylcd.lcd_clear()
        scroll_speed = 0.3  # seconds per scroll step
        pause_duration = 2  # how long to wait before/after scrolling

        def scroll_text(text, row):
            scroll_text = text + " " * 16
            for i in range(len(scroll_text) - 15):
                mylcd.lcd_display_string(scroll_text[i:i+16], row)
                time.sleep(scroll_speed)

        if len(line1) <= 16:
            mylcd.lcd_display_string(line1, 1)
        else:
            scroll_text(line1, 1)

        if line2:
            if len(line2) <= 16:
                mylcd.lcd_display_string(line2, 2)
            else:
                scroll_text(line2, 2)

        if len(line1) > 16 or len(line2) > 16:
            time.sleep(pause_duration)

    except Exception as e:
        print(f"LCD error: {e}")

def get_distance_inches():
    try:
        distance_cm = sensor.distance * 100
        return round(distance_cm / 2.54, 2)
    except Exception as e:
        print(f"Ultrasonic sensor error: {e}")
        return 0

def toggle_mode():
    global mode
    mode = 1 - mode  # Toggle between 0 and 1
    if mode == 0:
        display_lcd("Switched to", "BLIND mode")
        speak("Switched to blind mode")
    else:
        display_lcd("Switched to", "DEAF mode")
        speak("Switched to deaf mode")
    time.sleep(1.5)
    mylcd.lcd_clear()

# Bind button to toggle mode
button1.when_pressed = toggle_mode

# Main loop
try:
    print("Starting main loop...")
    while True:
        distance_in = get_distance_inches()
        distance_ft = round(distance_in / 12, 2)
        print(f"Distance: {distance_in} inches")

        if distance_in > ULTRASONIC_TRIGGER_DISTANCE_INCHES:
            detections = camera.get_detections()
            labels = camera.get_labels()

            detected_objects = []

            for detection in detections:
                label = labels[int(detection.category)]
                confidence = detection.conf

                if confidence >= DETECTION_CONFIDENCE_THRESHOLD:
                    print(f"{label} detected with {confidence:.2f} confidence!")
                    detected_objects.append(label)

            if detected_objects:
                detected_objects = detected_objects
                detected_objects_str = ', a '.join(detected_objects)
                summary = f"Looks like there may be: a {detected_objects_str} about {distance_ft} feet in front of you."

                if mode == 0:  # Blind Mode
                    speak(summary)
                else:  # Deaf Mode
                    display_lcd(f"{detected_objects_str}", f"{distance_in:.1f}\" away")

                led1.on()
            else:
                if mode == 1:
                    display_lcd(f"Dist: {distance_in:.1f}\"", "No detection")
                led1.off()
        else:
            if mode == 1:
                display_lcd(f"Dist: {distance_in:.1f}\"", "Too close")
            led1.off()

        time.sleep(2)

except KeyboardInterrupt:
    print("Interrupted by user. Cleaning up...")
    camera.stop()
    GPIO.cleanup()
    mylcd.lcd_clear()
    print("Shutdown complete.")
