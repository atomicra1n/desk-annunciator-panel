import board
import digitalio
import pwmio
import time
import tiles

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

# max7219 display
# these go through level shifters so everything is INVERTED!!!
# pico HIGH = max7219 LOW
disp_din = digitalio.DigitalInOut(board.GP11)
disp_din.direction = digitalio.Direction.OUTPUT
disp_clk = digitalio.DigitalInOut(board.GP10)
disp_clk.direction = digitalio.Direction.OUTPUT
disp_cs = digitalio.DigitalInOut(board.GP13)
disp_cs.direction = digitalio.Direction.OUTPUT
disp_cs.value = False  

def disp_send(addr, data):
    disp_cs.value = True
    # send 16 bits with most significant bit first, all bits inverted
    for val in [addr, data]:
        for bit in range(7, -1, -1):
            if (val >> bit) & 1:
                disp_din.value = False # inverted meaning pico low, max sees high
            else:
                disp_din.value = True
            disp_clk.value = True
            disp_clk.value = False
    disp_cs.value = False

def disp_setup():
    disp_send(0x0C, 0x01)  # not shutdown
    disp_send(0x09, 0xFF)  # decode
    disp_send(0x0B, 0x07)  # scan all 8
    disp_send(0x0A, 0x07)  # brightness
    disp_send(0x0F, 0x00)  # test off
    for d in range(1, 9):
        disp_send(d, 0x0F)

def disp_number(start_digit, text):
    # show a string of digits
    pos = start_digit
    for ch in text:
        if ch == '.':
            # add dot to previous digit
            if pos > start_digit:
                # resend previous digit with dot 
                prev = text[text.index('.') - 1]
                if prev.isdigit():
                    disp_send(pos - 1, int(prev) | 0x80)
        elif ch == ' ':
            disp_send(pos, 0x0F)
            pos = pos + 1
        elif ch.isdigit():
            disp_send(pos, int(ch))
            pos = pos + 1

def show_readings(cpm, usvh):
    # cpm on digits 1-4, usvh on 5-8
    cpm_str = str(int(cpm)).rjust(4)
    disp_number(1, cpm_str)

    if usvh < 10:
        usv_str = "{:.2f}".format(usvh)
    elif usvh < 100:
        usv_str = "{:.1f}".format(usvh)
    else:
        usv_str = str(int(usvh)).rjust(4)
    disp_number(5, usv_str)

# sounds are just simple beeps for now
def beep(freq, ms):
    p = pwmio.PWMOut(board.GP15, frequency=freq, duty_cycle=32768)
    time.sleep(ms / 1000)
    p.deinit()

def horn():
    beep(800, 100)
    beep(1200, 100)

def click():
    beep(2500, 5)

# --------------------------------------
# BEGIN MAIN LOOP
# ---------------------------------------

tiles.setup()
disp_setup()
click()

print("annunciator panel")

# demo
demo_tiles = [0, 1, 4, 8]
demo_idx = 0
demo_timer = time.monotonic()
demo_on = False
demo_tile = -1

cpm = 22
usvh = 0.14

prev_ack = True
prev_reset = True
prev_test = True
test_held = False

print("demo mode, use buttons to interact")

while True:
    now = time.monotonic()

    if now - demo_timer > 3.5:
        demo_timer = now
        if demo_on:
            tiles.set_condition(demo_tile, False)
            demo_on = False
            cpm = 22
            usvh = 0.14
        else:
            demo_tile = demo_tiles[demo_idx]
            tiles.set_condition(demo_tile, True)
            demo_idx = (demo_idx + 1) % len(demo_tiles)
            demo_on = True
            if demo_tile < 4:
                cpm = 380
                usvh = cpm * 0.0066
            #print("triggered tile", demo_tile)

    # buttons
    a = btn_ack.value
    r = btn_reset.value
    t = btn_test.value

    if not a and prev_ack:
        tiles.ack()
        beep(1800, 40)

    if not r and prev_reset:
        tiles.reset()
        click()

    if not t and prev_test:
        test_held = True
    if t and not prev_test:
        test_held = False

    prev_ack = a
    prev_reset = r
    prev_test = t

    # test overrides everything
    if test_held:
        tiles.shift_out([True] * 12)
    else:
        tiles.update()
        show_readings(cpm, usvh)

    # horn when something is flashing
    if tiles.any_flashing() and not test_held:
        horn()

    time.sleep(0.05)