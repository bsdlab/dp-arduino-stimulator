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


def main(stop_event: threading.Event = threading.Event(), logger_level: int = 10):
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

                    if val != last_val and len(val) == 1:
                        ival = int(val[0])
                        if ival > 127:
                            arduino.write("u\n".encode())
                            arduino.write("d\n".encode())

                        outlet.push_sample([ival])

                        sw.n_new = 0
                        last_val = val
                        tlast = time.perf_counter_ns()

                        sleep_s(dt_us * 1e-6 * 0.9)


def get_main_thread() -> tuple[threading.Thread, threading.Event]:
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


if __name__ == "__main__":
    Fire(main)
