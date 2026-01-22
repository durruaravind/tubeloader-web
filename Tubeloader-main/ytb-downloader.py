from tkinter import *
import yt_dlp
from datetime import datetime
import os

window = Tk()
window.geometry("720x480")
window.config(bg="ROYAL BLUE")
window.title("tubeloader")
window.resizable(0,0)
script_dir = os.path.dirname(os.path.abspath(__file__))
youtube_logo = PhotoImage(file = os.path.join(script_dir, "youtube-logo.png"))
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
    if(filetypevalue_mp4.get() == 1 and filetypevalue_mp3.get() == 1):
        audio_download()
        video_download()
    else:
        if(filetypevalue_mp4.get() == 1):
            video_download()
        if(filetypevalue_mp3.get() == 1):
            audio_download()

# code for downloading the mp4 video at highest resolution
def video_download():
    try:
        url = str(Video_Link.get())
        path_mp4 = str(Mp4_path.get())
        
        ydl_opts = {
            'format': 'best[ext=mp4]',
            'outtmpl': os.path.join(path_mp4, '%(title)s.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'Unknown')
        
        Label(window, text = "MP4 Video Download Completed!", font = ("Roboto", 14, "bold"), bg = "ROYAL BLUE", fg = "WHITE").place(x = 200, y = 400)
        Label(window, text = f"Saved to: {path_mp4}", font = ("Roboto", 10, "bold"), bg = "ROYAL BLUE", fg = "YELLOW").place(x = 150, y = 425)

        # writing the details of the download in history.txt as a record
        with open(os.path.join(script_dir, "history.txt"), "a") as f:
            now = datetime.now()
            dateandtime = now.strftime("%d/%m/%Y %H:%M:%S")
            f.write("MP4        ")
            f.write(title)
            f.write("       ")
            f.write(dateandtime)
            f.write("\n")
    except Exception as e:
        Label(window, text = f"Error: {str(e)}", font = ("Roboto", 12, "bold"), bg = "ROYAL BLUE", fg = "RED").place(x = 200, y = 400)

# code for downlading the mp3 audio
def audio_download():
    try:
        url = str(Video_Link.get())
        path_mp3 = str(Mp3_path.get())
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': os.path.join(path_mp3, '%(title)s.%(ext)s'),
            'ffmpeg_location': r'C:\ffmpeg\ffmpeg-master-latest-win64-gpl\bin',
            'quiet': False,
            'no_warnings': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'Unknown')
        
        Label(window, text = "MP3 Audio Download Completed!", font = ("Roboto", 14, "bold"), bg = "ROYAL BLUE", fg = "WHITE").place(x = 200, y = 400)
        Label(window, text = f"Saved to: {path_mp3}", font = ("Roboto", 10, "bold"), bg = "ROYAL BLUE", fg = "YELLOW").place(x = 150, y = 425)

        # writing the details of the download in history.txt as a record
        with open(os.path.join(script_dir, "history.txt"), "a") as f:
            now = datetime.now()
            dateandtime = now.strftime("%d/%m/%Y %H:%M:%S")
            f.write("MP3        ")
            f.write(title)
            f.write("       ")
            f.write(dateandtime)
            f.write("\n")
    except Exception as e:
        Label(window, text = f"Error: {str(e)}", font = ("Roboto", 12, "bold"), bg = "ROYAL BLUE", fg = "RED").place(x = 200, y = 400)

# Download button
Button(window, text = "DOWNLOAD", font = ("Roboto", 24, "bold"), bg = "LIGHTBLUE", command = getfiletype).place(x= 240, y = 275)
window.mainloop()