# SPDX-License-Identifier: AGPL-3.0-or-later
def mount_sd():
    import machine
    import os
    from lib.pins import SD_CS, SD_SCK, SD_MISO, SD_MOSI

    try:
        import sdcard
        spi = machine.SPI(2, baudrate=4000000, polarity=0, phase=0,
                         sck=machine.Pin(SD_SCK), mosi=machine.Pin(SD_MOSI), miso=machine.Pin(SD_MISO))
        sd = sdcard.SDCard(spi, machine.Pin(SD_CS))
        os.mount(sd, "/sd")
        return True
    except Exception:
        return False
