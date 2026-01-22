from tkinter import *
from pytube import YouTube
from datetime import datetime
import os

window = Tk()
window.geometry("720x480")
window.config(bg="ROYAL BLUE")
window.title("tubeloader")
window.resizable(0,0)
youtube_logo = PhotoImage(file = "youtube-logo.png")
window.iconphoto(False, youtube_logo)

Label(window, text = " YOUTUBE VIDEO DOWNLOADER ", font = ("Courier", 20, "bold"), bg = "WHITE").pack(padx = 5, pady = 50)
Video_Link = StringVar()
Mp4_path = StringVar()
Mp3_path = StringVar()
Label(window, text = " URL             ", font = ("Roboto", 14, "bold"), bg = "WHITE").place(x= 30, y = 175)
Label(window, text = " MP4 PATH ", font = ("Roboto", 14, "bold"), bg = "WHITE").place(x= 30, y = 125)
Label(window, text = " MP3 PATH ", font = ("Roboto", 14, "bold"), bg = "WHITE").place(x= 30, y = 150)
Entry_Link = Entry(window, width = 60, font = 24, textvariable = Video_Link).place(x = 150, y = 175)
Mp4_Link = Entry(window, width = 60, font = 24, textvariable = Mp4_path).place(x = 150, y = 125)
Mp3_Link = Entry(window, width = 60, font = 24, textvariable = Mp3_path).place(x = 150, y = 150)

# code for creating the checkbox form
filetypevalue_mp4 = IntVar()
filetype_mp4 = Checkbutton(text = "MP4", variable = filetypevalue_mp4).place(x = 300, y = 225)
filetypevalue_mp3 = IntVar()
filetype_mp3 = Checkbutton(text = "MP3", variable = filetypevalue_mp3).place(x = 350, y = 225)

# according to the value entered in checkbox, appropriate commands are excecuted
def getfiletype():
    if(filetypevalue_mp4.get() == 1 & filetypevalue_mp3.get() == 1):
        audio_download()
        video_download()
    else:
        if(filetypevalue_mp4.get() == 1):
            video_download()
        if(filetypevalue_mp3.get() == 1):
            audio_download()

# code for downloading the mp4 video at highest resolution
def video_download():
    video_url = YouTube(str(Video_Link.get()))
    video = video_url.streams.get_highest_resolution()
    path_mp4 = str(Mp4_path.get())
    mp4output = video.download(path_mp4)
    basemp4, ext = os.path.splitext(mp4output)
    new_mp4file = basemp4 + '.mp4'
    os.rename(mp4output, new_mp4file)
    Label(window, text = "MP4 Video Download Completed!", font = ("Roboto", 14, "bold"), bg = "ROYAL BLUE", fg = "WHITE").place(x = 200, y = 400)
    Label(window, text = "CHECK YOUR PROJECT FOLDER", font = ("Roboto", 14, "bold"), bg = "ROYAL BLUE", fg = "WHITE").place(x = 200, y = 425)

    # writing the details of the download in history.txt as a record
    with open("history.txt", "a") as f:
        now = datetime.now()
        dateandtime = now.strftime("%d/%m/%Y %H:%M:%S")
        f.write("MP4        ")
        f.write(video.title)
        f.write("       ")
        f.write(dateandtime)
        f.write("       Thumbnail  ")
        f.write(video_url.thumbnail_url)
        f.write("\n")

# code for downlading the mp3 audio
def audio_download():
    video_url = YouTube(str(Video_Link.get()))
    audio = video_url.streams.filter(only_audio=True).first()
    path_mp3 = str(Mp3_path.get())
    mp3output = audio.download(path_mp3)
    basemp3, ext = os.path.splitext(mp3output)
    new_mp3file = basemp3 + '.mp3'
    os.rename(mp3output, new_mp3file)
    Label(window, text = "MP3 Audio Download Completed!", font = ("Roboto", 14, "bold"), bg = "ROYAL BLUE", fg = "WHITE").place(x = 200, y = 400)
    Label(window, text = "CHECK YOUR PROJECT FOLDER", font = ("Roboto", 14, "bold"), bg = "ROYAL BLUE", fg = "WHITE").place(x = 200, y = 425)

    # writing the details of the download in history.txt as a record
    with open("history.txt", "a") as f:
        now = datetime.now()
        dateandtime = now.strftime("%d/%m/%Y %H:%M:%S")
        f.write("MP3        ")
        f.write(audio.title)
        f.write("       ")
        f.write(dateandtime)
        f.write("       Thumbnail  ")
        f.write(video_url.thumbnail_url)
        f.write("\n")

# Download button
Button(window, text = "DOWNLOAD", font = ("Roboto", 24, "bold"), bg = "LIGHTBLUE", command = getfiletype).place(x= 240, y = 275)
window.mainloop()