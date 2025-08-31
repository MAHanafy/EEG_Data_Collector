import time
import threading
import numpy as np

from utils.globals import openbci, vernier, noraxon, joystick

SAMPLE_RATE = 125


class CARLStream:
    def __init__(self):
        """
        Data layout:
        0-15, EEG data (16 channels)
        16-19, EMG data (4 channels)
        20-21, JOYSTICK (x,y)
        22, FORCE
        23-27, FEATURES (Features used by experiments, example: cue)
        28, TIMESTAMP
        """

        self.data = []
        self.features = np.zeros(5)
        self.running = False

    def start(self):
        """This method creates a stream and collects all data and features at 125Hz."""
        self.running = True

        def worker():
            perf_counter_ns = time.perf_counter_ns
            time_ns = time.time_ns
            np_hstack = np.hstack

            target = (1 / SAMPLE_RATE) * (10 ** 9)
            start = perf_counter_ns()
            count = 0

            while self.running:
                now = perf_counter_ns()
                next_sample = start + (target * count)

                if now > next_sample:
                    self.data.append(np_hstack([openbci.get_data(), noraxon.get_data(), joystick.get_data(),
                                                vernier.get_data(), self.features, time_ns()]))
                    count += 1

                time.sleep(0.00001)

            end = perf_counter_ns()
            print(f"CARLStream stopped at frequency of {(count / ((end - start) / 1_000_000_000)):.3f}hz")

        threading.Thread(target=worker, daemon=True).start()

    def set_feature(self, index, value):
        """This method sets a feature by index."""
        if index > 5 or index < 0:
            raise ValueError("CARLStream: feature index out of bounds.")
        self.features[index] = value

    def stop(self):
        """This method stops the stream."""
        self.running = False

    def save(self, filename, params=None):
        """This method saves the data to a file."""
        np_data = np.array(self.data)
        np.savez(filename, data=np_data, params=params)
        print(f"CARLStream saved file of shape {np_data.shape} to {filename}.")
        self.data = np.empty(SAMPLE_RATE * 5, dtype=object)