import argparse
import sys
import struct
import random
import socket

def encode_domain_name(domain_name):
    # Encode the domain name in DNS format (labels with length prefix)
    labels = domain_name.split('.')
    encoded_name = b''
    for label in labels:
        encoded_name += struct.pack('B', len(label))  # Length of label
        encoded_name += label.encode('ascii')  # The label itself
    encoded_name += b'\0'  # Null byte to indicate the end of the domain name
    return encoded_name

def create_request(hostname, ipv6=False):
    # DNS Header Fields
    transaction_id = random.randint(0, 65535)  # Random transaction ID
    flags = 0x0000  # Recursion Disabled (QR=0, OpCode=0, RD=0)
    questions = 1  # We are asking for one record
    answer_rrs = 0  # No answer section
    authority_rrs = 0  # No authority section
    additional_rrs = 0  # No additional section

    # DNS Question Section
    domain_name = encode_domain_name(hostname)
    if(ipv6):
        query_type = 28
    else:
        query_type = 1  # A record for IPv4 addresses

    query_class = 1  # IN class (Internet)

    # DNS Header + Question
    query = struct.pack('>HHHHHH', transaction_id, flags, questions, answer_rrs, authority_rrs, additional_rrs)
    query += domain_name
    query += struct.pack('>HH', query_type, query_class)

    # Calculate the size of the query
    query_size = len(query)

    # Prefix the query with the size (2-byte big-endian number)
    size_prefix = struct.pack('>H', query_size)

    # Output the result to sys.stdout.buffer
    sys.stdout.buffer.write(size_prefix)
    sys.stdout.buffer.write(query)
    
    return size_prefix + query

def bytes_to_bits(byte_data):
    return ''.join(f'{byte:08b}' for byte in byte_data)

