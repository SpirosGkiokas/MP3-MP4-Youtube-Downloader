#importing libs
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
import threading as th
import yt_dlp as ydl
from tkinter import messagebox
import os
import ctypes as ct
import json
import re
import subprocess
from data.exceptions import wrong_resolutions_mp4

#setting paths
dir_path = os.getcwd()
assets_path = os.path.join(dir_path, "Assets")
icon_path = os.path.join(assets_path, "mp3-mp4-downloader-icon.ico")
download_dir_path = os.path.expanduser("~/Downloads")
data_path = os.path.join(dir_path, "data")
ffmpeg_path = os.path.join(data_path, "ffmpeg", "bin")
ffmpeg_exe = os.path.join(ffmpeg_path, "ffmpeg.exe")
ffprobe_exe = os.path.join(ffmpeg_path, "ffprobe.exe")

# Inject into environment PATH
os.environ["PATH"] = ffmpeg_path + os.pathsep + os.environ["PATH"]

#taskbar icon
myappid = 'MP3-MP4 Youtube Downloader' 
ct.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

#setting starting app size
s_width = 1013
s_height = 920

#setting color vars
background_color_light = "#EAEAEA"
foreground_color_light = "#000511"
background_color_dark = "#252525"
foreground_color_dark = "#EBEBEB"
ctk_widget_background_dark = "#343638"
ctk_widget_foreground_dark = "#dce4ee"
ctk_widget_background_light = "#eaeaea"
ctk_widget_foreground_light = "#000000"
ctk_combobox_button_background = "#565b5e"
ctk_button_background_light = "#565b5e"
ctk_button_background_dark = "#1f6aa5"
progressbar_light_color = "#10af00"

#####################################################
######################  CLASS  ######################
#####################################################

