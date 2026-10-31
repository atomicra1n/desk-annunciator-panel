import busio
import digitalio
import board
import time

# shift register
spi = busio.SPI(clock=board.GP18, MOSI=board.GP19)
while not spi.try_lock():
    pass
spi.configure(baudrate=1000000, polarity=0, phase=0)

latch = digitalio.DigitalInOut(board.GP17)
latch.direction = digitalio.Direction.OUTPUT

oe = digitalio.DigitalInOut(board.GP16)
oe.direction = digitalio.Direction.OUTPUT
oe.value = True

# each tile can be OFF, FLASH, STEADY or RING with OFF not alarming, FLASH being a new alarm, with a fast blinking (pending ack), STEADY = alarm acknowledged and staying solid on and RING = condition cleared slow blink (needs RESET)
states = ["OFF"] * 12
conditions = [False] * 12

# flashing
flash_on = False
ring_on = False
last_flash = 0
last_ring = 0

def setup():
    oe.value = False

def shift_out(tiles):
    # tiles is a list of 12 booleans
    # we need to convert to 2 bytes for the shift registers
    # tiles 0-7 go to U1 shift register and tiles 8-11 go to U2
    # the white row (8-11) has transistors so the logic is flipped!!!!!!
    bits = 0
    for i in range(12):
        if tiles[i]:
            if i >= 8:
                bits = bits | (1 << i)
            else:
                pass
        else:
            if i >= 8:
                pass
            else:
                bits = bits | (1 << i)

    lo = bits & 0xFF
    hi = (bits >> 8) & 0xFF
    latch.value = False
    spi.write(bytes([hi, lo]))
    latch.value = True

def set_condition(tile, active):
    old = conditions[tile]
    conditions[tile] = active

    if active and not old:
        if states[tile] == "OFF" or states[tile] == "RING":
            states[tile] = "FLASH"
    elif not active and old:
        if states[tile] == "FLASH" or states[tile] == "STEADY":
            states[tile] = "RING"

def ack():
    for i in range(12):
        if states[i] == "FLASH":
            states[i] = "STEADY"

def reset():
    for i in range(12):
        if states[i] == "RING":
            states[i] = "OFF"

def any_flashing():
    for i in range(12):
        if states[i] == "FLASH":
            return True
    return False

def any_ringing():
    for i in range(12):
        if states[i] == "RING":
            return True
    return False

def update():
    global flash_on, ring_on, last_flash, last_ring

    now = time.monotonic()
    if now - last_flash >= 0.125:
        flash_on = not flash_on
        last_flash = now
    if now - last_ring >= 0.5:
        ring_on = not ring_on
        last_ring = now

    out = [False] * 12
    for i in range(12):
        if states[i] == "STEADY":
            out[i] = True
        elif states[i] == "FLASH":
            out[i] = flash_on
        elif states[i] == "RING":
            out[i] = ring_on
    shift_out(out)