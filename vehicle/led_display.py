import time
import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306 as fruit
import RPi.GPIO as GPIO
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import _thread


class User2VehicleInterface:

    def __init__(self, I2C, batIP, ethernetIP, wifiIP):

        self.kill = False
        self.fontPath = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
        self.disp = fruit.SSD1306_128_32(rst=24, i2c_address=I2C)
        self.width = self.disp.width
        self.height = self.disp.height
        self.image = Image.new('1', (self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)
        self.font = ImageFont.truetype(self.fontPath, 20)
        self.batIP, self.ethernetIP, self.wifiIP = batIP, ethernetIP, wifiIP
        self.disp.begin()
        self.disp.clear()
        self.disp.display()
        self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)
        self.loadFlag = False
        self.dummyFC = False
        self.messages = {"connecting2FC": [["Initializing", (12, 0, 0, 0)], ["flight controller.", (12, 1, 0, 0)]],
                         "connected!": [["Connected!", (20, 0, 0, 0)]],
                         "dummy": [["Using Dummy", (12, 0, 0, 0)], ["flight controller.", (12, 1, 0, 0)]],
                         "status": [["IP: " + self.ethernetIP, (10, 0, 0, 0)]]
                         }

        self.displayMode = ""
        _thread.start_new_thread(self.main, ())

    def LCDMessage(self, message):
        self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)
        for m in self.messages[message]:
            self.drawText(m[0], m[1])
        self.displayText()
        if self.loadFlag:
            self.loading(message)

    def drawText(self, text, dims):
        size, line, offset, yoff = dims
        font = ImageFont.truetype(self.fontPath, size)
        self.draw.text((offset, line * size + yoff), text, font=font, fill=1)

    def displayText(self):
        self.disp.image(self.image)
        self.disp.display()
        time.sleep(1)

    def loading(self, prevText):
        offset = 0
        sign = 1
        while self.loadFlag and not self.kill:
            self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)
            for m in self.messages[prevText]:
                self.drawText(m[0], m[1])
            self.drawText("...", (12, 2, offset, -2))
            self.displayText()
            time.sleep(.1)
            offset += 8 * sign
            if offset >= 106:
                sign = -1
            elif offset <= 0:
                sign = 1

    def main(self):

        while not self.kill:
            if self.displayMode == "connecting2FC":
                self.LCDMessage("connecting2FC")
                self.LCDMessage("connected!")
                time.sleep(2)
            elif self.displayMode == "dummy":
                self.LCDMessage("dummy")
            elif self.displayMode == "status":
                self.LCDMessage("status")


if __name__ == '__main__':

    ui = User2VehicleInterface(0x3C, "123.123.123.123", "123.123.123.123", "123.123.123.123")
    ui.loadFlag = True
    ui.displayMode = "connecting2FC"

    while True:

        try:
            time.sleep(5)
            ui.loadFlag = False
            ui.displayMode = "status"

        except:
            break

    pass
