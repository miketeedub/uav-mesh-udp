
import signal

class Killer:

    def __init__(self):
        self.kill = False
        signal.signal(signal.SIGINT, self.exit)
        signal.signal(signal.SIGTERM, self.exit)
    def exit(self, signum, frame):
        self.kill = True