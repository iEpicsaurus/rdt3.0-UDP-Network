import binascii
import socket
import struct
import sys
import hashlib
import random
import time

# THIS SECTION SIMULATES CORRUPTION, LOSS, AND DELAYS IN THE NETWORK.
# Base code in functions were provided by the professor and modified to fit needs of the program.
def Network_Delay():
    if False and random.choice([0,1,0]) == 1: # Set to False to disable Network Delay. Default is 33% packets are delayed
        time.sleep(.01)
        print("Packet Delayed")
    else:
        print("Packet Sent")


def Network_Loss():
    if False and random.choice([0,1,1,0]) == 1:  # Set to False to disable Network Loss. Default is 50% packets are lost
        print("Packet Lost")
        return(1)
    else:
        return(0)


def Packet_Checksum_Corrupter(packetdata):
    if False and random.choice([0,1,0,1]) == 1: # Set to False to disable Packet Corruption. Default is 50% packets are corrupt
        return(b'Corrupt!')
    else:
        return(packetdata)


def buildACKChecksum(ACK, valueOfSeq, data):
    values = (ACK, valueOfSeq, data)
    packer = struct.Struct('I I 8s')
    packed_data = packer.pack(*values)
    return bytes(hashlib.md5(packed_data).hexdigest(), encoding="UTF-8")


UDP_IP = "127.0.0.1"
UDP_PORT = 5005
unpacker = struct.Struct('I I 8s 32s')

currentACKNum = 0  # Used to indicate which sequence number is expected (i.e. which is correct)
wrongACK = 1  # Used when there is corruption, wrong sequence number is put in the ACK

# Create the socket and listen
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # create a UDP socket
sock.bind((UDP_IP, UDP_PORT))

while True:  # This will keep the server open (even when clients are done sending messages)

    # Receive Data
    data, addr = sock.recvfrom(1024)  # buffer size is 1024 bytes

    # The next 4 lines of code deals with a loss - ignores previously obtained packet (to simulate loss)
    # and receives the same packet that was lost
    lossTest = Network_Loss()
    if lossTest == 1:

        data, addr = sock.recvfrom(1024)

    UDP_Packet = unpacker.unpack(data)
    print("Received Message from Client: ", UDP_Packet)

    # The next 9 lines of code deals with corruption - if there is no corruption, proceed as normal
    corruptedTest = Packet_Checksum_Corrupter(UDP_Packet)
    if corruptedTest == b'Corrupt!':

        print("Corrupting Packet")  # Only enters this section if packet is to be corrupted
        chksum = 1  # Sets the packet's checksum to be obviously not the same, resulting in corruption

    else:

        # Create the checksum for comparison
        chksum = buildACKChecksum(UDP_Packet[0], UDP_Packet[1], UDP_Packet[2])

    # Compare checksums to test for corrupt data
    if UDP_Packet[3] == chksum:

        print("Checksums Match, Packet OK")

        if UDP_Packet[1] == currentACKNum:  # Checks to make sure packet has correct sequence number

            # Create the Checksum
            chksumACK = buildACKChecksum(1, currentACKNum, b"")

            # Build the UDP Packet
            GValues = (1, currentACKNum, b"", chksumACK)
            GUDP_Packet_Data = struct.Struct('I I 8s 32s')
            GUDP_Packet = GUDP_Packet_Data.pack(*GValues)

            Network_Delay()  # Poss;ibly causes a network delay
            print("Sent Packet to Client: ", GUDP_Packet)
            sock.sendto(GUDP_Packet, addr)  # sends packet to specified IP/PORT (to the server)

            # The next 7 lines deal with changing what the expected sequence numbers based on the current iteration
            if currentACKNum == 0:
                currentACKNum = 1
                wrongACK = 0

            elif currentACKNum == 1:
                currentACKNum = 0
                wrongACK = 1

    else:

        print("Checksums Don't Match, Packet Corrupt")

        # Create the checksum
        chksumACK1 = buildACKChecksum(1, wrongACK, b"")

        # Build the UDP Packet with wrong sequence number
        ErrValues = (1, wrongACK, b"", chksumACK1)
        ErrUDP_Packet_Data = struct.Struct('I I 8s 32s')
        ErrUDP_Packet = ErrUDP_Packet_Data.pack(*ErrValues)

        print("Sent Packet to Client: ", ErrUDP_Packet)
        sock.sendto(ErrUDP_Packet, addr)  # sends packet to specified IP/PORT (to the server)

