from tkinter import *
from tkinter.ttk import *

from gui.eeg import EEGTab
from gui.hd import HDTab
from gui.emg import EMGTab
from gui.joystick import JoystickTab
from gui.channels import ChannelsTab
from gui.exp3.root import EXP3Tab
from utils.globals import openbci, vernier, noraxon, joystick


class Window:
    def __init__(self):
        self.master = Tk()

        self.master.title("Data collection UI")
        self.master.configure(background="white")
        self.master.geometry("800x600")
        self.master.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.master.resizable(False, False)

        self.tabcontrol = Notebook(self.master)
        self.tabcontrol.pack(expand=1, fill='both')

        self.tabs = [EEGTab(self.tabcontrol), HDTab(self.tabcontrol), EMGTab(self.tabcontrol),
                     JoystickTab(self.tabcontrol), ChannelsTab(self.tabcontrol), EXP3Tab(self.tabcontrol)]

        for tab in self.tabs:
            self.tabcontrol.add(tab, text=tab.name)

    def _on_closing(self):
        """Stop all devices and close the application."""
        try:
            self.master.quit()
            self.master.destroy()

            openbci.close()
            vernier.close()
            noraxon.close()
            joystick.close()
        except:
            exit(1)

    def start(self):
        """Run the main gui event loop."""
        self.master.mainloop()
