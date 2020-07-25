import tkinter as tk
from tkinter import font  as tkfont
import numpy as np
from PIL import Image, ImageTk
import cv2
import pyaudio
import wave
import moviepy.editor as mp
import moviepy.video.fx.all as vfx
from pychorus import create_chroma, find_chorus
import os
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from pytube import YouTube
                
class PowerHourApp(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.title_font = tkfont.Font(family='Helvetica', size=18, weight="bold", slant="italic")
        self.name = ""
        self.videos = []
        self.BeerClip = None
        self.IntroClip = None

        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (WelcomePage, IntroPage, BeerClipPage, VideoPage):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame

            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("WelcomePage")

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()
        
    def initName(self, name):
        if name != "":
            self.name = name
        else:
            self.name = "Unnamed Playlist"
            
    def deleteVideos(self):
        dir_name = os.getcwd()
        items = os.listdir(dir_name)
        for item in items:
            if item.startswith(self.name) or item.startswith("BeerClip"):
                continue
            if item.endswith(".mp4") or item.endswith(".wav"):
                os.remove(os.path.join(dir_name, item))
                
    def downloadVid(self, name):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--incognito")
        driver = webdriver.Chrome(ChromeDriverManager().install(),options=options)

        wait = WebDriverWait(driver, 3)
        presence = EC.presence_of_element_located
        visible = EC.visibility_of_element_located
        searchAdd = " Official Music Video"

        # Navigate to url with video being appended to search_query
        video = name + searchAdd
        driver.get("https://www.youtube.com/results?search_query=" + video)

        # play the video
        wait.until(visible((By.ID, "video-title")))
        link = driver.find_element_by_id("video-title")
        url = link.get_attribute("href")
        video = YouTube(str(url))
        video.streams.filter(progressive=True, file_extension='mp4')
        #resolutions = ["720p", "480p", "360p", "240p", "144p"]
        #for r in resolutions:
        vid = video.streams.get_by_resolution("720p")
        if vid != None:
            vid.download(filename=name)
                #break
                
    def getChorus(self, name):
        try:
            video = mp.VideoFileClip(name + ".mp4")
            video.audio.write_audiofile(name + ".wav")
            chroma, song_wav_data, sr, song_length_sec = create_chroma(name + ".wav")
            chorus_start = find_chorus(chroma, sr, song_length_sec, 15)
            if chorus_start is None:
                return
            newclip = video.subclip(chorus_start-10, chorus_start + 50)
            self.videos.append(newclip)
            #newclip.write_videofile(name + " chorus.mp4")
        except:
            pass
                
    def addVid(self, name):
        self.downloadVid(name)
        self.getChorus(name)
        
    def publish(self):
        final = mp.concatenate_videoclips(self.videos,transition=self.BeerClip, method='compose')
        final.write_videofile(self.name + " final.mp4")


class WelcomePage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        
        label = tk.Label(self, text="Welcome to the Power Hour Creator!", font=controller.title_font)
        label.pack(side="top", fill="x", pady=10)
        
        label2 = tk.Label(self, text="Please enter the name of your Power Hour Playlist")
        label2.pack(side="top", fill="x", pady=10)
        
        entry = tk.Entry(self)
        entry.pack()

        button = tk.Button(self, text="Continue", command=lambda: self.continueButton(entry.get(),"IntroPage"))
        button.pack()
    
    def continueButton(self, modelName, pageName):
        self.controller.initName(modelName)
        self.controller.show_frame(pageName)
        

class recorder:
    def __init__(self, controller, final_name):
        self.final_name = final_name
        self.controller = controller
        self.window = tk.Toplevel(self.controller)  #Makes main window
        self.window.wm_title("Record Intro")
        self.window.config(background="#FFFFFF")
        
        self.imageFrame = tk.Frame(self.window, width=600, height=500)
        self.imageFrame.grid(row=0, column=0, padx=10, pady=2, columnspan=2)

        #Capture video frames
        self.lmain = tk.Label(self.imageFrame)
        self.lmain.grid(row=0, column=0)
        self.name = 'Intro.mp4'
        self.cap = cv2.VideoCapture(0)
        self.fourcc = cv2.VideoWriter_fourcc(*'MP4V')
        self.out = cv2.VideoWriter(self.name, self.fourcc, 30.0, (640,480))

        self.filename = "recorded.wav"
        # set the chunk size of 1024 samples
        self.chunk = 1024
        # sample format
        self.FORMAT = pyaudio.paInt16
        # mono, change to 2 if you want stereo
        self.channels = 2
        # 30000 samples per second
        self.sample_rate = 30000
        # initialize PyAudio object
        self.p = pyaudio.PyAudio()
        self.seconds = 10

        # open stream object as input & output
        self.stream = self.p.open(format=self.FORMAT,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk)
        self.frames = []

        self.start = False

        self.stop = False
        
        startButton = tk.Button(self.window, text="Start",command=lambda: self.setStart())
        startButton.grid(row=600, column=0, padx=10, pady=2)
        stopButton = tk.Button(self.window, text="Stop",command=lambda: self.setStop())
        stopButton.grid(row=600, column=1, padx=10, pady=2)
        self.show()
        
    def setStart(self):
        self.start = True

    def setStop(self):
        self.stop = True
        
    def show(self):
        ret, frame = self.cap.read()
        if self.start:
            self.out.write(frame)
            data = self.stream.read(self.chunk)
            self.frames.append(data)
        frame = cv2.flip(frame, 1)
        cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
        img = Image.fromarray(cv2image)
        imgtk = ImageTk.PhotoImage(image=img)
        self.lmain.imgtk = imgtk
        self.lmain.configure(image=imgtk)
        if self.stop:
            self.cap.release()
            self.out.release()
            cv2.destroyAllWindows()

            self.stream.stop_stream()
            self.stream.close()
            # terminate pyaudio object
            self.p.terminate()
            # save audio file
            # open the file in 'write bytes' mode
            wf = wave.open(self.filename, "wb")
            # set the channels
            wf.setnchannels(self.channels)
            # set the sample format
            wf.setsampwidth(self.p.get_sample_size(self.FORMAT))
            # set the sample rate
            wf.setframerate(self.sample_rate)
            # write the frames as bytes
            wf.writeframes(b"".join(self.frames))
            # close the file
            wf.close()

            #try:
            audioclip = mp.AudioFileClip("recorded.wav")
            videoclip = mp.VideoFileClip(self.name)
            #audioclip.set_duration(videoclip)
            videoclip2 = videoclip.set_audio(audioclip)
            #new_videoclip = (videoclip2.fx(vfx.accel_decel, new_duration=1))
            #new_videoclip.write_videofile("out.mp4")
            videoclip2.write_videofile(self.final_name + ".mp4")
            #except:
                #print("Error")
                #pass
            self.window.destroy()
            self.window.update()
            return
        self.lmain.after(10,self.show)


class IntroPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="Please record your intro video", font=controller.title_font)
        label.pack(side="top", fill="x", pady=10)
        startRecord = tk.Button(self, text="Start Recording", command=lambda: self.record())
        startRecord.pack()
        button3 = tk.Button(self, text="Continue", command=lambda: self.controller.show_frame("BeerClipPage"))
        button3.pack()
        
    def record(self):
        introClip = recorder(self.controller, self.controller.name)
    

class BeerClipPage(tk.Frame):
    
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="Please record your transition video", font=controller.title_font)
        label.pack(side="top", fill="x", pady=10)
        startRecord = tk.Button(self, text="Start Recording", command=lambda: self.record())
        startRecord.pack()
        button3 = tk.Button(self, text="Continue", command=lambda: self.controller.show_frame("VideoPage"))
        button3.pack()
        
    def record(self):
        self.controller.IntroClip = mp.VideoFileClip(self.controller.name + ".mp4")
        self.controller.videos.append(self.controller.IntroClip)
        beerClip = recorder(self.controller, "BeerClip")
        
class VideoPage(tk.Frame):
    
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="Upload video list", font=controller.title_font)
        label.pack(side="top", fill="x", pady=10)
        uploadButton = tk.Button(self, text="Upload", command=lambda: self.upload())
        uploadButton.pack()
        finishButton = tk.Button(self, text="Finish", command=lambda: self.finish())
        finishButton.pack()
    
    def upload(self):
        self.controller.BeerClip = mp.VideoFileClip("BeerClip.mp4")
        f = open("videos.txt", "r")
        for x in f:
            self.controller.addVid(x.rstrip())
        self.controller.publish()
            
    def finish(self):
        self.controller.deleteVideos()