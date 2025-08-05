from collections import deque
from util import trace

class DropTailBuffer:
    def __init__(self, capacity, bandwidth, label):
        self._queue = deque()
        self._capacity = capacity
        self._label = label
        self._size_in_buffer = 0

    def enqueue(self, packet):
        if len(self._queue) < self._capacity:
            trace('buffer-enqueue', f'buffering {packet} to {self._label} (buffer size {self._size_in_buffer}/{self._capacity}')
            self._queue.append(packet)
        else:
            trace('buffer-drop', f'dropping {packet} to {self._label} due to full buffer')

    def dequeue(self):
        if len(self._queue) == 0:
            return None
        else:
            packet = self._queue.popleft()
            self._size_in_buffer -= packet.size
            trace('buffer-dequeue', f'unbuffering {packet} for {self._label}')
            return packet

class PriorityQueueBuffer:
    def __init__(self, capacity, bandwidth, label):
        self._queueC1 = deque()
        self._queueC2 = deque()
        self._capacity = capacity

    def enqueue(self, packet):
        if len(self._queueC1 + self._queueC1) < self._capacity: #If we have space
            if(packet.label == "c1"):
                self._queueC1.append(packet)
            else:
                self._queueC2.append(packet)
        elif packet.label == "c1" and len(self._queueC2) > 0: #If we dont have space but the packet coming is C1 and C2 items are waiting
            self._queueC2.pop()
            self._queueC1.append(packet)
        else: #If we dont have space AND (the packet coming is C1 and there are not C2 items we can discard OR the packet coming is C2)
            return

    def dequeue(self):
        if len(self._queueC1 + self._queueC2) == 0:
            return None

        if len(self._queueC1) > 0:
            packet = self._queueC1.popleft()
            return packet
        else:
            packet = self._queueC2.popleft()
            return packet



class Bpacket:
    def __init__(self, packet, ft):
        self.packet = packet
        self.ft = ft

# Keep track of:
    # Start time of last sent packet (no matter from which flow); to compute FT for each packet
    # Finish time of last packet (current time of each flow); to compute ft for each packet
    # Finish time for each packet; max between the two above + packet size
class WeightedFairQueuingBuffer:
    def __init__(self, capacity, bandwidth, label):
        self._queueC1 = deque()
        self._queueC2 = deque()
        self._capacity = capacity
        self._time = 0
        self._C1FlowTime = 0
        self._C2FlowTime = 0
        self._C1Part = 2
        self._C2Part = 1

    def enqueue(self, packet):
        if len(self._queueC1 + self._queueC1) < self._capacity: #If we have space
            if(packet.label == "c1"):
                ft = max(self._time, self._C1FlowTime) + (packet.size/self._C1Part)
                bpack = Bpacket(packet, ft)
                self._queueC1.append(bpack)
                self._C1FlowTime = ft
            else: 
                ft = max(self._time, self._C2FlowTime) + (packet.size/self._C2Part)
                bpack = Bpacket(packet, ft)
                self._queueC2.append(bpack)
                self._C2FlowTime = ft

        else: #If we dont have space
            if(packet.label == "c1"): #And we get a packet from flow C1
                if(len(self._queueC2) == 0): #If the queue for flow C2 is empty, drop the packet
                    return
                ft = max(self._time, self._C1FlowTime) + (packet.size/self._C1Part)
                if(ft >= self._queueC2[-1].ft): #If the calculated finish time for the current packet is greater than the highest finish time for the last C2 packet, dropt the packet
                    return
                else: #If the calculted finish time for the current packet is less than the highest finish time for the last C2, dropt the last C2 packet and add C1 packet
                    self._C2FlowTime = self._C2FlowTime - (self._queueC2[-1].packet.size/self._C2Part)
                    self._queueC2.pop()
                    bpack = Bpacket(packet, ft)
                    self._queueC1.append(bpack)
                    self._C1FlowTime = ft
            else: #And we get a packet from flow C2
                if(len(self._queueC1) == 0): #If the queue for flow C1 is empty, drop the packet
                    return
                ft = max(self._time, self._C2FlowTime) + (packet.size/self._C2Part)
                if(ft >= self._queueC1[-1].ft): #If the calculated finish time for the current packet is greater than the highest finish time for the last C1 packet, dropt the packet
                    return
                else: #If the calculted finish time for the current packet is less than the highest finish time for the last C1, dropt the last C1 packet and add C2 packet
                    self._C1FlowTime = self._C1FlowTime - (self._queueC1[-1].packet.size/self._C1Part)
                    self._queueC1.pop()
                    bpack = Bpacket(packet, ft)
                    self._queueC2.append(bpack)
                    self._C2FlowTime = ft


    def dequeue(self):
        if len(self._queueC1 + self._queueC2) == 0:
            return None

        if len(self._queueC1) == 0:
            bpacket = self._queueC2.popleft()
            self._time = bpacket.ft - (bpacket.packet.size/self._C2Part)
        elif len(self._queueC2) == 0:
            bpacket = self._queueC1.popleft()
            self._time = bpacket.ft - (bpacket.packet.size/self._C1Part)
        elif (self._queueC1[0].ft < self._queueC2[0].ft):
            bpacket = self._queueC1.popleft()
            self._time = bpacket.ft - (bpacket.packet.size/self._C1Part)
        else:
            bpacket = self._queueC2.popleft()
            self._time = bpacket.ft - (bpacket.packet.size/self._C2Part)


        #self._time = bpacket.ft 
        return bpacket.packet





