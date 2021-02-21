import binascii
import socket
import struct
import sys
import hashlib

# Code in this function was provided by professor on how to build a checksum
def buildACKChecksum(ACK, valueOfSeq, data):
    values = (ACK, valueOfSeq, data)
    packer = struct.Struct('I I 8s')
    packed_data = packer.pack(*values)
    return bytes(hashlib.md5(packed_data).hexdigest(), encoding="UTF-8")


UDP_IP = "127.0.0.1"
UDP_PORT = 5005
unpacker = struct.Struct('I I 8s 32s')

print("UDP Target IP: ", UDP_IP)
print("UDP Target Port: ", UDP_PORT)

dataList = [b'NCC-1701', b'NCC-1422', b'NCC-1017']
currentDataItem = 0  # Indicates which item in the list is being processed currently
currentSequenceNum = 0  # Indicates what the expected sequence number is based on current iteration

# For all items in the list dataList
for x in range(0, 3):

    # Create the checksum
    chksum = buildACKChecksum(0, currentSequenceNum, dataList[currentDataItem])

    # Build the UDP Packet
    Nvalues = (0, currentSequenceNum, dataList[currentDataItem], chksum)
    UDP_Packet_Data = struct.Struct('I I 8s 32s')
    UDP_Packet = UDP_Packet_Data.pack(*Nvalues)

    # Send the UDP Packet
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # creates UDP socket

    print("Sent Packet to Server: ", UDP_Packet)
    sock.settimeout(0.009)  # sets timer to 9ms
    sock.sendto(UDP_Packet, (UDP_IP, UDP_PORT))  # sends packet to specified IP/PORT (to the server)

    while True:  # Continue to do until the correct ACK is received

        try:

            data, address = sock.recvfrom(4096)  # receives ACK from the server (at the specified IP/PORT from above)
            UDP_RPacket = unpacker.unpack(data)
            print("Received Message from Server: ({}, {}, {}, {})".format(UDP_RPacket[0], UDP_RPacket[1], UDP_RPacket[2].decode(), UDP_RPacket[3]))

            # Create the checksum for comparison
            chksumR = buildACKChecksum(UDP_RPacket[0], UDP_RPacket[1], UDP_RPacket[2])

            if UDP_RPacket[3] == chksumR and UDP_RPacket[1] == currentSequenceNum:  # Checks for correct ACK

                print("Checksums Match, Packet OK")

                sock.settimeout(None)  # Stop the timer
                break  # Leave the loop as correct ACK was received; can process next item in list

            else:

                print("Packet is corrupted")

        except socket.timeout:  # If timeout occurs, resend the same packet that was previously sent

            print("Packet Timer Expired")
            print("Sent Packet to Server: ", UDP_Packet)

            sock.settimeout(0.009) # Set timer to 9ms
            sock.sendto(UDP_Packet, (UDP_IP, UDP_PORT))  # sends packet to specified IP/PORT (to the server)

    # Variables set for next loop through the list; ready to process next item in list
    currentDataItem = currentDataItem + 1

    if currentSequenceNum == 0:  # This is used to determine what the next correct sequence number is

        currentSequenceNum = currentSequenceNum + 1

    elif currentSequenceNum == 1:

        currentSequenceNum = currentSequenceNum - 1