class main():
    def __init__(self, app, main_frame, light_theme, mode):
        self.app = app
        self.main_frame = main_frame
        self.light_theme = light_theme
        self.mode  = mode
        self.last_update_time = 0
        self.prev_size = "large"
        self.current_width = tk.IntVar()
        self.current_height = tk.IntVar()
        #self.app.bind("<Configure>", self.on_resize) #has to do with resizing but my spaghetti code is too slow and causes bugs

        #setting threads
        self.th1 = None #thread 1 for handling yt_dlp
        self.th2 = None #thread 2 for handling animations
        #creating widgets
        self.create_widgets()


    def create_widgets(self):
        #creating logo-title
        self.logo_frame = tk.Frame(self.main_frame)
        self.logo_frame.grid(row=0, column=0, pady=80)
        #mp3 logo-title
        self.logo_image_mp3 = tk.Label(self.logo_frame, image=mp3_logo_large)
        self.logo_title_mp3 = tk.Label(self.logo_frame, text="MP3 Downloader", font=("Impact", 55, "bold"))
        #mp4 logo-title
        self.logo_image_mp4 = tk.Label(self.logo_frame, image=mp4_logo_large)
        self.logo_title_mp4 = tk.Label(self.logo_frame, text="MP4 Downloader", font=("Impact", 55, "bold"))
        
        #link entry and label common in both
        self.enter_url_label = tk.Label(self.main_frame, text="Enter Url:", font=("Arial", 30))
        self.enter_url_label.grid(row=1, column=0)
        self.url_entry = ctk.CTkEntry(self.main_frame, placeholder_text="https://www.youtube.com/", font=("Arial", 40), 
                                      justify="center", width=800)
        self.url_entry.grid(row=2, column=0, pady=40)

        #progressbar - time label
        self.time_label = tk.Label(self.main_frame, text="", font=("Arial", 20))
        #light style progress bar
        self.style_light = ttk.Style()
        self.style_light.theme_use("clam")
        self.style_light.configure("Light.Horizontal.TProgressbar", troughcolor=background_color_light, background=progressbar_light_color,
                             relief="flat")
        #dark style progress bar
        self.progressbar_frame = tk.Frame(self.main_frame)
        self.style_dark = ttk.Style()
        self.style_dark.theme_use("clam")
        self.style_dark.configure("Dark.Horizontal.TProgressbar", troughcolor=background_color_dark, background=ctk_button_background_dark,
                             relief="flat")
        self.progressbar_label = tk.Label(self.progressbar_frame, text="", font=("Arial", 20))
        self.progressbar_label.pack(side="top")
        self.progressbar = ttk.Progressbar(self.progressbar_frame, value=0, style='Dark.Horizontal.TProgressbar', length=800,
                                           mode='determinate')
        self.progressbar.pack(side="bottom", ipady=15)
        
        #resolution - quality selection
        self.resolution_combobox = ctk.CTkComboBox(self.main_frame, state="readonly", font=("Arial", 30), justify="center",
                                                   values=["144p", "240p", "360p","480p", "720p", "1080p", "1440p", "2160p"],
                                                   width=180)
        self.resolution_combobox.set("720p")
        self.quality_combobox = ctk.CTkComboBox(self.main_frame, state="readonly", font=("Arial", 30), justify="center",
                                                   values=["128kbps", "192kbps", "256kbps", "320kbps"], width=180)
        self.quality_combobox.set("192kbps")
        
        #search - download - pause buttons
        #mp4 search-download buttons
        self.search_audio_button = ctk.CTkButton(self.main_frame, text="Search Audio", font=("Arial", 30), border_spacing = 20,
                                                 command=self.validate_url)
        self.download_audio_button = ctk.CTkButton(self.main_frame, text="Download Audio", font=("Arial", 30), border_spacing = 20, command=self.start_download)
        #mp4 search-download buttons
        self.search_video_button = ctk.CTkButton(self.main_frame, text="Search Video", font=("Arial", 30), border_spacing = 20,
                                                 command=self.validate_url)
        self.download_video_button = ctk.CTkButton(self.main_frame, text="Download Video", font=("Arial", 30), border_spacing = 20, command=self.start_download)
        self.pause_download_button = ctk.CTkButton(self.main_frame, text="Pause Download", font=("Arial", 30), border_spacing = 20, command=self.pause_download)

        #switch - go back - stop download buttons
        self.switch_button = ctk.CTkButton(self.main_frame, text="", font=("Arial", 30), border_spacing = 20, command=self.switch_mode)
        self.switch_button.grid(row=5, column=0)
        self.go_back_button = ctk.CTkButton(self.main_frame, text="     Go Back     ", font=("Arial", 30), border_spacing = 20, command=self.go_back)
        self.stop_download_button = ctk.CTkButton(self.main_frame, text="Stop Download", font=("Arial", 30), border_spacing = 20, command=self.stop_download)

        #light theme switch
        self.light_theme_switch = ctk.CTkSwitch(self.main_frame, text="", command=self.switch_theme, onvalue="1", offvalue="0",
                                                font=("Arial", 30), switch_width=70, switch_height=30)
        self.light_theme_switch.grid(row=6, column=0, pady=40)

        #rest of widgets here############
        ################################# 
        #matching mode to display previously selected mode(mp3-mp4)
        match self.mode:
            case "mp3":
                self.logo_image_mp3.pack(side="left", padx=30)
                self.logo_title_mp3.pack(side="right", padx=30)
                self.quality_combobox.grid(row=3, column=0)
                self.search_audio_button.grid(row=4, column=0, pady=40)
                self.switch_button.configure(text="Switch To MP4")
            case "mp4":
                self.logo_image_mp4.pack(side="left", padx=30)
                self.logo_title_mp4.pack(side="right", padx=30)
                self.resolution_combobox.grid(row=3, column=0)
                self.search_video_button.grid(row=4, column=0, pady=40)
                self.switch_button.configure(text="Switch To MP3")

        #setting light theme or dark theme
        self.set_widget_color()


    def set_widget_color(self):
        #0 for light theme, 1 for dark theme
        match self.light_theme:
            case "0":
                #main frame color
                self.main_frame.config(background=background_color_light)
                #logo_frame
                self.logo_frame.config(background=background_color_light)
                for widget in self.logo_frame.winfo_children():
                    widget.config(background = background_color_light, foreground = foreground_color_light)
                #url entry widgets
                self.enter_url_label.config(background = background_color_light, foreground = foreground_color_light)
                self.url_entry.configure(fg_color=ctk_widget_background_light, text_color=ctk_widget_foreground_light)
                #progressbar staff
                self.time_label.config(background = background_color_light, foreground = foreground_color_light)
                self.progressbar_frame.configure(background = background_color_light)
                self.progressbar_label.configure(background = background_color_light, foreground = foreground_color_light)
                self.progressbar.configure(style='Light.Horizontal.TProgressbar')
                #quality-resolution combobox
                self.resolution_combobox.configure(fg_color=ctk_widget_background_light, text_color=ctk_widget_foreground_light,
                                                   button_color=(ctk_widget_foreground_light, ctk_combobox_button_background),
                                                   dropdown_fg_color=ctk_widget_background_light, dropdown_text_color=ctk_widget_foreground_light)
                self.quality_combobox.configure(fg_color=ctk_widget_background_light, text_color=ctk_widget_foreground_light,
                                                button_color=(ctk_widget_foreground_light, ctk_combobox_button_background),
                                                dropdown_fg_color=ctk_widget_background_light, dropdown_text_color=ctk_widget_foreground_light)
                #search-download-pause buttons
                self.search_audio_button.configure(fg_color=ctk_button_background_light)
                self.search_video_button.configure(fg_color=ctk_button_background_light)
                self.download_audio_button.configure(fg_color=ctk_button_background_light)
                self.download_video_button.configure(fg_color=ctk_button_background_light)
                self.pause_download_button.configure(fg_color=ctk_button_background_light)
                self.go_back_button.configure(fg_color=ctk_button_background_light)
                self.stop_download_button.configure(fg_color=ctk_button_background_light)
                self.switch_button.configure(fg_color=ctk_button_background_light)
                self.light_theme_switch.configure(text="Switch to dark mode", text_color=foreground_color_light, button_color=background_color_dark)
            case "1":
                #main frame color
                self.main_frame.config(background=background_color_dark)
                #logo_frame
                self.logo_frame.config(background=background_color_dark)
                for widget in self.logo_frame.winfo_children():
                    widget.config(background = background_color_dark, foreground = foreground_color_dark)
                #url entry widgets
                self.enter_url_label.config(background = background_color_dark, foreground = foreground_color_dark)
                self.url_entry.configure(fg_color=ctk_widget_background_dark, text_color=ctk_widget_foreground_dark)
                #progressbar staff
                self.time_label.config(background = background_color_dark, foreground = foreground_color_dark)
                self.progressbar_frame.configure(background = background_color_dark)
                self.progressbar_label.configure(background = background_color_dark, foreground = foreground_color_dark)
                self.progressbar.configure(style='Dark.Horizontal.TProgressbar')
                #quality-resolution combobox
                self.resolution_combobox.configure(fg_color=ctk_widget_background_dark, text_color=ctk_widget_foreground_dark,
                                                   button_color=(ctk_widget_foreground_dark, ctk_combobox_button_background),
                                                   dropdown_fg_color=ctk_widget_background_dark, dropdown_text_color=ctk_widget_foreground_dark)
                self.quality_combobox.configure(fg_color=ctk_widget_background_dark, text_color=ctk_widget_foreground_dark,
                                                button_color=(ctk_widget_foreground_dark, ctk_combobox_button_background),
                                                dropdown_fg_color=ctk_widget_background_dark, dropdown_text_color=ctk_widget_foreground_dark)
                #search-download-pause buttons
                self.search_audio_button.configure(fg_color=ctk_button_background_dark)
                self.search_video_button.configure(fg_color=ctk_button_background_dark)
                self.download_audio_button.configure(fg_color=ctk_button_background_dark)
                self.download_video_button.configure(fg_color=ctk_button_background_dark)
                self.pause_download_button.configure(fg_color=ctk_button_background_dark)
                self.go_back_button.configure(fg_color=ctk_button_background_dark)
                self.stop_download_button.configure(fg_color=ctk_button_background_dark)
                self.switch_button.configure(fg_color=ctk_button_background_dark)
                self.light_theme_switch.configure(text="Switch to light mode", text_color=foreground_color_dark, button_color=background_color_light)
                self.light_theme_switch.select()
    

    def validate_url(self):
        self.url = self.url_entry.get()
        match is_valid_youtube_url(self.url):
            case True:
                # Reset dot count for animation
                self.dot_count = 1
                # Start threads for search and animation
                self.th1 = th.Thread(target=self.search, daemon=False)
                self.th2 = th.Thread(target=self.search_animation)
                print("Threads reserved tasks:\nth1: self.search()\nth2: self.search_animation()\n")
                # Start th1 and call wait_for_search
                self.th1.start()
                self.wait_for_search()
            case False:
                # Handle invalid URL format
                self.url_entry.delete(0, tk.END)
                self.url_entry.insert(0, "Invalid YouTube URL.")


    def wait_for_search(self):
        match self.th1.is_alive():
            case True:
                self.app.after(400, self.wait_for_search)
            case _:
                print("th1 stopped")
                print("th2 stopped")
                match self.mode:
                    case "mp3":
                        self.set_download_buttons()
                    case "mp4":
                        self.search_results()


    def search(self):
        print("th1 running...")
        self.switch_button._state = "disabled"
        self.url_entry.configure(state="disabled")
        match self.mode:
            case "mp3":
                self.quality_combobox._state = "disabled"
                self.search_audio_button._command = None
            case "mp4":
                self.resolution_combobox._state = "disabled"
                self.search_video_button._command = None

        # Start th2 for animations
        self.th2.start()
        print("th2 running...")
        self.available_resolutions = []
        self.available_qualities = []

        # yt-dlp options
        ydl_search_options = {
            'quiet': True,
            'extract_flat': False,
            'ffmpeg_location': ffmpeg_path,
            'cookies_from_browser': ('edge'),
            'geo_bypass': True
        }

        try:
            with ydl.YoutubeDL(ydl_search_options) as search:
                # Extract video information
                self.video_info = search.extract_info(self.url, download=False)

                # Process formats to extract resolutions and audio qualities
                for fmt in self.video_info.get('formats', []):
                    # Extract video resolutions (height)
                    height = fmt.get('height')
                    if height and height not in self.available_resolutions:
                        self.available_resolutions.append(height)

                    # Extract audio qualities (abr - audio bitrate)
                    abr = fmt.get('abr')  # Audio bitrate in kbps
                    if abr and abr not in self.available_qualities:
                        self.available_qualities.append(round(abr))

                # Sort the lists
                self.available_resolutions.sort()
                self.available_qualities.sort()
                print("Available Resolutions:", self.available_resolutions)
                print("Available Audio Qualities:", self.available_qualities)

                # Check if quality or resolution exists
                match self.mode:
                    case "mp3":
                        pass #mp3 quality is gonna be the best converted to wanted quality
                    case "mp4":
                        self.resolution_exists()

        except ydl.utils.DownloadError as e:
            error_str = str(e).lower()
            print("DownloadError caught:", error_str)
            self.url_entry.configure(state="normal")
            self.url_entry.delete(0, tk.END)
            if "video unavailable" in error_str or "not available" in error_str:
                self.url_entry.insert(tk.END, "Video does not exist.")
            else:
                self.url_entry.insert(tk.END, "Cannot access video. Check restrictions or link.")
            # Reset buttons
            self.switch_button._state = "normal"
            match self.mode:
                case "mp3":
                    self.quality_combobox.configure(state="readonly")
                    self.search_audio_button._command = self.validate_url
                    self.search_audio_button.configure(text="Search Audio")
                case "mp4":
                    self.resolution_combobox.configure(state="readonly")
                    self.search_video_button._command = self.validate_url
                    self.search_video_button.configure(text="Search Video")
        except Exception as e:
            print("Error during search:", e)
            self.url_entry.configure(state="normal")
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(tk.END, "Check your connection or URL.") #General error message
            # Reset buttons
            self.switch_button._state = "normal"
            match self.mode:
                case "mp3":
                    self.quality_combobox.configure(state="readonly")
                    self.search_audio_button._command = self.validate_url
                    self.search_audio_button.configure(text="Search Audio")
                case "mp4":
                    self.resolution_combobox.configure(state="readonly")
                    self.search_video_button._command = self.validate_url
                    self.search_video_button.configure(text="Search Video")


    def search_animation(self):
            #while th1 is running chack dot count and set text to the mode button
            match self.th1.is_alive():
                case True:
                    if self.dot_count>3:
                        self.dot_count=1
                    #matching active mode to change correct button
                    match self.mode:
                        case "mp3":
                            match self.dot_count:
                                case 1:
                                    self.search_audio_button.configure(text = "   Searching.    ")
                                case 2:
                                    self.search_audio_button.configure(text = "   Searching..   ")
                                case 3:
                                    self.search_audio_button.configure(text = "   Searching...  ")
                            self.dot_count+=1
                        case "mp4":
                            match self.dot_count:
                                case 1:
                                    self.search_video_button.configure(text = "   Searching.    ")
                                case 2:
                                    self.search_video_button.configure(text = "   Searching..   ")
                                case 3:
                                    self.search_video_button.configure(text = "   Searching...  ")
                            self.dot_count+=1
                    self.app.after(400, self.search_animation)
                case False:
                    pass


    def resolution_exists(self): #handled by th1 sets true or false and next resolution based on selection
        self.correct_available_resolutions = []
        for item in self.available_resolutions:
            if item not in wrong_resolutions_mp4:
                self.correct_available_resolutions.append(f"{item}p")
            else:
                #if resolution height is wrong append correct one
                match item:
                    case 128:
                        self.correct_available_resolutions.append("144p")
                    case 214:
                        self.correct_available_resolutions.append("240p")
                    case 320:
                        self.correct_available_resolutions.append("360p")
                    case 428:
                        self.correct_available_resolutions.append("480p")
                    case 640:
                        self.correct_available_resolutions.append("720p")
                    case 960:
                        self.correct_available_resolutions.append("1080p")
                    case 1280:
                        self.correct_available_resolutions.append("1440p")
                    case 1920:
                        self.correct_available_resolutions.append("2160p")
        if self.resolution_combobox.get() in self.correct_available_resolutions:    
            self.exists = True
        else:
            self.exists = False


    def search_results(self):
        match self.exists:
            case False:
                self.url_entry.configure(state="normal")
                self.url_entry.delete(0, tk.END)
                self.url_entry.insert(tk.END, f"Resolution Does Not Exist (Max {self.correct_available_resolutions[-1]}).")
                # Reset buttons
                self.switch_button._state = "normal"
                self.resolution_combobox.configure(state="readonly")
                self.search_video_button._command = self.validate_url
                self.search_video_button.configure(text="Search Video")
            case True:
                self.set_download_buttons()



    
    def go_back(self):
        self.go_back_button.grid_forget()
        self.switch_button.grid(row=5, column=0)
        self.url_entry.configure(state="normal")
        self.url_entry.delete(0, tk.END)
        self.url_entry._activate_placeholder()
        self.main_frame.focus()
        match self.mode:
            case "mp3":
                self.quality_combobox.configure(state="readonly")
                self.quality_combobox.set("192kbps")
                self.download_audio_button.grid_forget()
                self.search_audio_button.grid(row=4, column=0, pady=40)
            case "mp4":
                self.resolution_combobox.configure(state="readonly")
                self.resolution_combobox.set("720p")
                self.download_video_button.grid_forget()
                self.search_video_button.grid(row=4, column=0, pady=40)



    def set_download_buttons(self):
        self.url_entry.configure(state="normal")
        self.url_entry.delete(0, tk.END)
        self.url_entry.insert(tk.END, self.video_info['title'])
        self.url_entry.configure(state="disabled")
        match self.mode:
            case "mp3":
                # Reset - grid_forget buttons
                self.switch_button._state = "normal"
                self.switch_button.grid_forget()
                self.search_audio_button._command = self.validate_url
                self.search_audio_button.configure(text="Search Audio")
                self.search_audio_button.grid_forget()
                # Setting download buttons
                self.download_audio_button.grid(row=4, column=0, pady=40)
                self.go_back_button.grid(row=5, column=0)
            case "mp4":
                # Reset - grid_forget buttons
                self.switch_button._state = "normal"
                self.switch_button.grid_forget()
                self.search_video_button._command = self.validate_url
                self.search_video_button.configure(text="Search Video")
                self.search_video_button.grid_forget()
                # Setting download buttons
                self.download_video_button.grid(row=4, column=0, pady=40)
                self.go_back_button.grid(row=5, column=0)
        self.th1 = th.Thread(target=self.download, daemon=False)
        print("\nThreads reserved tasks:\nth1: self.download()\nth2: self.refresh_progressbar()\n")


    def start_download(self):
        self.download_progress = {"status": "downloading"}
        self.enter_url_label.grid_forget()
        self.time_label['text'] = "Starting Download..."
        self.time_label.grid(row=1, column=0)
        self.url_entry.grid_forget()
        self.progressbar.configure(value=0)
        self.progressbar_frame.grid(row=2, column=0, pady=40)
        self.go_back_button.grid_forget()
        self.stop_download_button.grid(row=5, column=0)
        match self.mode:
            case "mp3":
                self.download_audio_button.grid_forget()
            case "mp4":
                self.download_video_button.grid_forget()
        self.pause_download_button.grid(row=4, column=0, pady=40)
        self.th1.start()
        self.wait_for_download()


    def wait_for_download(self):
        match self.th1.is_alive():
            case True:
                self.app.after(400, self.wait_for_download)
            case _:
                print("th1 stopped")
                print("th2 stopped")
                self.reset_ui()


    def download(self):
        match self.mode:
            case "mp3":
                pass
            case "mp4":
                self.file_count = 0
        self.download_resume = True
        self.download_stop = False
        self.times_tried_to_delete = 0
        self.file_count = 0
        print("th1 running...")
        self.th2 = th.Thread(target=self.update_progressbar)
        self.th2.start()
        print("th2 running...")
        #setting download_options
        match self.mode:
            case "mp3":
                quality = self.quality_combobox.get()
                int_quality = int(quality.replace("kbps", ""))
                download_options = {
                    'format': 'bestaudio/best',
                    'cookies_from_browser': ('edge'),
                    'geo_bypass': True,
                    'outtmpl': os.path.join(download_dir_path, f"{self.video_info['title']}.%(ext)s"),
                    'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': int_quality,
                        }],
                        'postprocessor_args': [
                            '-ar', '44100',  
                            '-ac', '2',       
                        ],
                    'quiet': False,
                    "progress_hooks": [self.progress_hook]
                }
            case "mp4":
                resolution = self.resolution_combobox.get()
                int_resolution = int(resolution.replace("p", ""))
                download_options = {
                    "format": f"bestvideo[height<={int_resolution}]+bestaudio[acodec^=mp4a]/best[ext=mp4]",
                    "outtmpl": os.path.join(download_dir_path, f"{self.video_info['title']}.%(ext)s"),
                    "progress_hooks": [self.progress_hook],
                    'cookies_from_browser': ('edge'),
                    'geo_bypass': True
                }
        #downloading
        try:
            with ydl.YoutubeDL(download_options) as download:
                self.ydl_instance = download
                download.download(self.url)
        except Exception as e:
            print(e)


    def progress_hook(self, data):
        if self.download_stop:
            raise Exception('Download Stopped')
        else:
            if data.get('status') == 'downloading':
                self.download_progress['downloaded_mb'] = data.get('downloaded_bytes', 0)
                self.download_progress['total_mb'] = data.get('total_bytes', 1)
                self.download_progress['eta'] = data.get('eta', 0)
            elif data.get('status') == 'finished':
                self.file_count += 1
                self.download_progress['status'] = 'finished'

    def update_progressbar(self):
        match self.mode:
            case "mp3":
                if self.download_progress.get("status") == "finished":
                    return
            case "mp4":
                if self.file_count < 2:
                    pass
                else:
                    if self.download_progress.get("status") == "finished":
                        return

        try:
            match self.download_resume:
                case True:
                    downloaded = self.download_progress.get("downloaded_mb", 0) / 1048576
                    total = self.download_progress.get("total_mb", 1) or 1
                    if total not in (0, 1):
                        total /= 1048576

                    percent = (downloaded / total) * 100
                    self.progressbar_label.configure(text=f"{percent:.2f}%, {downloaded:.2f}MB / {total:.2f}MB")
                    self.progressbar.configure(value=percent)

                    eta = self.download_progress.get('eta')
                    if eta and isinstance(eta, (int, float)):
                        hours, remainder = divmod(int(eta), 3600)
                        minutes, seconds = divmod(remainder, 60)
                        if hours:
                            self.time_label.configure(text=f"Time remaining: {hours}:{minutes:02}:{seconds:02}")
                        else:
                            self.time_label.configure(text=f"Time remaining: {minutes}:{seconds:02}")
                case False:
                    self.time_label.configure(text=f"Download Paused")
        except Exception as e:
            print("Progress update error:", e)
            return

        self.app.after(500, self.update_progressbar)


    def pause_download(self):
        match self.download_resume:
            case True:
                self.download_resume = False
                self.pause_download_button.configure(text="Resume Download")
            case False:
                self.pause_download_button.configure(text="Pause Download")
                self.th1 = th.Thread(target=self.download, daemon=False)
                self.th1.start()


    def stop_download(self):
        self.download_stop = True
        output_template = self.ydl_instance.params.get('outtmpl', 'downloads/%(title)s.%(ext)s')
        
        try:
            for filename in os.listdir(download_dir_path):
                if filename.endswith(('.part', '.f1', '.f2', '.ytdl', '.temp', '.frag', '.m4a.tmp')):
                    file_path = os.path.join(download_dir_path, filename)
                    try:
                        os.remove(file_path)
                        print(f"Deleted partial file: {file_path}")
                    except Exception as e:
                        print(f"Failed to delete {file_path}: {e}")
                        
                        # Retry up to 10 times
                        self.times_tried_to_delete += 1
                        if self.times_tried_to_delete < 10:
                            self.app.after(1000, self.stop_download)
                        return  # Exit after scheduling retry
        except Exception as e:
            print(f"Error during stop/cleanup: {e}")


    def reset_ui(self):
        self.time_label.configure(text="")
        self.time_label.grid_forget()
        self.progressbar_label.configure(text="")
        self.progressbar_frame.grid_forget()
        self.enter_url_label.grid(row=1, column=0)
        self.url_entry.configure(state="normal")
        self.url_entry.delete(0, tk.END)
        self.url_entry._activate_placeholder()
        self.url_entry.grid(row=2, column=0, pady=40)
        self.main_frame.focus()
        self.pause_download_button.grid_forget()
        match self.mode:
            case "mp3":
                self.quality_combobox.configure(state="readonly")
                self.quality_combobox.set("192kbps")
                self.search_audio_button.grid(row=4, column=0, pady=40)
            case "mp4":
                self.resolution_combobox.configure(state="readonly")
                self.resolution_combobox.set("720p")
                self.search_video_button.grid(row=4, column=0, pady=40)
        self.stop_download_button.grid_forget()
        self.switch_button.grid(row=5, column=0)
        match self.mode:
            case "mp3":
                match self.download_stop:
                    case False:
                        messagebox.showinfo("Download Finished", f"File Location: Downloads Folder\nFile Name: {self.video_info['title']}")
                    case True:
                        messagebox.showinfo("Download Stopped", "Download was stopped and partial files were deleted.")
            case "mp4":
                match self.download_stop:
                    case False:
                        messagebox.showinfo("Download Finished", f"File Location: Downloads Folder\nFile Name: {self.video_info['title']}")
                    case True:
                        messagebox.showinfo("Download Stopped", "Download was stopped and partial files were deleted.")


    def switch_mode(self): #switch between mp3-mp4
        match self.mode:
            case "mp3":
                self.logo_image_mp3.pack_forget()
                self.logo_title_mp3.pack_forget()
                self.logo_image_mp4.pack(side="left", padx=30)
                self.logo_title_mp4.pack(side="right", padx=30)
                self.url_entry.delete(0, tk.END)
                self.url_entry._activate_placeholder()
                self.main_frame.focus() #focusing on main frame because if not user writes in place of placeholder
                self.quality_combobox.set("192kbps")
                self.quality_combobox.grid_forget()
                self.resolution_combobox.grid(row=3, column=0)
                self.search_audio_button.grid_forget()
                self.search_video_button.grid(row=4, column=0, pady=40)
                self.switch_button.configure(text="Switch To MP3")
                self.mode = "mp4"
                #self.resize_unique_widgets()
                write_to_json(self.light_theme, "mp4")
            case"mp4":
                self.logo_image_mp4.pack_forget()
                self.logo_title_mp4.pack_forget()
                self.logo_image_mp3.pack(side="left", padx=30)
                self.logo_title_mp3.pack(side="right", padx=30)
                self.url_entry.delete(0, tk.END)
                self.url_entry._activate_placeholder()
                self.main_frame.focus() #focusing on main frame because if not user writes in place of placeholder
                self.resolution_combobox.set("720p")
                self.resolution_combobox.grid_forget()
                self.quality_combobox.grid(row=3, column=0)
                self.search_video_button.grid_forget()
                self.search_audio_button.grid(row=4, column=0, pady=40)
                self.switch_button.configure(text="Switch To MP4")
                self.mode = "mp3"
                self.prev_size = ""
                #self.resize_unique_widgets()
                write_to_json(self.light_theme, "mp3")


    def switch_theme(self): #switch between light_dark theme
        match self.light_theme:
            case "0":
                #setting light theme value to opposite
                self.light_theme = "1"
                #main frame color
                self.main_frame.config(background=background_color_dark)
                #logo_frame
                self.logo_frame.config(background=background_color_dark)
                for widget in self.logo_frame.winfo_children():
                    widget.config(background = background_color_dark, foreground = foreground_color_dark)
                #url entry widgets
                self.enter_url_label.config(background = background_color_dark, foreground = foreground_color_dark)
                self.url_entry.configure(fg_color=ctk_widget_background_dark, text_color=ctk_widget_foreground_dark)
                #progressbar staff
                self.time_label.config(background = background_color_dark, foreground = foreground_color_dark)
                self.progressbar_frame.configure(background = background_color_dark)
                self.progressbar_label.configure(background = background_color_dark, foreground = foreground_color_dark)
                self.progressbar.configure(style='Dark.Horizontal.TProgressbar')
                #quality-resolution combobox
                self.resolution_combobox.configure(fg_color=ctk_widget_background_dark, text_color=ctk_widget_foreground_dark,
                                                   button_color=(ctk_widget_foreground_dark, ctk_combobox_button_background),
                                                   dropdown_fg_color=ctk_widget_background_dark, dropdown_text_color=ctk_widget_foreground_dark)
                self.quality_combobox.configure(fg_color=ctk_widget_background_dark, text_color=ctk_widget_foreground_dark,
                                                button_color=(ctk_widget_foreground_dark, ctk_combobox_button_background),
                                                dropdown_fg_color=ctk_widget_background_dark, dropdown_text_color=ctk_widget_foreground_dark)
                #search-download-pause buttons
                self.search_audio_button.configure(fg_color=ctk_button_background_dark)
                self.search_video_button.configure(fg_color=ctk_button_background_dark)
                self.download_audio_button.configure(fg_color=ctk_button_background_dark)
                self.download_video_button.configure(fg_color=ctk_button_background_dark)
                self.pause_download_button.configure(fg_color=ctk_button_background_dark)
                self.go_back_button.configure(fg_color=ctk_button_background_dark)
                self.stop_download_button.configure(fg_color=ctk_button_background_dark)
                #switch button + light switch
                self.switch_button.configure(fg_color=ctk_button_background_dark)
                self.light_theme_switch.configure(text="Switch to light mode", text_color=foreground_color_dark, button_color=background_color_light)
                dark_title_bar()
                write_to_json(self.light_theme, self.mode)
            case "1":
                #setting light theme value to opposite
                self.light_theme = "0"
                #main frame color
                self.main_frame.config(background=background_color_light)
                #logo_frame
                self.logo_frame.config(background=background_color_light)
                for widget in self.logo_frame.winfo_children():
                    widget.config(background = background_color_light, foreground = foreground_color_light)
                #url entry widgets
                self.enter_url_label.config(background = background_color_light, foreground = foreground_color_light)
                self.url_entry.configure(fg_color=ctk_widget_background_light, text_color=ctk_widget_foreground_light)
                #progressbar staff
                self.time_label.config(background = background_color_light, foreground = foreground_color_light)
                self.progressbar_frame.configure(background = background_color_light)
                self.progressbar_label.configure(background = background_color_light, foreground = foreground_color_light)
                self.progressbar.configure(style='Light.Horizontal.TProgressbar')
                #quality-resolution combobox
                self.resolution_combobox.configure(fg_color=ctk_widget_background_light, text_color=ctk_widget_foreground_light,
                                                   button_color=(ctk_widget_foreground_light, ctk_combobox_button_background),
                                                   dropdown_fg_color=ctk_widget_background_light, dropdown_text_color=ctk_widget_foreground_light)
                self.quality_combobox.configure(fg_color=ctk_widget_background_light, text_color=ctk_widget_foreground_light,
                                                button_color=(ctk_widget_foreground_light, ctk_combobox_button_background),
                                                dropdown_fg_color=ctk_widget_background_light, dropdown_text_color=ctk_widget_foreground_light)
                #search-download-pause buttons
                self.search_audio_button.configure(fg_color=ctk_button_background_light)
                self.search_video_button.configure(fg_color=ctk_button_background_light)
                self.download_audio_button.configure(fg_color=ctk_button_background_light)
                self.download_video_button.configure(fg_color=ctk_button_background_light)
                self.pause_download_button.configure(fg_color=ctk_button_background_light)
                self.go_back_button.configure(fg_color=ctk_button_background_light)
                self.stop_download_button.configure(fg_color=ctk_button_background_light)
                #switch button + light switch
                self.switch_button.configure(fg_color=ctk_button_background_light)
                self.light_theme_switch.configure(text="Switch to dark mode", text_color=foreground_color_light, button_color=background_color_dark)
                light_title_bar()
                write_to_json(self.light_theme, self.mode)


    #resize spaghetti
    def on_resize(self, event):
        self.app.config(width=event.width, height=event.height)
        self.current_width.set(str(self.app.winfo_width()))
        self.current_height.set(str(self.app.winfo_height()))
        self.resize_shared_widgets()



    def resize_shared_widgets(self):
        width = self.current_width.get()
        height = self.current_height.get()
        self.current_size = ""
        print(f"{width}x{height}") ##################### get new min size #######################

        #setting size
        if width>1400 and height>1200:
            self.current_size = "xlarge"
        elif width>1000 and height>900:
            self.current_size = "large"
        elif width>800 and height>700:
            self.current_size = "medium"
        else:
            self.current_size = "small"

        #if current size different than prev size resize
        if self.prev_size != self.current_size:
            match self.current_size:
                case "xlarge":
                    #here goes the resize 
                    self.logo_frame.grid_configure(pady=100)
                    for widget in self.logo_frame.winfo_children(): 
                        try:
                            padx = widget.pack_info().get('padx', 0)
                            match padx:
                                case 20 | 25 | 30:
                                    widget.pack_configure(padx=35)
                        except:
                            pass
                    for widget in self.main_frame.winfo_children():
                        try:
                            pady = widget.grid_info().get('pady', 0)
                            match pady:
                                case 20 | 30 | 40:
                                    widget.grid_configure(pady=50)
                        except:
                            pass
                        try:
                            font = widget.cget('font')
                            font = widget.cget('font')
                            if isinstance(font, str):
                                parts = font.split()
                                if len(parts) >= 2 and parts[1].isdigit():
                                    font_tuple = (parts[0], int(parts[1]))
                                else:
                                    font_tuple = None
                            else:
                                font_tuple = font if isinstance(font, tuple) else None
                            match font_tuple:
                                case ('Arial', 20) | ('Arial', 25) | ('Arial', 30):
                                    widget.configure(font=('Arial', 40))
                                case ('Arial', 15) | ('Arial', 17) | ('Arial', 20):
                                    widget.configure(font=('Arial', 25))
                        except:
                            pass
                        self.url_entry.configure(font=('Arial', 50), width=1000)
                        self.switch_button.configure(border_spacing=25)
                        self.light_theme_switch.configure(switch_width=90, switch_height=35)
                        self.progressbar.configure(length=1000)
                        self.progressbar.pack_configure(ipady=18)
                    self.resize_unique_widgets()
                    #setting prev size to xlarge value
                    self.prev_size = self.current_size
                
                case "large":
                    #here goes the resize
                    self.logo_frame.grid_configure(pady=80)
                    for widget in self.logo_frame.winfo_children(): 
                        try:  
                            padx = widget.pack_info().get('padx', 0)
                            match padx:
                                case 20 | 25 | 35:
                                    widget.pack_configure(padx=30)
                        except:
                            pass
                    for widget in self.main_frame.winfo_children():
                        try:
                            pady = widget.grid_info().get('pady', 0)
                            match pady:
                                case 20 | 30 | 50:
                                    widget.grid_configure(pady=40)
                        except:
                            pass
                        try:
                            font = widget.cget('font')
                            if isinstance(font, str):
                                parts = font.split()
                                if len(parts) >= 2 and parts[1].isdigit():
                                    font_tuple = (parts[0], int(parts[1]))
                                else:
                                    font_tuple = None
                            else:
                                font_tuple = font if isinstance(font, tuple) else None
                            if font_tuple:
                                match font_tuple:
                                    case ('Arial', 20) | ('Arial', 25) | ('Arial', 40):
                                        widget.configure(font=('Arial', 30))
                                    case ('Arial', 15) | ('Arial', 17) | ('Arial', 25):
                                        widget.configure(font=('Arial', 20))
                        except:
                            pass
                        self.url_entry.configure(font=('Arial', 40), width=800)
                        self.switch_button.configure(border_spacing=20)
                        self.light_theme_switch.configure(switch_width=70, switch_height=30)
                        self.progressbar.configure(length=800)
                        self.progressbar.pack_configure(ipady=15)
                    self.resize_unique_widgets()
                    #setting prev size to large value
                    self.prev_size = self.current_size
                
                case "medium":
                    #here goes the resize
                    self.logo_frame.grid_configure(pady=60)
                    for widget in self.logo_frame.winfo_children():
                        try:   
                            padx = widget.pack_info().get('padx', 0)
                            match padx:
                                case 20 | 30 | 35:
                                    widget.pack_configure(padx=25)
                        except:
                            pass
                    for widget in self.main_frame.winfo_children():
                        try:
                            pady = widget.grid_info().get('pady', 0)
                            match pady:
                                case 20 | 40 | 50:
                                    widget.grid_configure(pady=30)
                        except:
                            pass
                        try:
                            font = widget.cget('font')
                            if isinstance(font, str):
                                parts = font.split()
                                if len(parts) >= 2 and parts[1].isdigit():
                                    font_tuple = (parts[0], int(parts[1]))
                                else:
                                    font_tuple = None
                            else:
                                font_tuple = font if isinstance(font, tuple) else None
                            match font_tuple:
                                case ('Arial', 20) | ('Arial', 30) | ('Arial', 40):
                                    widget.configure(font=('Arial', 25))
                                case ('Arial', 15) | ('Arial', 20) | ('Arial', 25):
                                    widget.configure(font=('Arial', 17))
                        except:
                            pass
                        self.url_entry.configure(font=('Arial', 30), width=700)
                        self.switch_button.configure(border_spacing=17)
                        self.light_theme_switch.configure(switch_width=60, switch_height=25)
                        self.progressbar.configure(length=700)
                        self.progressbar.pack_configure(ipady=13)
                    self.resize_unique_widgets()
                    #setting prev size to medium value
                    self.prev_size = self.current_size
                
                case "small":
                    #here goes the resize
                    self.logo_frame.grid_configure(pady=40)
                    for widget in self.logo_frame.winfo_children():
                        try:   
                            padx = widget.pack_info().get('padx', 0)
                            match padx:
                                case 25 | 30 | 35:
                                    widget.pack_configure(padx=20)
                        except:
                            pass
                    for widget in self.main_frame.winfo_children():
                        try:
                            pady = widget.grid_info().get('pady', 0)
                            match pady:
                                case 30 | 40 | 50:
                                    widget.grid_configure(pady=20)
                        except:
                            pass
                        try:
                            font = widget.cget('font')
                            if isinstance(font, str):
                                parts = font.split()
                                if len(parts) >= 2 and parts[1].isdigit():
                                    font_tuple = (parts[0], int(parts[1]))
                                else:
                                    font_tuple = None
                            else:
                                font_tuple = font if isinstance(font, tuple) else None
                            match font_tuple:
                                case ('Arial', 25) | ('Arial', 30) | ('Arial', 40):
                                    widget.configure(font=('Arial', 20))
                                case ('Arial', 17) | ('Arial', 20) | ('Arial', 25):
                                    widget.configure(font=('Arial', 15))
                        except:
                            pass
                        self.url_entry.configure(font=('Arial', 25), width=600)
                        self.switch_button.configure(border_spacing=15)
                        self.light_theme_switch.configure(switch_width=50, switch_height=20) 
                        self.progressbar.configure(length=600)
                        self.progressbar.pack_configure(ipady=10)  
                    self.resize_unique_widgets()
                    #setting prev size to small value
                    self.prev_size = self.current_size


    def resize_unique_widgets(self):
        match self.current_size:
            case "xlarge":
                match self.mode:
                        case "mp3":
                            self.logo_image_mp3.configure(image=mp3_logo_xlarge)
                            self.logo_title_mp3.configure(font=("Impact", 65, "bold"))
                            self.quality_combobox.configure(width=220)
                            self.search_audio_button.configure(border_spacing=25)
                        case "mp4":
                            self.logo_image_mp4.configure(image=mp4_logo_xlarge)
                            self.logo_title_mp4.configure(font=("Impact", 65, "bold"))
                            self.resolution_combobox.configure(width=220)
                            self.search_video_button.configure(border_spacing=25)
            case "large":
                match self.mode:
                        case "mp3":
                            self.logo_image_mp3.configure(image=mp3_logo_large)
                            self.logo_title_mp3.configure(font=("Impact", 55, "bold"))
                            self.quality_combobox.configure(width=180)
                            self.search_audio_button.configure(border_spacing=20)
                        case "mp4":
                            self.logo_image_mp4.configure(image=mp4_logo_large)
                            self.logo_title_mp4.configure(font=("Impact", 55, "bold"))
                            self.resolution_combobox.configure(width=180)
                            self.search_video_button.configure(border_spacing=20)
            case "medium":
                match self.mode:
                        case "mp3":
                            self.logo_image_mp3.configure(image=mp3_logo_medium)
                            self.logo_title_mp3.configure(font=("Impact", 45, "bold"))
                            self.quality_combobox.configure(width=160)
                            self.search_audio_button.configure(border_spacing=17)
                        case "mp4":
                            self.logo_image_mp4.configure(image=mp4_logo_medium)
                            self.logo_title_mp4.configure(font=("Impact", 45, "bold"))
                            self.resolution_combobox.configure(width=160)
                            self.search_video_button.configure(border_spacing=17)
            case "small":
                match self.mode:
                        case "mp3":
                            self.logo_image_mp3.configure(image=mp3_logo_small)
                            self.logo_title_mp3.configure(font=("Impact", 35, "bold"))
                            self.quality_combobox.configure(width=140)
                            self.search_audio_button.configure(border_spacing=15)
                        case "mp4":
                            self.logo_image_mp4.configure(image=mp4_logo_small)
                            self.logo_title_mp4.configure(font=("Impact", 35, "bold"))
                            self.resolution_combobox.configure(width=140)
                            self.search_video_button.configure(border_spacing=15)
            
            


