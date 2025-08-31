import time
import ctypes
import pygame
import threading
import serial
import serial.tools
import numpy as np
import requests

from sdk.vernier.bindings import GoIOSDK, SKIP_CMD_ID_START_MEASUREMENTS, SKIP_CMD_ID_STOP_MEASUREMENTS
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
from serial import Serial
from serial.tools import list_ports

# OpenBCI Cyton Daisy Board
class OpenBCI:
    def __init__(self):
        self.board = None
        self.filter = None
        self.channels = []
        self.last_sample = np.zeros(16)

    def find_serial_port(self):
        openbci_port = ''
        for port in list_ports.comports():
            try:
                s = Serial(port=port.device, baudrate=115200, timeout=10)
                s.write(b'v')
                time.sleep(2)
                if s.inWaiting():
                    line = ''
                    while '$$$' not in line:
                        line += s.read().decode('utf-8', errors='replace')
                    if "OpenBCI" in line:
                        openbci_port = port.device
                        s.close()
                        break
                s.close()
            except (OSError, serial.SerialException):
                pass

        return openbci_port

    def open(self):
        def worker():
            while self.board is None:
                try:
                    params = BrainFlowInputParams()
                    params.timeout = 30
                    params.serial_port = self.find_serial_port()

                    temp_board = BoardShim(BoardIds.CYTON_DAISY_BOARD.value, params)
                    # temp_board = BoardShim(BoardIds.SYNTHETIC_BOARD.value, params)
                    # temp_board.enable_dev_board_logger()
                    temp_board.prepare_session()
                    time.sleep(5)
                    temp_board.start_stream()
                    self.board = temp_board
                    self.channels = BoardShim.get_eeg_channels(self.board.board_id)
                    break
                except Exception as error:
                    print('failed connecting to OpenBCI port, retrying: ', error)

                time.sleep(0.5)

        threading.Thread(target=worker, daemon=True).start()
        return self

    def close(self):
        if self.board is not None:
            self.board.stop_stream()
            self.board.release_session()
        return self

    def get_data(self):
        if self.board is not None:
            latest = self.board.get_current_board_data(1)
            sample = np.squeeze(latest)[:len(self.channels)] * ((4500000)/24/(2**23-1))

            if sample.shape != (16,):
                sample = np.zeros(16)

            if self.filter is not None:
                sample = self.filter.apply(sample, 'eeg')

            self.last_sample = sample

        return self.last_sample

    def set_filter(self, _filter):
        self.filter = _filter
        return self


# Vernier hand dynamometer
class Vernier:
    def __init__(self):
        self.sensor = 0
        self.filter = None
        self.last_sample = 0

        self.lib = GoIOSDK().get_library()
        self.lib.GoIO_Init()

    def open(self):
        def worker():
            while self.sensor == 0:
                try:
                    time.sleep(0.5)
                    found, name, vendor, product = GoIOSDK().get_device()
                    if not found:
                        raise Exception("failed connecting to Vernier device, retrying.")

                    self.sensor = self.lib.GoIO_Sensor_Open(name.encode(), vendor, product, 0)
                    if self.sensor == 0:
                        raise Exception("failed to open Vernier sensor, retrying.")

                    char_id = ctypes.c_ubyte()
                    self.lib.GoIO_Sensor_DDSMem_GetSensorNumber(self.sensor, ctypes.byref(char_id), 0, 0)
                    self.lib.GoIO_Sensor_SendCmdAndGetResponse(self.sensor, SKIP_CMD_ID_START_MEASUREMENTS, None, 0,
                                                               None, None, 1000)
                    break
                except Exception as error:
                    print("error while connecting to Vernier device, retrying:", error)

                time.sleep(0.5)

        threading.Thread(target=worker, daemon=True).start()
        return self

    def close(self):
        if self.sensor != 0:
            self.lib.GoIO_Sensor_SendCmdAndGetResponse(self.sensor, SKIP_CMD_ID_STOP_MEASUREMENTS, None, 0, None, None,
                                                       500)
            time.sleep(0.5)
            self.lib.GoIO_Sensor_Close(self.sensor)
        return self

    def get_data(self):
        if self.sensor != 0 and self.lib.GoIO_Sensor_GetNumMeasurementsAvailable(self.sensor) > 0:
            latest = self.lib.GoIO_Sensor_GetLatestRawMeasurement(self.sensor)
            volts = self.lib.GoIO_Sensor_ConvertToVoltage(self.sensor, latest)
            sample = self.lib.GoIO_Sensor_CalibrateData(self.sensor, volts)

            if self.filter is not None:
                sample = self.filter.apply(sample, 'hd')

            self.last_sample = sample

        return self.last_sample

    def set_filter(self, _filter):
        self.filter = _filter
        return self


