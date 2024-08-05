from pynput.keyboard import Controller as KeyboardController, Key
from pynput.mouse import Controller as MouseController, Button
from PIL import ImageGrab
import itertools
import time

# Ekranın ortasına tıklama işlevi
def click_center():
    screen = ImageGrab.grab()
    screen_width, screen_height = screen.size
    mouse.position = (screen_width / 2, screen_height / 2)
    mouse.click(Button.left)

# Şifreleri oluştur ve dene
def brute_force_passwords(min_length, max_length):
    digits = '0123456789'
    
    for length in range(min_length, max_length + 1):
        for password_tuple in itertools.product(digits, repeat=length):
            password = ''.join(password_tuple)
            click_center()  # Ekranın ortasına tıkla
            time.sleep(1)   # Bir saniye bekle
            keyboard.type(password)  # Şifreyi yaz
            keyboard.press(Key.enter)   # Enter tuşuna bas
            keyboard.release(Key.enter)
            time.sleep(1)   # Bir saniye bekle
            keyboard.press(Key.enter)   # Tekrar Enter tuşuna bas
            keyboard.release(Key.enter)
            time.sleep(2)   # Şifrelerin arasında iki saniye bekle

# Nesne oluştur
keyboard = KeyboardController()
mouse = MouseController()

# Fonksiyonu çağır
brute_force_passwords(4, 8)
