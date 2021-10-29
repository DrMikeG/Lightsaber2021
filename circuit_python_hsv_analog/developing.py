"""
Prop-Maker based Light Up Prop.
Adafruit invests time and resources providing this open source code.
Please support Adafruit and open source hardware by purchasing
products from Adafruit!
Written by Kattni Rembor for Adafruit Industries
Copyright (c) 2019 Adafruit Industries
Licensed under the MIT license.
All text above must be included in any redistribution.
"""
import time
import random
import digitalio
import audioio
import audiocore
import busio
import board
import adafruit_rgbled
import adafruit_lis3dh
import math
from analogio import AnalogIn

# CUSTOMISE COLORS HERE:
MAIN_COLOR = (255, 0, 0)  # Default is red
HIT_COLOR = (255, 255, 255)  # Default is white

# CUSTOMISE SENSITIVITY HERE: smaller numbers = more sensitive to motion
HIT_THRESHOLD = 650
SWING_THRESHOLD = 125

# Set to the length in seconds of the "on.wav" file
POWER_ON_SOUND_DURATION = 1.5

POWER_PIN = board.D10

analog_in = AnalogIn(board.A1)

enable = digitalio.DigitalInOut(POWER_PIN)
enable.direction = digitalio.Direction.OUTPUT
enable.value = False

# Pin the Red LED is connected to
RED_LED = board.D11

# Pin the Green LED is connected to
GREEN_LED = board.D12

# Pin the Blue LED is connected to
BLUE_LED = board.D13

# Create the RGB LED object
led = adafruit_rgbled.RGBLED(RED_LED, GREEN_LED, BLUE_LED)

audio = audioio.AudioOut(board.A0)  # Speaker

# Set up accelerometer on I2C bus, 4G range:
i2c = busio.I2C(board.SCL, board.SDA)
accel = adafruit_lis3dh.LIS3DH_I2C(i2c)
accel.range = adafruit_lis3dh.RANGE_4_G

COLOR_HIT = HIT_COLOR  # "hit" color is HIT_COLOR set above
COLOR_SWING = MAIN_COLOR  # "swing" color is MAIN_COLOR set above

def hsv2rgb(h, s, v):

    """HSV to RGB

    :param float h: 0.0 - 360.0
    :param float s: 0.0 - 1.0
    :param float v: 0.0 - 1.0
    :return: rgb
    :rtype: list

    """

    c = v * s
    x = c * (1 - abs(((h/60.0) % 2) - 1))
    m = v - c

    rgb = [255,0,0]

    if 0.0 <= h < 60:
        rgb = (c, x, 0)
    elif 0.0 <= h < 120:
        rgb = (x, c, 0)
    elif 0.0 <= h < 180:
        rgb = (0, c, x)
    elif 0.0 <= h < 240:
        rgb = (0, x, c)
    elif 0.0 <= h < 300:
        rgb = (x, 0, c)
    elif 0.0 <= h < 360:
        rgb = (c, 0, x)

    return list(map(lambda n: (n + m) * 255, rgb))

def lerp0To360(inputValue):
    minInput = 150
    maxInput = 65520
    percent = inputValue/(maxInput-minInput)
    retVal = 360.0 * percent
    retVal = min(retVal,360.0)
    retVal = max(retVal,0.0)
    return retVal

def play_wav(name, loop=False):
    """
    Play a WAV file in the 'sounds' directory.
    :param name: partial file name string, complete name will be built around
                 this, e.g. passing 'foo' will play file 'sounds/foo.wav'.
    :param loop: if True, sound will repeat indefinitely (until interrupted
                 by another sound).
    """
    print("playing", name)
    try:
        wave_file = open('sounds/' + name + '.wav', 'rb')
        wave = audiocore.WaveFile(wave_file)
        audio.play(wave, loop=loop)
    except:  # pylint: disable=bare-except
        return


# List of swing wav files without the .wav in the name for use with play_wav()
swing_sounds = [
    'swing1',
    'swing2',
    'swing3',
    'swing4',
    'swing5',
    'swing6',
    'swing7',
    'swing8',
]

# List of hit wav files without the .wav in the name for use with play_wav()
hit_sounds = [
    'hit1',
    'hit2',
    'hit3',
    'hit4',
    'hit5',
    'hit6',
    'hit7',
    'hit8',
]

mode = 0  # Initial mode = OFF

soundOn = True
maxLerpSeen = False
minLerpSeen = False

# Main loop
while True:

    if mode == 0:  # If currently off...

        lerp = lerp0To360( analog_in.value )
        rgblist = hsv2rgb( lerp, 1.0, 0.8)
        MAIN_COLOR = (rgblist[0], rgblist[1], rgblist[2])  # Default is red

        enable.value = True

        play_wav('on')  # Power up!
        led.color = MAIN_COLOR
        time.sleep(POWER_ON_SOUND_DURATION)
        play_wav('idle', loop=True)  # Play idle sound now
        mode = 1  # Idle mode

    elif mode >= 1:  # If not OFF mode...
        x, y, z = accel.acceleration  # Read accelerometer
        accel_total = x * x + z * z
        # (Y axis isn't needed, due to the orientation that the Prop-Maker
        # Wing is mounted.  Also, square root isn't needed, since we're
        # comparing thresholds...use squared values instead.)
        #if accel_total > HIT_THRESHOLD:  # Large acceleration = HIT
        #    play_wav(random.choice(hit_sounds))  # Start playing 'hit' sound
        #    COLOR_ACTIVE = COLOR_HIT  # Set color to fade from
        #    mode = 3  # HIT mode

        # print()
        lerp = lerp0To360( analog_in.value )

        # max lerp is 360
        # min lerp is 5
        # if we have seen both 360 and 5 - toggle sounds.
        if lerp == 360 :
            maxLerpSeen = True
        elif lerp < 5 :
            minLerpSeen = True

        if maxLerpSeen and minLerpSeen:
            if soundOn:
                soundOn = False
                play_wav('off')
#                audio.stop()
            elif not soundOn:
                soundOn = True
                play_wav('idle', loop=True)  # Play idle sound now
            
            maxLerpSeen = False
            minLerpSeen = False

            print('toggle sound '+str(soundOn))
            

        rgblist = hsv2rgb( lerp, 1.0, 0.8)
        MAIN_COLOR = (rgblist[0], rgblist[1], rgblist[2])  # Default is red

        if soundOn:
            if mode == 1 and accel_total > SWING_THRESHOLD:  # Mild = SWING
                play_wav(random.choice(swing_sounds))  # Randomly choose from available swing sounds
                led.color = MAIN_COLOR  # Set color to main color
                mode = 2  # SWING mode
            elif mode == 1:
                # Idle color
                led.color = MAIN_COLOR
            elif mode > 1:  # If in SWING or HIT mode...
                if audio.playing:  # And sound currently playing...
                    if mode == 2:  # If SWING,
                        led.color = MAIN_COLOR
                    else:
                        led.color = HIT_COLOR  # Set color to hit color
                else:  # No sound now, but still SWING or HIT modes
                    play_wav('idle', loop=True)  # Resume idle sound
                    mode = 1  # Return to idle mode
        else:
            led.color = MAIN_COLOR

