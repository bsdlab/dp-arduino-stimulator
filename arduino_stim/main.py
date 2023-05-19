import serial
import threading
import tomllib
import pylsl

from fire import Fire
from dareplane_utils.stream_watcher.lsl_stream_watcher import StreamWatcher
from dareplane_utils.logging.logger import get_logger

logger = get_logger("arduino_stim")


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


def main(
    stop_event: threading.Event = threading.Event(), logger_level: int = 10
):
    logger.setLevel(logger_level)
    config = tomllib.load(open("./configs/arduino_stim_sim_config.toml", "rb"))
    sw = connect_stream_watcher(config)

    last_val = 0

    acfg = config["arduino"]
    with serial.Serial(
        port=acfg["port"], baudrate=acfg["baudrate"], timeout=0.1
    ) as arduino:
        while not stop_event.is_set() and arduino is not None:
            sw.update()
            if sw.n_new > 0:
                if "delay_s" in config["stimulation"].keys():
                    lsl_delay(config["stimulation"]["delay_s"])
                val = sw.unfold_buffer()[0]
                print(f"{val} - {last_val}")
                if val != last_val and len(val) == 1:
                    arduino.write(f"{int(val[0])}\n".encode())
                    sw.n_new = 0
                    last_val = val


def get_main_thread() -> tuple[threading.Thread, threading.Event]:
    stop_event = threading.Event()
    stop_event.clear()

    thread = threading.Thread(target=main, kwargs={"stop_event": stop_event})
    thread.start()

    return thread, stop_event


if __name__ == "__main__":
    Fire(main)
