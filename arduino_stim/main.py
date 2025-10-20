import threading
import time

import pylsl
import serial
import tomllib
from dareplane_utils.logging.logger import get_logger
from dareplane_utils.stream_watcher.lsl_stream_watcher import StreamWatcher
from fire import Fire

from arduino_stim.utils.time import sleep_s

logger = get_logger("arduino_stim")


def init_lsl_outlet() -> pylsl.StreamOutlet:
    """    
    Initializes an LSL outlet to stream Arduino commands as a single-channel stream.

    This function creates an LSL outlet named ``arduino_cmd`` with a single channel of type "Marker" and format "int32".
    The sample rate is set to 0, indicating an irregular stream.

    Returns
    -------
    pylsl.StreamOutlet
        The LSL outlet for streaming the Arduino commands.
    """
    n_channels = 1
    info = pylsl.StreamInfo(
        "arduino_cmd",
        "Marker",
        n_channels,
        0,  # srate = 0 --> irregular stream
        "int32",
    )

    # enrich a channel name
    chns = info.desc().append_child("channels")
    ch = chns.append_child("channel")
    ch.append_child_value("label", "arduino_stim")
    ch.append_child_value("unit", "AU")
    ch.append_child_value("type", "arduino_stim")
    ch.append_child_value("scaling_factor", "1")

    outlet = pylsl.StreamOutlet(info)

    return outlet


def connect_stream_watcher(config: dict) -> StreamWatcher:
    """
    Connect to and configure the input stream watcher.

    This function initializes a StreamWatcher to monitor an input LSL stream.

    Parameters
    ----------
    config : dict
        Configuration dictionary containing stream connection settings.

    Returns
    -------
    StreamWatcher
        Connected StreamWatcher instance ready for data monitoring.
    """
    sw = StreamWatcher(
        config["stream_to_query"]["stream"],
        buffer_size_s=config["stream_to_query"]["buffer_size_s"],
    )
    sw.connect_to_stream()

    return sw


def lsl_delay(dt_us: int = 0):
    tstart = pylsl.local_clock()
    while pylsl.local_clock() - tstart < dt_us / 1e6:
        pass


def main(
    stop_event: threading.Event = threading.Event(), logger_level: int = 10
):
    """
    The Arduino stimulator main loop.

    Watches an input LSL stream, processes the data, and sends a signal to the Arduino over a serial connection,
    as well as the ``arduino_cmd`` LSL outlet. The stream to watch, buffer size, grace period, Arduino port and the Arduino baudrate are defined in the configuration file.

    The loop runs until ``stop_event`` is set.

    Parameters
    ----------
    stop_event : threading.Event, optional
        Event used to terminate the loop from another thread. If not provided, a new one is created.
    logger_level : int, optional
        Logging level passed to the module logger (e.g., 10=DEBUG, 20=INFO). Default is 10.

    Returns
    -------
    None

    Notes
    -----
    - Configuration is loaded from ``./configs/arduino_stim_sim_config.toml``.
    """

    logger.setLevel(logger_level)
    config = tomllib.load(open("./configs/arduino_stim_sim_config.toml", "rb"))
    sw = connect_stream_watcher(config)

    outlet = init_lsl_outlet()

    last_val = 0

    tlast = time.perf_counter_ns()
    dt_us = 100  # for update polling

    acfg = config["arduino"]
    with serial.Serial(
        port=acfg["port"], baudrate=acfg["baudrate"], timeout=0.1
    ) as arduino:
        while not stop_event.is_set() and arduino is not None:
            # limit the update rate
            if time.perf_counter_ns() - tlast > dt_us * 1e3:
                sw.update()
                dt_ms = (time.perf_counter_ns() - tlast) / 1e6

                if sw.n_new > 0 and dt_ms > config["stimulation"]["grace_period_ms"]:
                    val = sw.unfold_buffer()[-1]

                    # Process the incoming data and send commands
                    #  implement your controller logic here
                    if val != last_val and len(val) == 1:
                        ival = int(val[0])
                        if ival > 127:
                            # print("Pushing up-down")
                            arduino.write("u\n".encode())
                            arduino.write("d\n".encode())

                        outlet.push_sample([ival])

                        sw.n_new = 0
                        last_val = val
                        tlast = time.perf_counter_ns()

                        sleep_s(dt_us * 1e-6 * 0.9)


def get_main_thread() -> tuple[threading.Thread, threading.Event]:
    """
    Run the main loop in a separate thread.

    This function creates and starts a background thread that runs the main
    arduino stimulator loop. It allows the Arduino controller to be stopped via 
    the returned Event object.

    Returns
    -------
    tuple[threading.Thread, threading.Event]
        A tuple containing:
        - threading.Thread: The thread object running the main loop
        - threading.Event: Event object that can be .set() to stop the main loop
    """
    stop_event = threading.Event()
    stop_event.clear()

    thread = threading.Thread(target=main, kwargs={"stop_event": stop_event})
    thread.start()

    return thread, stop_event


def write_and_read(arduino: serial.Serial, message: str):
    tpre = time.time_ns()

    while time.time_ns() - tpre < 10_000_000_000:
        arduino.write("u\n".encode())
        arduino.write("d\n".encode())
    # l = arduino.readline()
    # #
    # tfirst = time.time_ns()
    # print(f"{tfirst-tpre=}")
    # l2 = arduino.readline()
    # tsecond = time.time_ns()
    #
    # l = l.decode()
    # l2 = l2.decode()
    #
    # retstr = f"{l=} {l2=} {tsecond-tfirst=} {tfirst-tpre=} {tsecond-tpre=}"
    # print(retstr)


# In [89]: %timeit arduino.write('u'.encode())
# 520 µs ± 19.7 ns per loop (mean ± std. dev. of 7 runs, 1,000 loops ea
# ch)
# Also the full cycle seems to be about 520us as tested with the oscilloscope and this:
#
# while time.time_ns() - tpre < 10_000_000_000:
#     arduino.write('u'.encode())
#     arduino.write('d'.encode())

if __name__ == "__main__":
    Fire(main)
