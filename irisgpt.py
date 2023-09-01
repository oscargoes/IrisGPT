import speech_recognition as sr
import pyttsx3

# Initialize globals and Python TTS engine
engine = pyttsx3.init()
engine.setProperty('volume', 1.0)
WAKE_WORD = "Iris"
LOG = "log.txt"

class Iris:
    def __init__(self):
        self.rec = sr.Recognizer()
        self.mic = sr.Microphone()

    def hear(self):
        try:
            with self.mic as source:
                print("Waiting for command.")
                self.rec.adjust_for_ambient_noise(source)
                self.rec.dynamic_energy_threshold = 3000
                audio = self.rec.listen(source, timeout=1.0)
                command = self.rec.recognize_google(audio)
                return command.lower()
        except sr.WaitTimeoutError:
            pass
        except sr.UnknownValueError:
            pass
        except sr.RequestError:
            print("Network error.")

    def output(self, text):
        f = open(LOG, "a")
        f.write(text + "\n")
        f.close

def main():
    i = Iris()
    while(True):
        text = i.hear()
        print(text)
        print(type(text))
        if text is not None:
            i.output(text)
            engine.say(text)
            engine.runAndWait()
        
        if text == "go to sleep":
            break

if __name__ == "__main__":
    main()