def process_response(response):
    print("\n[HEADER]")
    size = int.from_bytes(response[:2], byteorder='big')
    ID = response[2:4].hex()
    flags = bytes_to_bits(response[4:6])
    Rcode = flags[-4:]
    if(str(Rcode) != '0000'):
        print("RCODE: ERROR[" + str(Rcode) + "]")
    QDcount = int.from_bytes(response[6:8], byteorder='big')
    ANcount = int.from_bytes(response[8:10], byteorder='big')
    NScount = int.from_bytes(response[10:12], byteorder='big')
    ARcount = int.from_bytes(response[12:14], byteorder='big')
    print("Message Size: " + str(size) + " bytes")
    print("Identifier: " + ID)
    print("Flag bits: " + str(flags))
    print("Questions: " + str(QDcount))
    print("Answer Resource Records: " + str(ANcount))
    print("Authorative Server Resource Records (NS) "+ str(NScount))
    print("Additional Resource Records: " + str(ARcount))
    body = response[14:]
    
    i = 0
    labels_array = []
    print("\n[QUESTIONS]")       
    for _ in range(QDcount):
        while (True):
            # Get size and push to labes to array
            label = ''
            size = int.from_bytes(body[i:i+1], byteorder='big')
            i = i + 1
            if size == 0:
                # Get type and class
                Type = int.from_bytes(body[i:i+2], byteorder='big')
                i = i + 2
                Class = int.from_bytes(body[i:i+2], byteorder='big')
                i = i + 2
                Name = ''
                for z in range (len(labels_array)):
                    Name = Name + labels_array[z] + '.'
                Name = Name[:-1]
                print("Name: " + Name)
                print("Name Length: " + str(len(Name)))
                print("Label Count: " + str(len(labels_array)))
                print("Type: " + str(Type))
                print("Class: " + str(Class) + '\n')
                labels_array = []
                break
            for y in range (size):
                label = label + body[i:i+1].decode('ascii')
                i = i + 1
            labels_array.append(label)

    print("\n[ANSWERS]")
    for _ in range(ANcount):
        while (True):
            # Get size and push to labes to array
            label = ''
            size = int.from_bytes(body[i:i+1], byteorder='big')
            i = i + 1
            if size == 0:
                # Get type and class
                Type = int.from_bytes(body[i:i+2], byteorder='big')
                i = i + 2
                Class = int.from_bytes(body[i:i+2], byteorder='big')
                i = i + 2
                TTL = int.from_bytes(body[i:i+4], byteorder='big')
                i = i + 4
                DLength = int.from_bytes(body[i:i+2], byteorder='big')
                i = i + 2
                Name = ''
                for z in range (len(labels_array)):
                    Name = Name + labels_array[z] + '.'
                Name = Name[:-1]
                print("Name: " + Name)
                print("Name Length: " + str(len(Name)))
                print("Label Count: " + str(len(labels_array)))
                print("Type: " + str(Type))
                print("Class: " + str(Class))
                print("Time to Live: " + str(TTL))
                print("Data Length: " + str(DLength))
                labels_array = []
                if(Type == 1 or Type == 28):
                    IPv = ''
                    for x in range (DLength):
                        if(Type == 1):
                            IPv = IPv + str(int.from_bytes(body[i:i+1], byteorder='big')) + '.'
                            i = i + 1
                        else:
                            IPv = IPv + body[i:i+2].hex() + ':'
                            i = i + 2
                            if(x == 7):
                                break
                    IPv = IPv[:-1]
                    print("Address: " + IPv + "\n")
                if(Type == 5):
                    while(True):
                        size = int.from_bytes(body[i:i+1], byteorder='big')
                        i = i + 1
                        if(size == 0):
                            cname = ''
                            for z in range (len(labels_array)):
                                cname = cname + labels_array[z] + '.'
                            cname = cname[:-1]
                            print("CNAME: " + cname + '\n')
                            labels_array = []
                            break
                        for y in range (size):
                            label = label + body[i:i+1].decode('ascii')
                            i = i + 1
                        labels_array.append(label)
                        label = ''
                break
            for y in range (size):
                label = label + body[i:i+1].decode('ascii')
                i = i + 1
            labels_array.append(label)



    print("\n[AUTHORITATIVE NAMESERVERS]")
    for _ in range(NScount):
        while (True):
            # Get size and push to labes to array
            label = ''
            size = int.from_bytes(body[i:i+1], byteorder='big')
            i = i + 1
            if size == 0:
                # Get type and class
                Type = int.from_bytes(body[i:i+2], byteorder='big')
                i = i + 2
                Class = int.from_bytes(body[i:i+2], byteorder='big')
                i = i + 2
                TTL = int.from_bytes(body[i:i+4], byteorder='big')
                i = i + 4
                DLength = int.from_bytes(body[i:i+2], byteorder='big')
                i = i + 2
                Name = ''
                for z in range (len(labels_array)):
                    Name = Name + labels_array[z] + '.'
                Name = Name[:-1]
                print("Name: " + Name)
                print("Name Length: " + str(len(Name)))
                print("Label Count: " + str(len(labels_array)))
                print("Type: " + str(Type))
                print("Class: " + str(Class))
                print("Time to Live: " + str(TTL))
                print("Data Length: " + str(DLength))
                labels_array = []
                if(Type == 2):
                    while(True):
                        size = int.from_bytes(body[i:i+1], byteorder='big')
                        i = i + 1
                        if(size == 0):
                            NS = ''
                            for z in range (len(labels_array)):
                                NS = NS + labels_array[z] + '.'
                            NS = NS[:-1]
                            print("Name Server: " + NS + '\n')
                            labels_array = []
                            break
                        for y in range (size):
                            label = label + body[i:i+1].decode('ascii')
                            i = i + 1
                        labels_array.append(label)
                        label = ''
                if(Type == 6):
                    count = 0 
                    while(True):
                        size = int.from_bytes(body[i:i+1], byteorder='big')
                        i = i + 1
                        if(size == 0):
                            NS = ''
                            for z in range (len(labels_array)):
                                NS = NS + labels_array[z] + '.'
                            NS = NS[:-1]
                            labels_array = []
                            if(count == 0):
                                count = count + 1
                                print("Primary Name Server: " + NS)
                            else:
                                print("Responsible Authority's Mailbox: " + NS)
                                print("Serial Number: " + str(int.from_bytes(body[i:i+4], byteorder='big')))
                                i = i + 4
                                print("Refresh Interval: " + str(int.from_bytes(body[i:i+4], byteorder='big')))
                                i = i + 4
                                print("Retry Interval: " + str(int.from_bytes(body[i:i+4], byteorder='big')))
                                i = i + 4
                                print("Expire Limit: " + str(int.from_bytes(body[i:i+4], byteorder='big')))
                                i = i + 4
                                print("Maximum TTL: " + str(int.from_bytes(body[i:i+4], byteorder='big')))
                                i = i + 4
                                break
                        for y in range (size):
                            label = label + body[i:i+1].decode('ascii')
                            i = i + 1
                        if(label != ''):
                            labels_array.append(label)
                        label = ''
                break
            for y in range (size):
                label = label + body[i:i+1].decode('ascii')
                i = i + 1
            labels_array.append(label)



    print("\n[ADDITIONAL RECORDS]")
    for _ in range(ARcount):
        while (True):
            # Get size and push to labes to array
            label = ''
            size = int.from_bytes(body[i:i+1], byteorder='big')
            i = i + 1
            if size == 0:
                # Get type and class
                Type = int.from_bytes(body[i:i+2], byteorder='big')
                i = i + 2
                Class = int.from_bytes(body[i:i+2], byteorder='big')
                i = i + 2
                TTL = int.from_bytes(body[i:i+4], byteorder='big')
                i = i + 4
                DLength = int.from_bytes(body[i:i+2], byteorder='big')
                i = i + 2
                Name = ''
                for z in range (len(labels_array)):
                    Name = Name + labels_array[z] + '.'
                Name = Name[:-1]
                print("Name: " + Name)
                print("Name Length: " + str(len(Name)))
                print("Label Count: " + str(len(labels_array)))
                print("Type: " + str(Type))
                print("Class: " + str(Class))
                print("Time to Live: " + str(TTL))
                print("Data Length: " + str(DLength))
                labels_array = []
                if(Type == 1 or Type == 28):
                    IPv = ''
                    for x in range (DLength):
                        if(Type == 1):
                            IPv = IPv + str(int.from_bytes(body[i:i+1], byteorder='big')) + '.'
                            i = i + 1
                        else:
                            IPv = IPv + body[i:i+2].hex() + ':'
                            i = i + 2
                            if(x == 7):
                                break
                    IPv = IPv[:-1]
                    print("Address: " + IPv + "\n")
                if(Type == 5):
                    while(True):
                        size = int.from_bytes(body[i:i+1], byteorder='big')
                        i = i + 1
                        if(size == 0):
                            cname = ''
                            for z in range (len(labels_array)):
                                cname = cname + labels_array[z] + '.'
                            cname = cname[:-1]
                            print("CNAME: " + cname + '\n')
                            labels_array = []
                            break
                        for y in range (size):
                            label = label + body[i:i+1].decode('ascii')
                            i = i + 1
                        labels_array.append(label)
                        label = ''
                break
            for y in range (size):
                label = label + body[i:i+1].decode('ascii')
                i = i + 1
            labels_array.append(label)



