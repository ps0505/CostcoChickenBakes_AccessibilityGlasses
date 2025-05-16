import pyttsx4


engine = pyttsx4.init()


def speak(outtxt):
    engine.say(str(outtxt))
    engine.runAndWait()