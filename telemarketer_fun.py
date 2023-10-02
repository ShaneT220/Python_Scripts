"""
@author: Shane Tomasello

@note: This project was mainly for fun to see the limitations of OpenAI and to explore the possibility of having OpenAI handle telemarketers in a funny way.
"""

import pyaudio
import math
import struct
import wave
import time
import os
import openai
import pyttsx3

Threshold = 10

SHORT_NORMALIZE = (1.0/32768.0)
chunk = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
swidth = 2

TIMEOUT_LENGTH = 5

f_name_directory = '<Output_Location>'

openai.api_key = "<OpenAI_Key>"

preface = "Pretend you’re an 80 year old elderly man named Edward . Respond to the below text. If the below text mentions that they want a credit card, then give a fake credit card number that could be plausible. If the speaker does not ask for a credit card number, do not give one. Do not mention it is fake. Do not hesitate or think you are being scammed. If there are any numbers, spell them out."

class Recorder:

    @staticmethod
    def rms(frame):
        count = len(frame) / swidth
        format = "%dh" % (count)
        shorts = struct.unpack(format, frame)

        sum_squares = 0.0
        for sample in shorts:
            n = sample * SHORT_NORMALIZE
            sum_squares += n * n
        rms = math.pow(sum_squares / count, 0.5)

        return rms * 1000

    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=FORMAT,
                                  channels=CHANNELS,
                                  rate=RATE,
                                  input=True,
                                  output=True,
                                  frames_per_buffer=chunk)

    def record(self):
        print('Noise detected, recording beginning')
        rec = []
        current = time.time()
        end = time.time() + TIMEOUT_LENGTH

        while current <= end:

            data = self.stream.read(chunk)
            if self.rms(data) >= Threshold: end = time.time() + TIMEOUT_LENGTH

            current = time.time()
            rec.append(data)
        self.write(b''.join(rec))

    def write(self, recording):
        filename = 'audio_recording.wav'

        filename = os.path.join(f_name_directory, filename)

        wf = wave.open(filename, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(self.p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(recording)
        wf.close()
        print('Written to file: {}'.format(filename))
        print('Transcribing audio...')
        self.transcribe_audio(filename)

    def transcribe_audio(self, filename):
        audio_file = open(filename, "rb")
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
        current = transcript
        lols = f"""{preface}

        Respond to the following text given the context above.
        {current}
        """
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=lols,
            temperature=0.7,
            max_tokens=2000,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )['choices'][0]['text']
        self.speak(response)
        print(response)
        time.sleep(5)
        print('Returning to listening')
        

    def speak(self, text):
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        engine.setProperty('voice', voices[1].id)
        rate = engine.getProperty('rate')
        engine.setProperty('rate', rate - 30)
        engine.say(text)
        engine.runAndWait()
        engine.stop()

    def listen(self):
        print('Listening beginning')
        while True:
            input = self.stream.read(chunk)
            rms_val = self.rms(input)
            if rms_val > Threshold:
                self.record()

a = Recorder()

a.listen()
