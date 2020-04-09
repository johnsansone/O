# receiver.py - The receiver in the reliable data transer protocol
import packet
import socket
import sys
import udt

RECEIVER_ADDR = ('localhost', 8080)

# SR Receive packets from sender program
def receive(sock, filename):
    # Open the file for writing
    try:
        file = open(filename, 'wb')
    except IOError:
        print('Unable to open: ', filename)
        return
    i = 0
    expected_num = 0
    arr_of_pack = []
    while True:
        # Get's next packet
        pkt, addr = udt.recv(sock)
        if not pkt:
            break
        seq_num, data = packet.extract(pkt)
        print('Got packet :', seq_num)
        
        # Send back ACK dependent on if it is correct 
        if seq_num == expected_num:
            print('Got expected Packet')
            print('Sending ACK :', expected_num)
            pkt = packet.make(expected_num)
            udt.send(pkt, sock, addr)
            file.write(data)
            expected_num += 1

            if len(arr_of_pack) > expected_num:
                i = expected_num
                if arr_of_pack[expected_num] != 0:
                    while i < len(arr_of_pack) and arr_of_pack[i] != 0 :
                        print('Writing cashed line to file.')
                        file.write(arr_of_pack[i])
                        i = i+1

                    expected_num = i

        else:
            pkt2,_ = udt.recv(sock)
            print('Staching duplicate or out of order Packet :', seq_num)
            if seq_num >= len(arr_of_pack):
                missing = seq_num + 1 - len(arr_of_pack)
                i = 0
                while i <= missing :
                    arr_of_pack.append(0) 
                    i = i+1

            arr_of_pack[seq_num] = data
            print('Sending ACK of duplicate or out of order Packet :', seq_num)
            pkt2 = packet.make(seq_num)
            udt.send(pkt2, sock, addr)
    print('File finished closeing')
    file.close()

def gbn(sock, filename):
    # Open the file for writing
    try:
        file = open(filename, 'wb')
    except IOError:
        print('Unable to open', filename)
        return
    
    expected_num = 0
    while True:
        # Get the next packet from the sender
        pkt, addr = udt.recv(sock)
        if not pkt:
            break
        seq_num, data = packet.extract(pkt)
        print('Got packet :', seq_num)
        
        # Send back an ACK
        if seq_num == expected_num:
            print('Got expected packet')
            print('Sending ACK :', expected_num)
            pkt = packet.make(expected_num)
            udt.send(pkt, sock, addr)
            expected_num += 1
            file.write(data)
        else:
            print('Got packet out of order')
            print('Sending ACK :', expected_num - 1)
            pkt = packet.make(expected_num - 1)
            udt.send(pkt, sock, addr)

    file.close()

# Main function
if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Expected GBN/SR and filename as command line arguments')
        exit()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(RECEIVER_ADDR)
    filename = sys.argv[2]
    if sys.argv[1] == 'GBN':
        gbn(sock, filename)
    elif sys.argv[1] == 'SR':
        receive(sock, filename)
    else:
        print('Invalid input')
    sock.close()


