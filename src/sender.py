import packet
import socket
import sys
import _thread
import time
import udt
from packet import extract
from timer import Timer

PACKET_SIZE = 512
RECEIVER_ADDR = ('localhost', 8080)
SENDER_ADDR = ('localhost', 0)
SLEEP_INTERVAL = 0.05
TIMEOUT_INTERVAL = 0.5
WINDOW_SIZE = 4


base = 0
mutex = _thread.allocate_lock()
send_timer = Timer(TIMEOUT_INTERVAL)
#object for window (only size of 4 but can switch to a linked list farly easily)
class P_Window(object):
    contains = 0
    def __init__(self):
        return
    def start(self,packet1,packet2,packet3,packet4):
        self.lpacket1 = packet1
        self.lpacket2 = packet2
        self.lpacket3 = packet3
        self.lpacket4 = packet4
        #adds packets into the window
    def add_packet(self,packet):
        print('adding packet')
        if self.contains == 0 :
            self.lpacket1 = packet
            self.contains = self.contains +1
        elif self.contains == 1 :
            self.lpacket2 = packet
            self.contains = self.contains +1
        elif self.contains == 2 :
            self.lpacket3 = packet
            self.contains = self.contains +1
        elif self.contains == 3 :
            self.lpacket4 = packet
            self.contains = self.contains +1
        else:
            self.lpacket1 = self.lpacket2
            self.lpacket2 = self.lpacket3
            self.lpacket3 = self.lpacket4
            self.lpacket4 = packet
    def contain(self):
        return self.contains
    def packet1(self):
        return self.lpacket1
    def packet2(self):
        return self.lpacket2
    def packet3(self):
        return self.lpacket3
    def packet4(self):
        return self.lpacket4
    # returns the represinitive number of a packet
    def return_packet(self,num):
        ack, _ = packet.extract(self.lpacket1.returnpacket())
        if ack == num :
            return 1
        ack, _ = packet.extract(self.lpacket2.returnpacket())
        if ack == num :
            return 2
        ack, _ = packet.extract(self.lpacket3.returnpacket())
        if ack == num :
            return 3
        ack, _ = packet.extract(self.lpacket4.returnpacket())
        if ack == num :
            return 4
        else : 
            return 0
    # returns the packet object
    def return_packet_full(self,num):
        ack, _ = packet.extract(self.lpacket1.returnpacket())
        if ack == num :
            return self.lpacket1
        ack, _ = packet.extract(self.lpacket2.returnpacket())
        if ack == num :
            return self.lpacket2
        ack, _ = packet.extract(self.lpacket3.returnpacket())
        if ack == num :
            return self.lpacket3
        ack, _ = packet.extract(self.lpacket4.returnpacket())
        if ack == num :
            return self.lpacket4
    # returns packet timer status
    def timer_status(self):
        if self.contains == 1 :
            return self.lpacket1.timerstate()
        elif self.contains == 2 :
            return self.lpacket1.timerstate() and not self.lpacket2.did_runout()
        elif self.contains == 3 :
            return self.lpacket1.timerstate() and not self.lpacket2.did_runout() and not self.lpacket3.did_runout()
        else:
            pak1bool = self.lpacket1.stat() == 0 and not self.lpacket1.did_runout() and not self.lpacket2.did_runout() and not self.lpacket3.did_runout() and not self.lpacket4.did_runout()
            pak2bool = self.lpacket2.stat() == 0 and not self.lpacket1.did_runout() and not self.lpacket2.did_runout() and not self.lpacket3.did_runout() and not self.lpacket4.did_runout()
            pak3bool = self.lpacket3.stat() == 0 and not self.lpacket1.did_runout() and not self.lpacket2.did_runout() and not self.lpacket3.did_runout() and not self.lpacket4.did_runout()  
            pak4bool = self.lpacket4.stat() == 0 and not self.lpacket1.did_runout() and not self.lpacket2.did_runout() and not self.lpacket3.did_runout() and not self.lpacket4.did_runout() 
            return pak1bool or pak2bool or pak3bool or pak4bool
        
        
    
        
window = P_Window()
# Sets the window size
def set_window_size(num_packets):
    global base
    return min(WINDOW_SIZE, num_packets - base)



