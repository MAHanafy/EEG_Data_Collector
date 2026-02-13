import numpy as np

from tkinter import *
from matplotlib import animation
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from utils.globals import openbci


class EEGTab(Frame):
    def __init__(self, notebook):
        super().__init__(notebook)

        self.name = "EEG"
        self.anim = None
        self.values = np.zeros(16)

        self._create_widgets()

        self.bind("<Map>", self._start_animation)
        self.bind("<Unmap>", self._stop_animation)

    def _start_animation(self, event):
        """Start the animation when the tab becomes visible."""
        if self.anim is None:
            self.anim = animation.FuncAnimation(self.figure, self._update_canvas, blit=True, cache_frame_data=False, interval=1000/60)
        else:
            self.anim.event_source.start()

    def _stop_animation(self, event):
        """Stop the animation when the tab is hidden."""
        if self.anim is not None:
            self.anim.event_source.stop()

    def _update_canvas(self, frame):
        """Update function for FuncAnimation to dynamically update the canvas."""
        for bar, value in zip(self.bars, openbci.get_data()):
            if bar.get_height() != value:
                bar.set_height(value)

        return self.bars
        
    def _bci_callback(self, sample):
        """This method is called every time a new sample is ready from the OpenBCI device, it sets the latest sample."""
        self.values = sample
        print(sample)

    def _create_widgets(self):
        """Create the widgets for the tab."""
        self.figure = Figure(constrained_layout=True)
        self.ax = self.figure.add_subplot(1, 1, 1)
        self.bars = self.ax.bar(np.arange(16) + 1, self.values, edgecolor='black')

        self.ax.set_title('EEG data')
        self.ax.set_xlabel('Channel')
        self.ax.set_ylabel('Activity (µV)')
        self.ax.set_ylim(-2000, 2000)
        self.ax.set_xlim(0.5, 16.5)
        self.ax.set_xticks(np.arange(16) + 1)
        
        self.canvas = FigureCanvasTkAgg(self.figure, self)
        self.canvas.get_tk_widget().pack()