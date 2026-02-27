"""
Live OpenBCI Cyton+Daisy stream -> terminal table + sliding window builder.

This script REUSES the existing OpenBCI connection logic in this repo
(`utils.devices.OpenBCI` via `utils.globals.openbci`), instead of creating a
second BrainFlow session. That means:

- Same serial-port discovery logic as the GUI / EXP3.
- Same channel filtering and clamping configured in `filter.json`.

What it does:
    - Waits for the global `openbci` instance to connect to the Cyton+Daisy.
    - Samples the 16 EEG channels continuously via `openbci.get_data()`.
    - Maintains a ring buffer of the most recent samples.
    - Builds overlapping sliding windows suitable for ML input.
    - Prints a small live table of recent samples in the terminal.

Usage:
    1. Make sure your board and dongle are powered and connected.
    2. (Optional) Launch the GUI once to apply channel filters if you use them.
    3. Run:

           python tools/stream_window_table.py

    4. Watch the terminal for:
        - Live updates of the last few samples.
        - Periodic "Window #N" messages with basic stats.

Windowing defaults:
    SAMPLE_RATE_HZ   = 125       # Cyton+Daisy nominal sampling rate
    WINDOW_SIZE_SEC  = 2.0       # 2 seconds  -> 250 samples
    WINDOW_STEP_SEC  = 0.25      # hop        -> 31 samples

    - windows in samples_first shape:  (250, 16)
    - and channels_first shape:        (16, 250)
"""

import os
import time
from collections import deque

import numpy as np
from brainflow.board_shim import BoardShim

from utils.globals import openbci


# =========================
# CONFIG
# =========================

# Visual table
PRINT_EVERY_SEC = 1.0          # how often to refresh the table
DISPLAY_ROWS = 10              # number of recent samples shown
DISPLAY_CHANNELS = 6           # show first N EEG channels (out of 16)

# Windowing (for ML input)
WINDOW_SIZE_SEC = 2.0          # 2 seconds -> ~2 * sampling_rate samples
WINDOW_STEP_SEC = 0.25         # hop in seconds; converted to fractional samples at runtime

# Buffering (keep enough for windowing)
BUFFER_SECONDS = 10


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def format_table(rows: np.ndarray, header: list[str]) -> str:
    """Pretty-print a small numeric table for the terminal."""
    col_widths = [len(h) for h in header]
    for r in rows:
        for i, val in enumerate(r):
            col_widths[i] = max(col_widths[i], len(str(val)))

    def fmt_row(items):
        return " | ".join(str(x).rjust(col_widths[i]) for i, x in enumerate(items))

    sep = "-+-".join("-" * w for w in col_widths)
    out = [fmt_row(header), sep]
    out.extend(fmt_row(r) for r in rows)
    return "\n".join(out)


def build_window_from_buffer(
    eeg_buffer: deque, ts_buffer: deque, window_samples: int
) -> tuple[np.ndarray, np.ndarray] | tuple[None, None]:
    """
    Returns a window in samples_first shape: (window_samples, channels) and the
    corresponding timestamp vector of shape (window_samples,).

    eeg_buffer items are expected to be 1D arrays of shape (channels,).
    """
    if len(eeg_buffer) < window_samples:
        return None, None

    # Take the last `window_samples` entries from both buffers
    eeg_window = np.array(list(eeg_buffer)[-window_samples:])  # (window_samples, channels)
    ts_window = np.array(list(ts_buffer)[-window_samples:])    # (window_samples,)
    return eeg_window, ts_window


def wait_for_openbci(timeout_sec: float = 60.0) -> bool:
    """
    Wait until the global `openbci` instance has a live BrainFlow board.

    Returns True if connected within timeout, False otherwise.
    """
    start = time.time()
    while openbci.board is None and (time.time() - start) < timeout_sec:
        print("Waiting for OpenBCI connection...", end="\r")
        time.sleep(0.5)

    if openbci.board is None:
        print("\nFailed to detect an active OpenBCI board in time.")
        return False

    print("\nOpenBCI board detected.")
    return True


