"""Netzwerk- & Sleep-Helfer fuer den Inky Frame 7.3".

Kapselt den Standard-Pimoroni-Setup (VSYS-HOLD, RTC, WiFi-Connect,
Sleep) so, dass main.py sauber bleibt.
"""
import math
import time
import network
from machine import Pin, PWM, Timer

HOLD_VSYS_EN_PIN = 2
I2C_SDA_PIN = 4
I2C_SCL_PIN = 5
NETWORK_LED_PIN = 7
WARN_LED_PIN = 6

# VSYS-HOLD setzen, damit das Geraet am Strom nicht abschaltet.
hold_vsys_en_pin = Pin(HOLD_VSYS_EN_PIN, Pin.OUT)
hold_vsys_en_pin.value(True)

warn_led = Pin(WARN_LED_PIN, Pin.OUT)

# Network-LED (PWM) fuer pulsierendes Feedback waehrend des Verbindens.
network_led_pwm = PWM(Pin(NETWORK_LED_PIN))
network_led_pwm.freq(1000)
network_led_pwm.duty_u16(0)

_network_led_timer = Timer(-1)
_network_led_pulse_speed_hz = 1


def _network_led_brightness(brightness):
    brightness = max(0, min(100, brightness))
    value = int(pow(brightness / 100.0, 2.8) * 65535.0 + 0.5)
    network_led_pwm.duty_u16(value)


def _network_led_callback(_t):
    brightness = (time.ticks_ms() * math.pi * 2 / (1000 / _network_led_pulse_speed_hz))
    brightness = (math.sin(brightness) * 40) + 60
    _network_led_brightness(brightness)


def pulse_network_led(speed_hz=1):
    global _network_led_timer, _network_led_pulse_speed_hz
    _network_led_pulse_speed_hz = speed_hz
    _network_led_timer.deinit()
    _network_led_timer.init(period=50, mode=Timer.PERIODIC, callback=_network_led_callback)


def stop_network_led():
    global _network_led_timer
    _network_led_timer.deinit()
    network_led_pwm.duty_u16(0)


def network_connect(SSID, PSK):
    """Verbindet mit dem WLAN. Gibt True/False zurueck."""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    max_wait = 10
    pulse_network_led()
    wlan.config(pm=0xa11140)  # Power-Saving aus (manche APs brauchen das)
    wlan.connect(SSID, PSK)
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print("waiting for connection...")
        time.sleep(1)
    stop_network_led()
    if wlan.status() == 3:
        network_led_pwm.duty_u16(30000)
        return True
    warn_led.on()
    return False


def get_rtc():
    """Liefert die PCF85063A-RTC-Instanz (fuer set_time / sleep_for)."""
    from pcf85063a import PCF85063A
    from pimoroni_i2c import PimoroniI2C
    i2c = PimoroniI2C(I2C_SDA_PIN, I2C_SCL_PIN, 100000)
    return PCF85063A(i2c)


def sync_time():
    """RTC mit Pico syncen und ggf. per NTP setzen (wenn Jahr < 2023)."""
    import inky_frame
    import machine
    inky_frame.pcf_to_pico_rtc()
    year, _month, _day, _dow, _hour, _minute, _second, _ = machine.RTC().datetime()
    if year < 2023:
        inky_frame.set_time()
    print("time:", time.localtime())


def sleep_for(minutes):
    """Schlafen legen fuer `minutes` Minuten (RTC-Timer + Power-Off)."""
    rtc = get_rtc()
    rtc.clear_timer_flag()
    rtc.set_timer(minutes, ttp=rtc.TIMER_TICK_1_OVER_60HZ)
    rtc.enable_timer_interrupt(True)
    hold_vsys_en_pin.init(Pin.IN)  # erlaubt Power-Off auf Batterie
    time.sleep(60 * minutes)        # Fallback fuer USB-Betrieb