################## END OF CLASS ###################
###################################################
#################### FUNCTIONS ####################


def light_title_bar(): 
    if os.name == 'nt':
        app.update()
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        set_app_attribute = ct.windll.dwmapi.DwmSetWindowAttribute
        get_parent = ct.windll.user32.GetParent
        hwnd = get_parent(app.winfo_id())
        rendering_policy = DWMWA_USE_IMMERSIVE_DARK_MODE
        value = 0
        value = ct.c_int(value)
        set_app_attribute(hwnd, rendering_policy, ct.byref(value),
                             ct.sizeof(value))
        

def dark_title_bar():
    if os.name == 'nt':
        app.update()
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        set_app_attribute = ct.windll.dwmapi.DwmSetWindowAttribute
        get_parent = ct.windll.user32.GetParent
        hwnd = get_parent(app.winfo_id())
        rendering_policy = DWMWA_USE_IMMERSIVE_DARK_MODE
        value = 2
        value = ct.c_int(value)
        set_app_attribute(hwnd, rendering_policy, ct.byref(value),
                             ct.sizeof(value))
        

def is_valid_youtube_url(url):
    youtube_regex = re.compile(r'^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+$')
    return youtube_regex.match(url) is not None
        

def center_screen():
    #place app at the center of the screen
    global screen_height, screen_width, x_cordinate, y_cordinate
    screen_width = app.winfo_screenwidth()
    screen_height = app.winfo_screenheight()
    x_cordinate = int((screen_width/2) - (600/2))
    y_cordinate = int((screen_height/2) - (550/2))
    app.geometry("{}x{}+{}+{}".format(600, 550, x_cordinate, y_cordinate))