class Noraxon:
    def __init__(self):
        self.session = None
        self.address = None
        self.port = None
        self.filter = None
        self.last_sample = np.zeros(4)

    def open(self, address, port):
        self.address = address
        self.port = port

        def worker():
            while self.session is None:
                try:
                    temp_session = requests.Session()
                    headers = temp_session.get(f"http://{address}:{port}/headers")
                    
                    print(headers.json()["headers"])

                    if len(headers.json()["headers"]) != 4:
                        raise Exception(f"expected 4 emg sensors, got {len(headers.json()['headers'])}")
                    else:
                        enabled = temp_session.get(f"http://{address}:{port}/enable/all")

                        if enabled.status_code != 200:
                            raise Exception("failed to enable all channels.")

                    self.session = temp_session
                    break
                except Exception as error:
                    print(f"failed connecting to Noraxon stream, retrying: {error}")

                time.sleep(0.5)

        threading.Thread(target=worker, daemon=True).start()
        return self

    def close(self):
        if self.session is not None:
            disable = self.session.get(f"http://{self.address}:{self.port}/disable/all")
            if disable.status_code != 200:
                raise Exception("failed to disable all channels.")
            self.session.close()
        return self

    def get_data(self):
        if self.session is not None:
            data = self.session.get(f"http://{self.address}:{self.port}/samples")

            if data.status_code == 200:
                channels = data.json()["channels"]

                sample = np.zeros(4)
                
                for _, channel in enumerate(channels):
                    index = channel["index"]
                    latest = channel["samples"][-1]
                    sample[index] = latest

                if self.filter is not None:
                    sample = self.filter.apply(sample, 'emg')

                self.last_sample = sample

        return self.last_sample

    def set_filter(self, _filter):
        self.filter = _filter
        return self


class Joystick:
    def __init__(self):
        self.joystick = None
        self.filter = None
        self.last_sample = np.zeros(2, dtype=np.float64)

    def open(self):
        pygame.joystick.init()
        pygame.display.set_mode((100, 100))

        def worker():
            while self.joystick is None:
                try:
                    if pygame.joystick.get_count() > 0:
                        temp_joystick = pygame.joystick.Joystick(0)
                        temp_joystick.init()

                        if temp_joystick.get_numaxes() < 2:
                            raise Exception("joystick should have at-least 2 axes")

                        print(f"connected to joystick: {temp_joystick.get_name()}")
                        self.joystick = temp_joystick
                        break
                    else:
                        raise Exception("no joystick found")
                except Exception as error:
                    print(f"failed connecting to joystick, retrying: {error}")

                time.sleep(0.5)

        threading.Thread(target=worker, daemon=True).start()
        return self

    def close(self):
        if self.joystick is not None:
            self.joystick.quit()
        return self

    def get_data(self):
        if self.joystick is not None:
            pygame.event.pump()
            sample = np.array([self.joystick.get_axis(0), self.joystick.get_axis(1) * -1] , dtype=np.float64)

            if self.filter is not None:
                sample = self.filter.apply(sample, 'joystick')

            self.last_sample = sample

        return self.last_sample

    def set_filter(self, _filter):
        self.filter = _filter
        return self
