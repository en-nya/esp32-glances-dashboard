import time

from config import REFRESH_INTERVAL_SECONDS
from lib.display import Display
from lib.glances_client import GlancesClient


def format_percent(value):
    if value is None:
        return "--"
    return "{:.1f}%".format(value)


def main():
    display = Display()
    client = GlancesClient()

    display.show_message("Glances dashboard starting")

    while True:
        try:
            status = client.fetch_summary()
            line = "CPU {} | MEM {} | DISK {}".format(
                format_percent(status.get("cpu_percent")),
                format_percent(status.get("mem_percent")),
                format_percent(status.get("disk_percent")),
            )
            print(line)
            display.show_message(line)
        except Exception as exc:
            message = "Glances error: {}".format(exc)
            print(message)
            display.show_message(message)

        time.sleep(REFRESH_INTERVAL_SECONDS)


main()
