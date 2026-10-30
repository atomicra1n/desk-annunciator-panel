import board
import busio
import digitalio
import time

# shift register pins
spi = busio.SPI(clock=board.GP18, MOSI=board.GP19)
while not spi.try_lock():
    pass
spi.configure(baudrate=1000000, polarity=0, phase=0)

latch = digitalio.DigitalInOut(board.GP17)
latch.direction = digitalio.Direction.OUTPUT

oe = digitalio.DigitalInOut(board.GP16)
oe.direction = digitalio.Direction.OUTPUT
oe.value = True  # leds off for now

# buttons
btn_ack = digitalio.DigitalInOut(board.GP2)
btn_ack.direction = digitalio.Direction.INPUT
btn_ack.pull = digitalio.Pull.UP

btn_reset = digitalio.DigitalInOut(board.GP3)
btn_reset.direction = digitalio.Direction.INPUT
btn_reset.pull = digitalio.Pull.UP

btn_test = digitalio.DigitalInOut(board.GP4)
btn_test.direction = digitalio.Direction.INPUT
btn_test.pull = digitalio.Pull.UP

def shift_out(tiles):
    # tiles is a list of 12 booleans
    # we need to convert to 2 bytes for the shift registers
    # tiles 0-7 go to U1 shift register and tiles 8-11 go to U2
    # the white row (8-11) has transistors so the logic is flipped!!!!!!
    bits = 0
    for i in range(12):
        if tiles[i]:
            if i >= 8:
                # white row is inverted, ON means bit is 0
                pass
            else:
                bits = bits | (1 << i)
        else:
            if i >= 8:
                # white row OFF means bit is 1
                bits = bits | (1 << i)

    lo = bits & 0xFF         # U1
    hi = (bits >> 8) & 0xFF  # U2
    latch.value = False
    spi.write(bytes([hi, lo]))
    latch.value = True

# begin test
oe.value = False
print("annunciator test")

# all tiles on
all_on = [True] * 12
all_off = [False] * 12
shift_out(all_on)
time.sleep(1)
shift_out(all_off)
time.sleep(0.5)

# test by lighting each tile individually
print("lamp test")
for i in range(12):
    t = [False] * 12
    t[i] = True
    shift_out(t)
    time.sleep(0.15)

shift_out(all_off)
time.sleep(0.3)

# flash all tiles twice
for _ in range(2):
    shift_out(all_on)
    time.sleep(0.2)
    shift_out(all_off)
    time.sleep(0.2)

print("led test PASS")
print("ACK = toggle red row, RESET = clear, TEST = all on")

tiles = [False] * 12
prev_ack = True
prev_reset = True
prev_test = True

while True:
    a = btn_ack.value    # False when pressed
    r = btn_reset.value
    t = btn_test.value

    # toggle red row on ACK press
    if not a and prev_ack:
        print("ACK")
        for i in range(4):
            tiles[i] = not tiles[i]
        shift_out(tiles)

    # clear on RESET
    if not r and prev_reset:
        print("RESET")
        tiles = [False] * 12
        shift_out(tiles)

    # test button lights everything while held
    if not t and prev_test:
        print("TEST")
        shift_out(all_on)
    if t and not prev_test:
        # released
        shift_out(tiles)

    prev_ack = a
    prev_reset = r
    prev_test = t

    time.sleep(0.02)