from gpiozero import DistanceSensor, Button, LED
import time
import pyttsx4
import I2C_LCD_driver
import RPi.GPIO as GPIO
import threading

# Initialize hardware
sensor = DistanceSensor(echo=24, trigger=23, max_distance=5)
engine = pyttsx4.init()
mylcd = I2C_LCD_driver.lcd()
button1 = Button(20)
led1 = LED(21)


# Lock to prevent overlapping actions
is_busy = threading.Lock()

# Speak asynchronously
def speak_async(text):
    def _speak():
        try:
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print(f"Speech error: {e}")
    threading.Thread(target=_speak, daemon=True).start()

# Display info on LCD
def display_distance(distance_in):
    mylcd.lcd_clear()
    line1 = f"You are {distance_in}in"
    mylcd.lcd_display_string(line1[:16], 1)  # Ensure it fits
    mylcd.lcd_display_string("from an object", 2)
    time.sleep(5)
    mylcd.lcd_clear()

# Main measurement function
def measure_distance():
    if is_busy.locked():
        print("Still processing previous measurement...")
        return
    
    def process():
        with is_busy:
            distance_cm = int(sensor.distance * 100)
            distance_in = round(distance_cm / 2.54, 2)
            print(f"{distance_cm} cm | {distance_in} in")
            speak_async(f'You are {distance_in} inches from an object')
            display_distance(distance_in)

    threading.Thread(target=process, daemon=True).start()

# Bind button press
button1.when_pressed = measure_distance

# Keep program alive
try:
    print("Waiting for button press... Press Ctrl+C to exit.")
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    GPIO.cleanup()
    mylcd.lcd_clear()
    print("Interrupted and ended.")