start_of_program = 0
# Send for SR (converted from GBN)
def send(sock, filename):
    global mutex
    global base
    global window
    global start_of_program

    # Open file
    try:
        file = open(filename, 'rb')
    except IOError:
        print('Unable to open', filename)
        return
    
    # Add all the packets to the buffer
    packets = []
    seq_num = 0
    while True:
        data = file.read(PACKET_SIZE)
        if not data:
            break
        packets.append(packet.make(seq_num, data))
        seq_num += 1

    num_packets = len(packets)
    print('There are :', num_packets)
    next_to_send = 0
    base = 0
    arr_of_pack = []

    # Start the receiver thread
    _thread.start_new_thread(receive, (sock,))

    while base < num_packets:
        mutex.acquire()
        # start sending packets
        if  window.contain() < 4 and next_to_send < num_packets:
            print('Sending packet', next_to_send)
            arr_of_pack.append(packet.Packeto(packets[next_to_send]))
            window.add_packet(packet.Packeto(packets[next_to_send]))
            udt.send(packets[next_to_send], sock, RECEIVER_ADDR)
            next_to_send = next_to_send + 1

        elif  window.packet1().stat() == 1 and next_to_send < num_packets:
            print('Sending packet', next_to_send)
            arr_of_pack.append(packet.Packeto(packets[next_to_send]))
            window.add_packet(packet.Packeto(packets[next_to_send]))
            udt.send(packets[next_to_send], sock, RECEIVER_ADDR)
            next_to_send = next_to_send + 1

        elif next_to_send == num_packets and window.packet1().stat() == 1 and window.packet2().stat() == 1 and window.packet3().stat() == 1 and window.packet4().stat() == 1:
            break

        while window.timer_status() and window.contain() > 3:
            print('Waiting')
            mutex.release()
            time.sleep(SLEEP_INTERVAL)
            mutex.acquire()

        if  window.contain() < 4:
            wid = 0

        elif  window.packet1().stat() == 0 and window.packet1().did_runout():
            # timed out
            print('Time out 1')
            ack, _ = packet.extract(window.packet1().returnpacket())
            udt.send(window.packet1().returnpacket(), sock, RECEIVER_ADDR)
            window.packet1().starttimer() 
            mutex.release()
            time.sleep(SLEEP_INTERVAL)
            mutex.acquire()
        elif  window.contain() > 1 and ( window.packet2().stat() == 0 and window.packet2().did_runout()):
            # timed out
            print('Time out 2')
            ack, _ = packet.extract(window.packet2().returnpacket())
            udt.send(window.packet2().returnpacket(), sock, RECEIVER_ADDR)
            window.packet2().starttimer()
            mutex.release()
            time.sleep(SLEEP_INTERVAL)
            mutex.acquire()
        elif  window.contain() > 2 and (window.packet3().stat() == 0 and window.packet3().did_runout()):
            # timed out
            print('Time out 3')
            ack, _ = packet.extract(window.packet3().returnpacket())
            udt.send(window.packet1().returnpacket(), sock, RECEIVER_ADDR)
            window.packet1().starttimer()
            mutex.release()
            time.sleep(SLEEP_INTERVAL)
            mutex.acquire()
        elif  window.contain() > 3 and (window.packet4().stat() == 0 and window.packet4().did_runout()):
            # timed out
            print('Time out 4')
            ack, _ = packet.extract(window.packet4().returnpacket())
            udt.send(window.packet4().returnpacket(), sock, RECEIVER_ADDR)
            window.packet4().starttimer()
            mutex.release()
            time.sleep(SLEEP_INTERVAL)
            mutex.acquire()
        #sees if it is time to leave while
        elif window.contain() > 3 and window.packet1().stat() == 1 and window.packet2().stat() == 1 and window.packet3().stat() == 1 and window.packet4().stat() == 1:
            ack, _ = packet.extract(window.packet4().returnpacket())
            if ack + 1 == num_packets:
                break
        else:
            mutex.release()
            time.sleep(SLEEP_INTERVAL)
            mutex.acquire()
        mutex.release()

    # Send empty packet as end
    udt.send(packet.make_empty(), sock, RECEIVER_ADDR)
    time.sleep(SLEEP_INTERVAL)
    udt.send(packet.make_empty(), sock, RECEIVER_ADDR)
    time.sleep(SLEEP_INTERVAL)
    udt.send(packet.make_empty(), sock, RECEIVER_ADDR)
    file.close()
    
