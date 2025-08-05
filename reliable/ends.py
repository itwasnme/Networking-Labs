import config
from util import Packet, Message, now, trace, create_timer, cancel_timer

class MySender:

    def __init__(self):
        self.interval = 0
        self.canSend = True
        self.PackSent = Packet() 
        self.resend_timer = 0
        self.AVG = config.INITIAL_TIMEOUT
        self.timeout = config.INITIAL_TIMEOUT

    def from_application(self, message):
        if(self.canSend == False):
            return False
        #print("Mande: " + str(message.data))
        packet = Packet()
        packet.data = message.data
        packet.is_end = message.is_end
        packet.seq_num = self.interval
        packet.timestamp = now()
        self.PackSent = packet # Make a copy of the last packet sent
        self.to_network(packet) #Send packet
        self.resend_timer = create_timer(self.timeout, lambda: self.re_send(self.PackSent))
        self.canSend = False # Stop sending until further notice
        return True
    
    def re_send(self, packet):
        packet.timestamp = now()
        self.to_network(packet)
        self.resend_timer = create_timer(self.timeout, lambda: self.re_send(packet))

    def from_network(self, packet):
        if(packet.ack_num == self.interval):
            cancel_timer(self.resend_timer)
            #print(self.timeout)
            self.AVG = (now() - packet.timestamp) * 0.2 + self.AVG * (1-0.2)
            self.timeout = self.AVG*2
            print("Recibi bien " + str(packet.ack_num) + " @" + str(packet.timestamp))
            if(self.interval == 0):
                self.interval = 1
            else:
                self.interval = 0
            self.canSend = True
            if(self.PackSent.is_end):
                return
            self.ready_for_more_from_application()  
        else:
            print("Recibi mal")

class MyReceiver:
    def __init__(self):
         self.waitingForPackN = 0
         self.timestamp = 0

    def from_network(self, packet):
        ACKpacket = Packet()
        ACKpacket.ack_num = packet.seq_num
        ACKpacket.timestamp = packet.timestamp
        self.to_network(ACKpacket)
        if(packet.seq_num == self.waitingForPackN):
            print ("Llego: " + str(packet.data))
            message = Message(data=packet.data, is_end=packet.is_end)
            self.to_application(message)
            if(self.waitingForPackN == 0):
                self.waitingForPackN = 1
            else:
                self.waitingForPackN = 0

