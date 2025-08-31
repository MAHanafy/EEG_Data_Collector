import random
import time
import pickle

from tkinter import *
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
        self.levels = ([1, 2, 3, 4] * self.subject.cues)[:self.subject.cues]
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


        if self.subject.run_type != "Demo":
            self.stream.start()
        self._loop()

    def _render(self):
        """This method renders the current stage of the experiment."""
        if self.step >= len(self.levels):
            self.header_label.config(text="Done")

            if self.subject.run_type != "Demo":
                self.stream.stop()
                self.stream.save(
                    f"./data/EXP3_SUBJECT{self.subject.id}_{self.subject.run_type}_{self.subject.run}.npz",
                    params=pickle.dumps(self.subject.__dict__))

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
            if delta_stamp >= self.subject.time_plan:
                self.phase = 1
                self.stamp = time.perf_counter()
                return

            self.target = self.levels[self.step]
            self.header_label.config(
                text=f"Planning {self.subject.time_plan - int(delta_stamp)} | Step: {str_step} | Target: {self.targets[self.levels[self.step]]}")

        if self.phase == 1:
            if delta_stamp >= self.subject.time_task:
                self.target = 0
                self.phase = 2
                self.stamp = time.perf_counter()
                self.image_frame.config(highlightbackground="red", highlightcolor="red")
                return

            self.header_label.config(
                text=f"Task: {self.subject.time_task - int(delta_stamp)} | Step: {str_step} | Target: {self.targets[self.levels[self.step]]}")
            self.image_frame.config(highlightbackground="green", highlightcolor="green")

        if self.phase == 2:
            if delta_stamp >= self.subject.time_rest:
                self.phase = 0
                self.stamp = time.perf_counter()
                self.step += 1
                return

            self.header_label.config(
                text=f"Rest: {self.subject.time_rest - int(delta_stamp)} | Step: {str_step}")

    def _loop(self):
        """This method is the main loop of the window."""
        if self.running:
            self._render()
            self.after(8, self._loop)