# Receive thread for SR
def receive(sock):
    global mutex
    global base
    global window
    varable = True
    val2 = 0
    val3 = 0
    val4 = 0
    while varable == True:
        pkt, _ = udt.recv(sock)
        ack, _ = packet.extract(pkt)
        print('Got ACK :', ack)
        mutex.acquire()
        caught_up_by = 0
        packet_number = window.return_packet(ack)
        if packet_number == 1:
            window.packet1().acked()
            window.packet1().endtimer()
            if window.packet1().stat() == 0 :
                base = base + 1
                window.packet1().acked()
                window.packet1().endtimer()
            if window.contain() > 1 and window.packet2().stat() == 1:
                if val2 == 1:
                    caught_up_by = caught_up_by +1

                base = base + val2
                val2 = 0
                if window.contain() > 2 and window.packet3().stat() == 1:
                    if val3 == 1:
                        caught_up_by = caught_up_by +1


                    base = base + val3
                    val3 = 0
                    if window.contain() > 3 and window.packet4().stat() == 1:
                        if val4 == 1:
                            caught_up_by = caught_up_by +1
                        
                        base = base + val4
                        val4 = 0
            if caught_up_by > 0:
                print('caught up by: ',caught_up_by )
                caught_up_by = 0
        elif packet_number == 2 :
            print('Got ACK that is ahead by: ' , packet_number , ' Packets')
            if window.packet2().stat() == 0 :
                val2 = 1
            window.packet2().acked()
            window.packet2().endtimer()
        elif packet_number == 3  :
            print('Got ACK that is ahead by: ' , packet_number , ' Packets')
            if window.packet3().stat() == 0 :
                val3 = 1
            window.packet3().acked()
            window.packet3().endtimer()
        elif packet_number == 4:
            print('Got ACK that is ahead by: ' , packet_number , ' Packets')
            if window.packet4().stat() == 0 :
                val4 = 1
            window.packet4().acked()
            window.packet4().endtimer()
        
        mutex.release()

def gbn(sock, filename):
    global mutex
    global base
    global send_timer

    # Open the file
    try:
        file = open(filename, 'rb')
    except IOError:
        print('Unable to open', filename)
        return
    
    # Add the packets to the buffer
    packets = []
    seq_num = 0

    while True:
        data = file.read(PACKET_SIZE)
        if not data:
            break
        packets.append(packet.make(seq_num, data))
        seq_num += 1

    num_packets = len(packets)
    print('there are : ', num_packets)
    window_size = set_window_size(num_packets)
    next_to_send = 0
    base = 0

    # Start the receiver thread
    _thread.start_new_thread(receive_gbn, (sock,))

    while base < num_packets:
        mutex.acquire()
        # Send all the packets in the window
        while next_to_send < base + window_size:
            print('Sending packet', next_to_send)
            udt.send(packets[next_to_send], sock, RECEIVER_ADDR)
            next_to_send += 1

        # Starts timer
        if not send_timer.running():
            print('Starting timer')
            send_timer.start()

        # Wait until the timer runs out or we get an ACK
        while send_timer.running() and not send_timer.timeout():
            mutex.release()
            time.sleep(SLEEP_INTERVAL)
            mutex.acquire()

        if send_timer.timeout():
            send_timer.stop()
            next_to_send = base
        else:
            print('Shifting window')
            window_size = set_window_size(num_packets)
        mutex.release()

    # Send empty packet as sentinel
    udt.send(packet.make_empty(), sock, RECEIVER_ADDR)
    file.close()
    
# Receive thread
def receive_gbn(sock):
    global mutex
    global base
    global send_timer
    # waits to recive ACK's
    while True:
        pkt, _ = udt.recv(sock)
        ack, _ = packet.extract(pkt)

        print('Got ACK :', ack)
        if (ack >= base):
            mutex.acquire()
            base = ack + 1
            print('Base updated :', base)
            send_timer.stop()
            mutex.release()

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Expected GBN/SR and filename as command line arguments')
        exit()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(SENDER_ADDR)
    filename = sys.argv[2]
    if sys.argv[1] == 'GBN':
        gbn(sock, filename)
    elif sys.argv[1] == 'SR':
        send(sock, filename)
    else:
        print('Invalid input')
    
    sock.close()