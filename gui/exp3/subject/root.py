import random
import time
import pickle
import os
from datetime import datetime

from tkinter import *
from tkinter.ttk import Progressbar
from utils.stream import CARLStream
from gui.exp3.config import Config

"""
0 = resting, subject has both arms on a chair with an arm rest, the wrist is extending out of the arm rest, parallel to the forearm. (stop)
1 = subject is imagining clenching the left hand as tight as they can
2 = subject is imagining clenching the right hand as tight as they can
3 = subject is imagining plantar of the left foot
4 = subject is imagining plantar flexion of the right foot
"""


class SubjectInterface(Toplevel):
    def __init__(self, master):
        super().__init__()

        self.master = master
        self.title("Subject interface")
        self.config(background="white")
        self.attributes("-topmost", True)
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.resizable = (False, False)
        self.geometry("800x600")

        self.subject = Config().load()
        self.stream = CARLStream()

        self.step = 0
        self.phase = 0
        self.stamp = 0
        self.target = 0
        self.running = True

        self.levels = []

        # set up levels
        self.levels = ([1, 2] * self.subject.cues)[:self.subject.cues]
        if self.subject.run_type != "Demo":
            random.shuffle(self.levels)

        self.images = [
            PhotoImage(file="./gui/exp3/resources/resting.png"),                 # Resting (0)
            PhotoImage(file="./gui/exp3/resources/left_hand_clench.png"),        # Left hand clench (1)
            PhotoImage(file="./gui/exp3/resources/right_hand_clench.png"),       # Right hand clench (2)
            PhotoImage(file="./gui/exp3/resources/left_foot_plantar.png"),  # Left foot dorsiflexion (3)
            PhotoImage(file="./gui/exp3/resources/right_foot_plantar.png")  # Right foot dorsiflexion (4)
        ]

        self.targets = [
            "Resting",
            "Left hand clench",
            "Right hand clench",
            "Left foot plantar flexion",
            "Right foot plantar flexion"
        ]

        self._create_widgets()

    def _close(self):
        """This method is called when the window is closed."""
        self.master.subject_window = None
        self.destroy()

    def _create_widgets(self):
        """This method creates the widgets of the window."""

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=10)
        self.grid_columnconfigure(0, weight=1)

        # Header frame
        self.header_label = Label(self, text="Loading...", background='black',
                                  foreground='white')
        self.header_label.grid(row=0, column=0, columnspan=2, sticky='nsew')

        # Image
        self.image_frame = Frame(self, background='black', highlightbackground="red",
                                      highlightcolor="red", highlightthickness=1)
        self.image = Label(self.image_frame, image=None, background='black')
        self.image_frame.grid(row=1, column=0, sticky='nsew')
        self.image.pack(padx=0)

        # Countdown label (3, 2, 1)
        self.countdown_label = Label(self, text="", background='black', foreground='yellow',
                                     font=("Arial", 72, "bold"))
        
        # Progress bar for task phase
        self.progress_frame = Frame(self, background='black')
        self.progress_frame.grid(row=2, column=0, sticky='ew', padx=20, pady=10)
        self.progress_bar = Progressbar(self.progress_frame, orient=HORIZONTAL, length=400, mode='determinate')
        self.progress_bar.pack(fill=X, padx=20)
        self.progress_frame.grid_remove()  # Hide initially

        if self.subject.run_type != "Demo":
            self.stream.start()
        self._loop()

    def _render(self):
        """This method renders the current stage of the experiment."""
        if self.step >= len(self.levels):
            self.header_label.config(text="Done")
            self.countdown_label.place_forget()
            self.progress_frame.grid_remove()

            if self.subject.run_type != "Demo":
                self.stream.stop()
                data_filename = f"./data/EXP3_SUBJECT{self.subject.id}_{self.subject.run_type}_{self.subject.run}"
                self.stream.save(
                    f"{data_filename}.npz",
                    params=pickle.dumps(self.subject.__dict__))
                
                # Save log file with subject name and date
                self._save_log_file(data_filename)

            self.running = False
            return

        if self.stamp == 0:
            self.stamp = time.perf_counter()

        delta_stamp = time.perf_counter() - self.stamp
        str_step = f"{self.step + 1}/{len(self.levels)}"

        self.image.config(image=self.images[self.target])

        self.stream.set_feature(0, self.target)
        self.stream.set_feature(1, self.phase)

        if self.phase == 0:
            # Hide progress bar during planning
            self.progress_frame.grid_remove()
            
            time_remaining = self.subject.time_plan - delta_stamp
            
            if delta_stamp >= self.subject.time_plan:
                self.phase = 1
                self.stamp = time.perf_counter()
                self.countdown_label.place_forget()
                return

            self.target = self.levels[self.step]
            
            # Show countdown (3, 2, 1) in the last 3 seconds of planning
            if time_remaining <= 3 and time_remaining > 0:
                countdown_num = int(time_remaining) + 1
                if countdown_num <= 3:
                    self.countdown_label.config(text=str(countdown_num))
                    self.countdown_label.place(relx=0.5, rely=0.5, anchor=CENTER)
            else:
                self.countdown_label.place_forget()
            
            self.header_label.config(
                text=f"Planning {int(time_remaining) + 1} | Step: {str_step} | Target: {self.targets[self.levels[self.step]]}")

        if self.phase == 1:
            # Show progress bar during task
            self.progress_frame.grid()
            self.countdown_label.place_forget()
            
            # Update progress bar
            progress_percent = (delta_stamp / self.subject.time_task) * 100
            self.progress_bar['value'] = min(progress_percent, 100)
            
            if delta_stamp >= self.subject.time_task:
                self.target = 0
                self.phase = 2
                self.stamp = time.perf_counter()
                self.image_frame.config(highlightbackground="red", highlightcolor="red")
                self.progress_frame.grid_remove()
                self.progress_bar['value'] = 0
                return

            self.header_label.config(
                text=f"Task: {self.subject.time_task - int(delta_stamp)} | Step: {str_step} | Target: {self.targets[self.levels[self.step]]}")
            self.image_frame.config(highlightbackground="green", highlightcolor="green")

        if self.phase == 2:
            # Hide progress bar during rest
            self.progress_frame.grid_remove()
            
            if delta_stamp >= self.subject.time_rest:
                self.phase = 0
                self.stamp = time.perf_counter()
                self.step += 1
                return

            self.header_label.config(
                text=f"Rest: {self.subject.time_rest - int(delta_stamp)} | Step: {str_step}")

    def _save_log_file(self, data_filename):
        """Save a log file with subject name, date, and experiment details."""
        log_filename = f"{data_filename}.log"
        with open(log_filename, 'w') as log_file:
            log_file.write(f"=== EEG Experiment Log ===\n")
            log_file.write(f"Subject Name: {self.subject.subject_name}\n")
            log_file.write(f"Date: {self.subject.date}\n")
            log_file.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            log_file.write(f"\n=== Session Parameters ===\n")
            log_file.write(f"Subject ID: {self.subject.id}\n")
            log_file.write(f"Run: {self.subject.run}\n")
            log_file.write(f"Run Type: {self.subject.run_type}\n")
            log_file.write(f"Number of Cues: {self.subject.cues}\n")
            log_file.write(f"Planning Time: {self.subject.time_plan}s\n")
            log_file.write(f"Task Time: {self.subject.time_task}s\n")
            log_file.write(f"Rest Time: {self.subject.time_rest}s\n")
            log_file.write(f"\n=== Data File ===\n")
            log_file.write(f"Data File: {data_filename}.npz\n")
        print(f"Log file saved to {log_filename}")

    def _loop(self):
        """This method is the main loop of the window."""
        if self.running:
            self._render()
            self.after(8, self._loop)
