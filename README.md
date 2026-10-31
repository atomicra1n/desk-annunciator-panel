# Desk Annunciator Panel

A smaller version of alarm panels found in Main Control Rooms of Nuclear Power Plants. Has 12 backlit alarm tiles, a seven segment display (8 digits) and ACK, RESET and TEST buttons. It is controlled by a Raspberry Pi Pico WH and shows live radiation readings from my [Wi-Fi Geiger Counter](https://github.com/atomicra1n/wifi-geiger-counter) which I made in Week 1 of Half Life. The alarm tiles light up when a problem occurs to notify me and play a sound.

<img width="1637" height="1415" alt="image" src="https://github.com/user-attachments/assets/6eda8c45-0fc9-4cf8-bb7a-227443a26130" />
<img width="2465" height="1705" alt="image" src="https://github.com/user-attachments/assets/238c71fd-28f2-491d-be54-8f4e40314bde" />
<img width="1784" height="1783" alt="image" src="https://github.com/user-attachments/assets/e40e2252-5631-4cbe-a875-753647a55f28" />
<img width="1632" height="1648" alt="image" src="https://github.com/user-attachments/assets/be9919ca-e05f-4cfb-962e-dae2a365601b" />
<img width="1439" height="1395" alt="image" src="https://github.com/user-attachments/assets/793507fa-926f-4a52-82a6-8f3d32d27292" />

## Features

- 12 alarm tiles with LEDs of three colors, red for critical alerts, yellow for warnings and white for reminders and general info.
- Proper annunciator sequence, new alarm flashes fast and creates sound, ACK makes the flashing steady and when condition is cleared it flashes slowly until RESET is pressed after which it stops being lit.
- TEST button lights up all tiles
- Seven segment display with 8 digits showing CPM and radiation levels in microSieverts/h from my Geiger project
- Demo mode for simulating alarms
- Fully through-hole with no SMD soldering and no screws needed for the enclosure

## Motivation

I've always loved nuclear energy and worked on many projects related to it. Annunciators are a particularly cool part of each NPP MCR and I thought having one at home would be really cool. Perhaps I can add a SCRAM button one day!

## Functionality

- The RPi Pico WH connects to Wi-Fi and checks the Geiger Counter's /api/data endpoint every 5 seconds to get the CPM, uSv/h, voltage status, counts and Wi-Fi signal
- Two shift registers drive the 12 tile LEDs. They run at 3.3V, and turn on yellow and red LEDs with a LOW output.
- White LEDs need 2.9V which is too close to 3.3V to work well, so they run from 5V via 2N3904 transistors. This means their logic is flipped.
- The MAX7219 display module needs 3.5V for a HIGH logic, yet our RPi only outputs 3.3V, so I made level shifters from three 2N3904 transistors. The signal is inverted, so the firmware must also send it inverted.
- The speaker is driven by another 2N3904 with a 47 ohm resistor and a flyback diode.
- Buttons go straight to the RPi Pico.

### Tiles

Red tiles: RAD HIGH, RAD HI-HI, HV FAULT, TUBE FAIL
Yellow tiles: RATE RISE, COMM LOST, WIFI WEAK, API ERROR
White tiles: WK REVIEWS, WK LESSONS, ANKI DUE, RAIN TODAY

I study Japanese and use many services to learn Kanji, vocabulary and grammar every day. As such, for the white tiles, I added tiles to notify me when I need to do some work on these services (WaniKani and Anki). However, as it would be a bit trickier to test, I only laid the foundation in the firmware for now and will add a proper API via a CF worker during build week.

## How it was made

I made the PCB itself in KiCad and used Fusion for the enclosure, a couple issues that arised:

- I originally wanted the 74HCT595 shift register so it could run at 5V and still take 3.3 volt logic, but GM Electronic (my local supplier) only had the SMD version, so instead I used the HC version at 3.3V. This meant I'd need to put the white LEDs on 5V.
- I initially put the white LEDs on 5 volts directly but realized the shift register outputs could end up above their 3.3V supply which the datasheet discourages, so I added transistors for the white LED row.
- Different shops listed the MAX display module anywhere between 80 and 85 milimeters long and nobody published the exact header hole locations, so I made a 3D printed support post that can be adjusted and printed again.
- The PCB is quite small for all it contains, so most of the logic goes on the back and the LEDs and speaker and seven segment went on the front.
- KiCad, just like always, assigned wrong footprints, so I needed to manually reassign
- My speaker needed a custom footprint as KiCad didn't have it built in.
- I accidentally inverted the LED logic when making the firmware, noticed it only as I was writing the journal entry!

## Tech stack

- KiCad for all PCB work
- Autodesk Fusion for the enclosure
- CircuitPython + Adafruit_requests library for the firmware

## Repo layout

- pcb/ has the KiCad project
- pcb/gerbers has all gerber and drill files + a zip for them
- cad has the .f3d file for Fusion and a .step file
- stl has the exported printable parts
- firmware/ contains the CircuitPython firmware and firmware/lib/ has the needed libraries (adafruit requests)
- images/ contains renders, screenshots and the printable label sheet

## Bill of materials

| Part | Qty | Source | Unit | Total |
|---|---|---|---|---|
| [PCB Manufacturing](https://jlcpcb.com) | 1 | JLCPCB | $4.00 | $4.00 |
| [CONNFLY BL120G-V8.5 female header 1x20pin](https://www.gme.cz/v/1498892/connfly-bl120g-v85-dutinkova-lista-1x20pin-roztec-254mm-vyska-85mm) | 3 | GM Electronic | $0.45 | $1.35 |
| [LED display seven segment MAX7219](https://www.gme.cz/v/1508913/led-displej-8x7-segmentu-cerveny) | 1 | GM Electronic | $3.57 | $3.57 |
| [Texas Instruments SN74HC595N](https://www.gme.cz/v/1490931/texas-instruments-sn74hc595n-cmos-8bit-posuvny-registr-se-seriovym-vstupem-s-vystupnym-registrem) | 2 | GM Electronic | $1.71 | $3.42 |
| [KLS DIL16PZ socket](https://www.gme.cz/v/1499942/kls-dil16pz-patice) | 2 | GM Electronic | $0.57 | $1.14 |
| [Lucky Light red LED 5 mm](https://www.gme.cz/v/1495977/lucky-light-503vd2e-v1-4i-led-5mm-cervena) | 4 | GM Electronic | $0.14 | $0.56 |
| [Lucky Light yellow LED 5 mm](https://www.gme.cz/v/1496003/lucky-light-503uyd2e-y2-4g-led-5mm-zluta) | 4 | GM Electronic | $0.17 | $0.68 |
| [OptoSupply white LED 5 mm](https://www.gme.cz/v/1491945/optosupply-osw5dk6ee2a-led-5mm-studena-bila) | 4 | GM Electronic | $0.36 | $1.44 |
| [Resistor 270 ohm 0207](https://www.gme.cz/v/1488130/gym-cym-rm-270r-06w-1-0207-metalizovany-rezistor) | 10 | GM Electronic | $0.10 | $1.00 |
| [Resistor 330 ohm 0207](https://www.gme.cz/v/1494116/gym-cym-rm-330r-06w-1-0207-metalizovany-rezistor) | 10 | GM Electronic | $0.10 | $1.00 |
| [Resistor 47 ohm 0207](https://www.gme.cz/v/1493086/gym-cym-rm-47r-06w-1-0207-metalizovany-rezistor) | 10 | GM Electronic | $0.10 | $1.00 |
| [Resistor 1 kiloohm 0207](https://www.gme.cz/v/1486228/gym-cym-rm-1k-06w-1-0207-metalizovany-rezistor) | 10 | GM Electronic | $0.10 | $1.00 |
| [Resistor 10 kiloohm 0207](https://www.gme.cz/v/1494150/gym-cym-rm-10k-06w-1-0207-metalizovany-rezistor) | 10 | GM Electronic | $0.10 | $1.00 |
| [SEMTECH 2N3904 transistor](https://www.gme.cz/v/1487027/semtech-2n3904-bipolarni-tranzistor) | 18 | GM Electronic | $0.06 | $1.08 |
| [SEMTECH 1N4148 diode](https://www.gme.cz/v/1487018/semtech-1n4148-dioda) | 19 | GM Electronic | $0.04 | $0.76 |
| [HITANO CK 100n/50V](https://www.gme.cz/v/1489676/hitano-ck-100n-50v-x7r-rm508-10-keramicky-kondenzator) | 3 | GM Electronic | $0.25 | $0.75 |
| [HITANO CE 47u/16V](https://www.gme.cz/v/1489745/hitano-ce-47u-16vt-hit-emr-5x7-rm2-bulk-elektrolyticky-kondenzator) | 16 | GM Electronic | $0.05 | $0.80 |
| [Kingstate KSSG3108 speaker](https://www.gme.cz/v/1498669/kingstate-kssg3108-magnetodynamicky-menic) | 1 | GM Electronic | $2.36 | $2.36 |
| [Diptronic DTS62K switch](https://www.gme.cz/v/1501370/diptronic-dts62k-mikrospinac) | 3 | GM Electronic | $0.25 | $0.75 |
| **Parts subtotal** | | | | **$27.66** |
| Shipping (estimate) | | | | $10.00 |
| **Total** | | | | **$37.66** |

The RPi Pico WH isn't included as I already own it. The order quantities are higher than the PCB technically needs as GM Electronic has minimum order quantities. 3D Printed parts will be printed by me at school. The total exceeds tier 1 funding, so I will cover the rest myself.

## Assembly

1. Order the PCB from JLCPCB using the exported gerber files and order the parts from your preferred electronics retailer.
2. Solder the back parts first (DIP sockets, resistors, transistors, capacitors, diode)
3. Solder the RPi Pico sockets on the back, make sure the USB points to the right board edge.
4. Solder the front LEDs, display pins, speaker and buttons.
5. Put the 74HC595 shift registers into their sockets and plug in the pico.
6. Flash CircuitPython to the pico.
7. Solder the straight header on the display module making sure the pins point out the back. The support post's pin should be in the module's corner hole. Plug the module into the pins.
8. Print the bezel face down, the back cover plate down and diffusers in white PLA.
9. Print the label sheet at 100% scale. Cut the labels out and secure them in the bezel cells.
10. Put the 3 button plungers into button holes from the inside.
11. Slide the PCB into the bezel until it is on the ledges, resting. Push the back cover in until a click is heard.

## Firmware

1. Download CircuitPython for the RPi Pico WH
2. Hold BOOTSEL on the Pico, plug it in and drag the downloaded .uf2 onto it.
3. When you see the CIRCUITPY drive, copy over code.py, tiles.py and the lib folder.
4. Rename settings.toml.example to settings.toml and fill it in, making sure you also put it on the CIRCUITPY drive.

## Controls

- ACK acknowledges flashing alarms and silences the alarm.
- RESET clears the alarms who's conditions have cleared.
- TEST lights up all tiles.

## AI disclosure

LLMs (Claude Opus 5.5) was used to get feedback on the PCB schematic and routing, review parts of the work and help find and fix bugs. It was also used for other tedious but simple tasks, such as adding the BOM to this README. AI was not used in writing the README, Journal or other parts of the project.

---

Built for [Hack Club Half Life](https://halflife.hackclub.com/) Week 4 (Displays).
