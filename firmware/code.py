import board
import digitalio
import pwmio
import time
import os
import tiles

# wifi
import wifi
import socketpool
import ssl

pool = None
requests = None

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

# config from settings.toml
GEIGER_IP = os.getenv("GEIGER_IP", "")
DEMO_MODE = os.getenv("DEMO_MODE", "1") == "1"

# geiger alarms config
RAD_HIGH = 0.5 # usvh
RAD_HIHI = 2.0  # usvh
HV_LOW = 350   # volts, below this is considered hv fault
HV_HIGH = 450
RATE_THRESH = 100 # cpm jump in one reading

# connect wifi
def wifi_connect():
    global pool, requests
    ssid = os.getenv("CIRCUITPY_WIFI_SSID")
    if not ssid:
        print("no wifi configured")
        return False
    try:
        print("connecting to", ssid)
        wifi.radio.connect(ssid, os.getenv("CIRCUITPY_WIFI_PASSWORD", ""))
        print("connected, ip:", wifi.radio.ipv4_address)
        pool = socketpool.SocketPool(wifi.radio)
        # needs adafruit_requests in lib/ so we safely try to import
        import adafruit_requests
        requests = adafruit_requests.Session(pool, ssl.create_default_context())
        return True
    except Exception as e:
        print("wifi failed:", e)
        return False

# data fetching
last_geiger = {}
prev_total = -1
no_count_since = 0

def poll_geiger():
    global last_geiger
    if not requests or not GEIGER_IP:
        return None
    try:
        r = requests.get("http://" + GEIGER_IP + "/api/data", timeout=5)
        data = r.json()
        r.close()
        last_geiger = data
        return data
    except:
        return None

def check_rain():
    # open-meteo free api
    if not requests:
        return False
    try:
        # brno coordinates
        url = "https://api.open-meteo.com/v1/forecast?latitude=49.19&longitude=16.61&daily=precipitation_sum&timezone=Europe/Prague&forecast_days=1"
        r = requests.get(url, timeout=10)
        data = r.json()
        r.close()
        precip = data["daily"]["precipitation_sum"][0]
        return precip > 0.5  # more than 0.5mm = rain
    except:
        return False

# tbd wanikani check via cloudflare worker
# will be setup during build week when i can properly test
def check_wk():
    return 0, 0 # no pending reviews or lessons

# tbd anki check via ankiconnect
# will be setup during build week when i can properly test
def check_anki():
    return 0  # no due cards

# -----

tiles.setup()
disp_setup()
click()

has_wifi = wifi_connect()

if DEMO_MODE or not has_wifi:
    if not DEMO_MODE:
        print("no wifi, falling back to demo")
    DEMO_MODE = True

print("annunciator panel")
if DEMO_MODE:
    print("running in demo mode")

# state
cpm = 0
usvh = 0.0
prev_ack = True
prev_reset = True
prev_test = True
test_held = False

# demo
demo_tiles = [0, 1, 4, 8]
demo_idx = 0
demo_timer = time.monotonic()
demo_on = False
demo_tile = -1

# timer for non demo mode
poll_timer = time.monotonic()
rain_timer = time.monotonic()
rain_alarm = False
POLL_INTERVAL = 5 # seconds
RAIN_INTERVAL = 600 # check rain every 10 min

show_readings(0, 0.0)

while True:
    now = time.monotonic()

    if DEMO_MODE:
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
    else:
        # check geiger
        if now - poll_timer > POLL_INTERVAL:
            poll_timer = now
            data = poll_geiger()

            if data is None:
                # cant reach geiger
                tiles.set_condition(5, True) # COMM LOST
                tiles.set_condition(7, True) # API ERROR
            else:
                tiles.set_condition(5, False)
                tiles.set_condition(7, False)

                cpm = data.get("cpm", 0)
                usvh = data.get("usvh", 0)
                hv = data.get("hv", 0)
                total = data.get("total", 0)

                # rad alarms
                tiles.set_condition(0, usvh > RAD_HIGH) # RAD HIGH
                tiles.set_condition(1, usvh > RAD_HIHI) # RAD HI-HI
                tiles.set_condition(4, cpm > RATE_THRESH) # RATE RISE

                # hv fault
                tiles.set_condition(2, hv < HV_LOW or hv > HV_HIGH)

                # tube fail if counts havent changed in 30 seconds
                if total == prev_total:
                    if no_count_since == 0:
                        no_count_since = now
                    elif now - no_count_since > 30:
                        tiles.set_condition(3, True) # TUBE FAIL
                else:
                    no_count_since = 0
                    tiles.set_condition(3, False)
                prev_total = total

                # wifi signal
                try:
                    rssi = data.get("rssi", 0)
                    tiles.set_condition(6, rssi < -75 and rssi != 0)
                except:
                    pass

        # rain check
        if now - rain_timer > RAIN_INTERVAL:
            rain_timer = now
            rain_alarm = check_rain()
            tiles.set_condition(11, rain_alarm)  # RAIN TODAY

        # tbd wk and anki checks
        # wk_rev, wk_les = check_wk()
        # tiles.set_condition(8, wk_rev > 0)
        # tiles.set_condition(9, wk_les < 10)  # less than daily lesson target
        # anki_due = check_anki()
        # tiles.set_condition(10, anki_due > 0)
        # not very testable right now so will be built alongside the api during build week :)

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