def main():
    # Ensure the shared OpenBCI instance is ready
    if not wait_for_openbci():
        return

    sampling_rate = BoardShim.get_sampling_rate(openbci.board.board_id)
    window_samples = int(round(WINDOW_SIZE_SEC * sampling_rate))
    step_samples_float = WINDOW_STEP_SEC * sampling_rate
    buffer_max_samples = int(BUFFER_SECONDS * sampling_rate)

    # Ring buffers
    eeg_buffer = deque(maxlen=buffer_max_samples)  # each item: np.array shape (16,)
    ts_buffer = deque(maxlen=buffer_max_samples)   # each item: float timestamp

    # Windowing counters
    samples_since_last_window = 0.0
    window_count = 0
    last_table_print = time.time()

    print(
        f"Streaming from OpenBCI via `utils.globals.openbci` "
        f"@ ~{sampling_rate} Hz, "
        f"window={WINDOW_SIZE_SEC}s, step={WINDOW_STEP_SEC}s."
    )

    try:
        while True:
            # NOTE: `get_data()` internally pulls from BrainFlow and applies filters.
            sample = openbci.get_data()  # shape (16,)
            ts = time.time()

            eeg_buffer.append(sample.copy())
            ts_buffer.append(ts)
            samples_since_last_window += 1.0

            # =========================
            # WINDOW BUILDING
            # =========================
            while samples_since_last_window >= step_samples_float:
                samples_since_last_window -= step_samples_float

                window_samples_first, ts_window = build_window_from_buffer(
                    eeg_buffer, ts_buffer, window_samples
                )
                if window_samples_first is None:
                    break

                # Shapes for ML models:
                # (250, 16) samples_first
                # (16, 250) channels_first
                window_channels_first = window_samples_first.T
                window_count += 1

                window_start_ts = float(ts_window[0])
                window_end_ts = float(ts_window[-1])
                w_min = float(window_samples_first.min())
                w_max = float(window_samples_first.max())
                print(
                    f"Window #{window_count}: "
                    f"samples_first={window_samples_first.shape} | "
                    f"channels_first={window_channels_first.shape} | "
                    f"range=[{w_min:.2f}, {w_max:.2f}] | "
                    f"time=[{window_start_ts:.3f}, {window_end_ts:.3f}]"
                )

                # Here is where you would plug in your ML model, e.g.:
                # prediction = model.predict(window_channels_first[None, ...])
                # print('Prediction:', prediction)

            # =========================
            # LIVE TABLE PRINT
            # =========================
            now = time.time()
            if now - last_table_print >= PRINT_EVERY_SEC:
                last_table_print = now
                clear_screen()

                n = min(DISPLAY_ROWS, len(eeg_buffer))
                if n == 0:
                    print("No data received yet...")
                    time.sleep(0.01)
                    continue

                eeg_recent = np.array(list(eeg_buffer)[-n:])  # (n, 16)
                ts_recent = np.array(list(ts_buffer)[-n:])    # (n,)

                ch_n = min(DISPLAY_CHANNELS, eeg_recent.shape[1])
                rows = []
                for i in range(n):
                    row = [f"{ts_recent[i]:.3f}"] + [f"{eeg_recent[i, c]:.2f}" for c in range(ch_n)]
                    rows.append(row)
                rows = np.array(rows, dtype=object)

                header = ["timestamp"] + [f"EEG{c + 1}" for c in range(ch_n)]
                table = format_table(rows, header)

                print("OpenBCI Cyton+Daisy Live Stream (from utils.globals.openbci)")
                print(f"Nominal rate: {sampling_rate} Hz")
                print(
                    f"Window: {WINDOW_SIZE_SEC}s (~{window_samples} samples) | "
                    f"Step: {WINDOW_STEP_SEC}s (~{step_samples_float:.2f} samples)"
                )
                print(f"Built windows so far: {window_count}")
                print(f"Buffer size: {len(eeg_buffer)} samples\n")
                print(table)

                recent_min = float(np.min(eeg_recent[:, :ch_n]))
                recent_max = float(np.max(eeg_recent[:, :ch_n]))
                print(f"\nRecent range (shown channels): [{recent_min:.2f}, {recent_max:.2f}]")

            # Throttle the polling loop a bit; the actual rate is governed by the board.
            time.sleep(1.0 / sampling_rate / 2.0)

    except KeyboardInterrupt:
        print("\nStopping (Ctrl+C)...")


if __name__ == "__main__":
    main()

