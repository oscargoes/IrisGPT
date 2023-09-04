import speech_recognition as sr
import pyttsx3
from datetime import date
import cv2 as cv
import os
from dotenv import load_dotenv
import openai
import azure.ai.vision as sdk

# Initialize globals and Python TTS engine
global frame
engine = pyttsx3.init()
engine.setProperty("volume", 1.0)
voices = engine.getProperty("voices")
engine.setProperty("voice", voices[1].id)
WAKE_WORD = "iris"
LOG = "log.txt"
IMG = "frame.jpg"

# Initialize keywords for sphinx to focus on
keywords = [("iris", 1), ("Iris", 1),]
is_listening = False

# Initialize OpenAI
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize Azure Computer Vision API
service_options = sdk.VisionServiceOptions(os.getenv("AZURE_VISION_ENDPOINT"),
                                           os.getenv("AZURE_VISION_KEY"))

analysis_options = sdk.ImageAnalysisOptions()
analysis_options.features = (
    sdk.ImageAnalysisFeature.DENSE_CAPTIONS |
    sdk.ImageAnalysisFeature.TEXT
)
analysis_options.language = "en"
analysis_options.gender_neutral_caption = False

# Wait to hear wake word and listen for command when wake detected
def hear(rec, audio):
    try:
        print("word detected")
        # Use sphinx stt to reduce use of google stt
        text = rec.recognize_sphinx(audio, keyword_entries=keywords)
        # print(text)
        text = text.lower()
        if WAKE_WORD in text:
            print("listening")
            # engine.say("How can I help you?")
            # engine.runAndWait()
            listen()
        else:
            pass
        
    except sr.WaitTimeoutError:
        pass
    except sr.UnknownValueError:
        print("Sphinx could not understand audio")
    except sr.RequestError as e:
        print("Sphinx error; {0}".format(e))

# Listens for command after wake word and calls interpreter
def listen():
    try:
        command = rec.listen(mic)
        text = rec.recognize_google(command)
        print("interpreting command")
        interpret(text.lower())
    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand audio")
    except sr.RequestError as e:
        print("Could not request results from Google Speech Recognition service; {0}".format(e))

# Takes in text from speech and determines which command to run
def interpret(text):
    with open(LOG, "a") as f:
        f.write("User: " + text + "\n")
        speak = "I do not know that command yet"

        if text == "go to sleep":
            speak = "going to sleep"
            f.write("Iris: " + speak + "\n")
            global is_listening
            is_listening = False
        elif text == "say hello":
            speak = "hello, how are you?"
            f.write("Iris: " + speak + "\n")
        elif text == "how are you":
            speak = "fine, thank you"
            f.write("Iris: " + speak + "\n")
        elif text == "analyze image":
            cv.imwrite("frame.jpg", frame)
            vision_source = sdk.VisionSource(filename=IMG)
            image_analyzer = sdk.ImageAnalyzer(service_options, vision_source, analysis_options)
            result = image_analyzer.analyze()
            if result.reason == sdk.ImageAnalysisResultReason.ANALYZED:

                print(" Image height: {}".format(result.image_height))
                print(" Image width: {}".format(result.image_width))
                print(" Model version: {}".format(result.model_version))

                if result.dense_captions is not None:
                    print(" Dense Captions:")
                    for caption in result.dense_captions:
                        print("   '{}', {}, Confidence: {:.4f}".format(caption.content, caption.bounding_box, caption.confidence))

                if result.text is not None:
                    print(" Text:")
                    for line in result.text.lines:
                        points_string = "{" + ", ".join([str(int(point)) for point in line.bounding_polygon]) + "}"
                        print("   Line: '{}', Bounding polygon {}".format(line.content, points_string))
                        for word in line.words:
                            points_string = "{" + ", ".join([str(int(point)) for point in word.bounding_polygon]) + "}"
                            print("     Word: '{}', Bounding polygon {}, Confidence {:.4f}"
                                .format(word.content, points_string, word.confidence))

                result_details = sdk.ImageAnalysisResultDetails.from_result(result)
                print(" Result details:")
                print("   Image ID: {}".format(result_details.image_id))
                print("   Result ID: {}".format(result_details.result_id))
                print("   Connection URL: {}".format(result_details.connection_url))
                print("   JSON result: {}".format(result_details.json_result))

            else:

                error_details = sdk.ImageAnalysisErrorDetails.from_result(result)
                print(" Analysis failed.")
                print("   Error reason: {}".format(error_details.reason))
                print("   Error code: {}".format(error_details.error_code))
                print("   Error message: {}".format(error_details.message))            
        else:
            # try:
            #     conn = http.client.HTTPSConnection('*.cognitiveservices.azure.com')
            #     conn.request("POST", "/computervision/imageanalysis:analyze?api-version=2023-02-01-preview&%s" % params, "{body}", headers)
            #     response = conn.getresponse()
            #     data = response.read()
            #     print(data)
            #     conn.close()
            # except Exception as e:
            #     print("[Errno {0}] {1}".format(e.errno, e.strerror))

            # response = openai.ChatCompletion.create(
            #     model="gpt-3.5-turbo",
            #     messages=[
            #         {
            #             "role": "user",
            #             "content": text
            #         }
            #     ],
            #     temperature=1,
            #     max_tokens=128,
            #     top_p=1,
            #     frequency_penalty=0,
            #     presence_penalty=0
            # )
            f.write("Iris: " + text + "\n")

        f.close()
        # engine.say(speak)
        # engine.runAndWait()


# Initialize video feed
videoCapture = cv.VideoCapture(0, cv.CAP_DSHOW)
videoCapture.set(cv.CAP_PROP_FRAME_WIDTH, 1920)
videoCapture.set(cv.CAP_PROP_FRAME_HEIGHT, 1080)

# Initialize speech recognizer and microphone
rec = sr.Recognizer() 
mic = sr.Microphone()
with mic as source:
    # Adjust mic input for background noise
    rec.adjust_for_ambient_noise(source, duration=2)
    rec.dynamic_energy_threshold = True

# Run hear function in a new thread to allow main function to run while listening in background
stopper = rec.listen_in_background(mic, hear)
is_listening = True

# Time stamp onto log
today = str(date.today())
with open(LOG, "a") as f:
    f.write("--- Started on: " + today + " ---\n")
    f.close()

while(True):
    ret, frame = videoCapture.read()
    if not ret:
        break
    
    # cv.imshow("input", frame)

    if cv.waitKey(1) == 27:
        stopper()
        engine.stop()
        break

    if is_listening:
        # print("CL")
        pass
    else:
        print("stopping listening and program")
        stopper()
        engine.stop()
        break

cv.destroyAllWindows() 
videoCapture.release()
with open(LOG, "a") as f:
    f.write("--- Ended conversation ---\n\n")
    f.close()