def read_config():
    #reading file contents
    with open(os.path.join(dir_path, "config.json"), "r") as js:
        config = json.load(js)
    light_theme = config["configuration"][0]["light-theme"]
    mode = config["configuration"][0]["selected-mode"]
    #if config.json gets corrupted switch back to dark theme mp4
    try:
        match light_theme:
            case "0":
                light_title_bar()
            case "1":
                dark_title_bar()
            case _:
                raise ValueError("Corrupted json, resetting values")
        main(app, main_frame, light_theme, mode)
    except ValueError:
        tk.messagebox.showerror("Error", "Configuration file is corrupted. Resetting to default values.")
        write_to_json("1", "mp4")
        main(app, main_frame, "1", "mp4")


def write_to_json(light_theme, selected_mode):
    config = {
            "configuration": [
                {
                    "light-theme": light_theme,
                    "selected-mode": selected_mode
                }
            ]
        }
    with open(os.path.join(dir_path, "config.json"), "w") as js:
            js.write(json.dumps(config, indent=4))


################## END OF FUNCTIONS ##################
######################################################
#################### TKINTER MAIN ####################


#creating app
app = tk.Tk()

#setting window attributes
app.title("MP3-MP4 Youtube Downloader")
app.geometry(f"{s_width}x{s_height}")
app.minsize(width=s_width, height=s_height)
app.iconbitmap(icon_path)
app.state("zoomed")

#PhotoImaging, resizing at the start the images
mp3_logo = tk.PhotoImage(file=os.path.join(assets_path, "mp3-logo.png"))
mp3_logo_xlarge = mp3_logo.subsample(2,2)
mp3_logo_large = mp3_logo.subsample(3,3)
mp3_logo_medium = mp3_logo.subsample(5,5)
mp3_logo_small = mp3_logo.subsample(7,7)
mp4_logo = tk.PhotoImage(file=os.path.join(assets_path, "mp4-logo.png"))
mp4_logo_xlarge = mp4_logo.subsample(2,2)
mp4_logo_large = mp4_logo.subsample(3,3)
mp4_logo_medium = mp4_logo.subsample(5,5)
mp4_logo_small = mp4_logo.subsample(7,7)

#setting main frame for better theme managment
main_frame = tk.Frame(app, background=background_color_dark)
main_frame.grid_columnconfigure(0, weight=1) #placing column 0 widgets in center
main_frame.pack(expand=True, fill="both")

#centering app, setting title bar theme before calling the main class
center_screen()
read_config()

# If you don't know what mainloop() does, it's time to brush up on your GUI programming basics!
app.tk.mainloop()