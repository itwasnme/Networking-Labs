from collections import deque
import zlib
import struct

MAX_LENGTH = 1024


def bytes_to_bits(the_bytes):
    result = bytearray()
    for a_byte in the_bytes:
        for i in range(8):
            result.append(0 if (a_byte & (0x1 << i)) == 0 else 1)
    return result

def bits_to_bytes(the_bits):
    result = bytearray()
    for i in range(0, len(the_bits), 8):
        current = 0
        for j in range(8):
            current += (the_bits[i+j] << j)
        result.append(current)
    return result

class MySender:
    def __init__(self, channel):
        self.channel = channel

    def send_message(self, message_bytes):
        delimeter = bytes_to_bits(b'\x7E') #Translate delimeter to bits
        message_bits = bytes_to_bits(message_bytes) #Translate message bytes to bits
        sequence = bytearray([0,1,1,1,1,1,1]) #Modify message bits to avoid conlfict with delimiter
        i = 0 
        while i <= len(message_bits) - 7:
            if message_bits[i:i+7] == sequence:
                message_bits.insert(i + 7, 1)
                i += 7+1
            else:
                i += 1
        checksum = bytes_to_bits(struct.pack('>I' ,zlib.crc32(message_bytes))) #Produce checksum in bytes of message in bytes, turn into bits
        self.channel.send_bits(checksum+message_bits+delimeter) #Concatenate checksum bits +  message + delimeter bits and send

class MyReceiver:
    def __init__(self, got_message_function):
        self.got_message_function = got_message_function
        self.recent_bits = bytearray()

    def handle_bit_from_network(self, the_bit):
        self.recent_bits.append(the_bit) #Get bit
        if len(self.recent_bits) >= 40 and  self.recent_bits[-8:] == bytearray([0,1,1,1,1,1,1,0]): #Reach Delimeter on a long enough message
            checksum_r = bits_to_bytes(self.recent_bits[:32]) #Get transmited checksum bits and turn into bytes
            message_bits = self.recent_bits[32:-8] #Get message bits
            sequence = bytearray([0,1,1,1,1,1,1,1]) #Modify message bits to remove delimeter fix from sned_message
            i = 0
            while i <= len(message_bits) - 8:
                if message_bits[i:i + 8] == sequence:
                    del message_bits[i+7]  # Delete the 1 after the sequence
                    i = i + 7
                else:
                    i += 1  # Move to the next bit
            if(len(message_bits) % 8 != 0): #If the left message is not complete, discard
                self.recent_bits.clear()
                return
            message_with_0 = bits_to_bytes(message_bits) #Get message bits and turn into bytes
            checksum_c = struct.pack('>I', zlib.crc32(message_with_0)) #Compute checksum of received message bytes
            self.recent_bits.clear() #Clear the bits buffer
            if checksum_r == checksum_c:
                self.got_message_function(message_with_0) #Get the message without the delimeter