def send_request(hostname, server, port, ipv6=False):
    if ipv6:
        print(f"Sending DNS request for {hostname} to {server}:{port} using IPv6.")
    else:
        print(f"Sending DNS request for {hostname} to {server}:{port} using IPv4.")

    sock = socket.create_connection((server, port))
    sock.sendall(create_request(hostname))

    while(True):
        data = sock.recv(1024)
        process_response(data)
        if not data:
            break

def main():
    parser = argparse.ArgumentParser(description="DNS Request Program")

    # Flags for creating, sending, and processing requests
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--create-request", action="store_true", help="Create a DNS request")
    group.add_argument("--process-response", action="store_true", help="Process the DNS response")
    group.add_argument("--send-request", action="store_true", help="Send a DNS request")

    # Common arguments
    parser.add_argument("hostname", type=str, nargs="?", help="The hostname for the DNS request")
    parser.add_argument("--ipv4", action="store_true", help="Use IPv4 address")
    parser.add_argument("--ipv6", action="store_true", help="Use IPv6 address")

    # Additional arguments for sending request
    parser.add_argument("--server", type=str, help="DNS server to send request to")
    parser.add_argument("--port", type=int, help="Port of the DNS server")

    # Parse arguments
    args = parser.parse_args()

    # Handle the create-request flag
    if args.create_request:
        if args.hostname is None:
            print("Error: --create-request requires a hostname.")
            return
        if args.ipv4 and args.ipv6:
            print("Error: You cannot specify both --ipv4 and --ipv6 at the same time.")
            return
        if args.ipv4:
            create_request(args.hostname, ipv6=False)
        elif args.ipv6:
            create_request(args.hostname, ipv6=True)
        else:
            print("Error: You must specify either --ipv4 or --ipv6.")
            return

    # Handle the send-request flag
    elif args.send_request:
        if args.hostname is None:
            print("Error: --send-request requires a hostname.")
            return
        if not args.server or not args.port:
            print("Error: --server and --port are required when using --send-request.")
            return

        if args.ipv4 and args.ipv6:
            print("Error: You cannot specify both --ipv4 and --ipv6 at the same time.")
            return
        if args.ipv4:
            send_request(args.hostname, args.server, args.port, ipv6=False)
        elif args.ipv6:
            send_request(args.hostname, args.server, args.port, ipv6=True)
        else:
            print("Error: You must specify either --ipv4 or --ipv6 for the request.")
            return

    # Handle the process-response flag
    elif args.process_response:
            data = sys.stdin.buffer.read()
            if (data == ''):
                print("Error: there is no data!")
                return
            process_response(data)

    else:
        print("Error: You must specify either --create-request, --send-request, or --process-response.")
        return

if __name__ == "__main__":
    main()
