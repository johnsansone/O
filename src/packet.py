
import time
from timer import Timer
TIMEOUT_INTERVAL_P = 0.5
# packet.py - Packet-related functions

# Creates a packet from a sequence number and byte data
def make(seq_num, data = b''):
    seq_bytes = seq_num.to_bytes(4, byteorder = 'little', signed = True)
    return seq_bytes + data

# Creates an empty packet
def make_empty():
    return b''

# Extracts sequence number and data from a non-empty packet
def extract(packet):
    seq_num = int.from_bytes(packet[0:4], byteorder = 'little', signed = True)
    return seq_num, packet[4:]

# packet object that allows for the linking of timers to it
class Packeto(object):
    def __init__(self, net_packet):
        self.sent_info = net_packet
        self.timer = Timer(TIMEOUT_INTERVAL_P)
        self.timer.start()
        self.status = 0
    def starttimer(self):
        self.timer.stop()
        self.timer.start()
    def endtimer(self):
        self.timer.stop()
    def acked(self):
        self.status = 1
        print('packet acked')
    def timerstate(self):
        if not self.status == 1 and not self.timer.timeout():
            return True
        else:
            return False
    def did_runout(self):
        return self.timer.timeout()
    def returnpacket(self):
        return self.sent_info
    def stat(self):
        return self.status