import sys
import socket
import os

relocated_files = []
relocated_files.append('redirect-example')

def not_authorized(path):
    body = """
    <html>
    <head><title>403 Not Authorized</title></head>
    <body>
        <h1>403 Not Authorized</h1>
    </body>
    </html>
    """    
    length = len(body)
    answer = b"HTTP/1.1 403 Not Authorized\r\nContent-Type: text/html\r\nContent-Length: " + str(length).encode() + b"\r\nConnection: close\r\n\r\n" + body.encode()
    return answer

def moved_permanently(path):
    body = """
    <html>
    <head><title>301 Moved Permanently</title></head>
    <body>
        <h1>301 Moved Permanently</h1>
    </body>
    </html>
    """    
    length = len(body)
    answer = b"HTTP/1.1 301 Moved Permanently\r\nLocation: /redirect-target.html\r\nContent-Type: text/html\r\nContent-Length: " + str(length).encode() + b"\r\nConnection: close\r\n\r\n" + body.encode()
    return answer

def not_found(path):
    body = """
    <html>
    <head><title>404 Not Found</title></head>
    <body>
        <h1>404 Not Found</h1>
        <p>The requested resource is not found.</p>
    </body>
    </html>
    """    
    length = len(body)
    answer = b"HTTP/1.1 404 Not Found\r\nContent-Type: text/html\r\nContent-Length: " + str(length).encode() + b"\r\nConnection: close\r\n\r\n" + body.encode()
    return answer

def method_not_allowed(path):
    body = """
    <html>
    <head><title>405 Method Not Allowed</title></head>
    <body>
        <h1>405 Method Not Allowed</h1>
        <p>The HTTP method you used is not allowed for the requested resource.</p>
        <p>Please check the allowed methods and try again.</p>
    </body>
    </html>
    """
    length = len(body)
    answer = b"HTTP/1.1 405 Method Not Allowed\r\nContent-Type: text/html\r\nContent-Length: " + str(length).encode() + b"\r\nConnection: close\r\n\r\n" + body.encode()
    return answer

def head_method(file_descriptor, path):
    content_type = path.split('.')[-1]
    if content_type == 'html' or content_type == 'htm':
        content_type = 'text/html'
    else:
        content_type = 'text/plain'

    body = file_descriptor.read()
    length = len(body)
    answer = b"HTTP/1.1 200 OK\r\nContent-Type: " + content_type.encode() + b"\r\nContent-Length: " + str(length).encode() + b"\r\nConnection: keep-alive\r\n\r\n"
    file_descriptor.close()  
    return answer

def get_method(file_descriptor, path):
    content_type = path.split('.')[-1]
    if content_type == 'html' or content_type == 'htm':
        content_type = 'text/html'
    else:
        content_type = 'text/plain'

    body = file_descriptor.read()
    length = len(body)
    answer = b"HTTP/1.1 200 OK\r\nContent-Type: " + content_type.encode() + b"\r\nContent-Length: " + str(length).encode() + b"\r\nConnection: keep-alive\r\n\r\n" + body.encode()
    file_descriptor.close()     
    return answer

def process_request(request):
    print("\nRequest:")
    print(request)
    headers = request.split('\n')
    start_line = headers[0]
    headers = headers [1:]
    http_method = start_line.split(' ')[0]
    path = start_line.split(' ')[1][1:]
    if (http_method != "GET" and http_method != "HEAD"):
        return method_not_allowed(path)
    if path in relocated_files:
        return moved_permanently(path)
    if '/' not in path and os.path.exists(path) and os.path.isfile(path):
        if(http_method == "GET"):
            try:
                file_descriptor = open(path, 'r')
                return get_method(file_descriptor, path)
            except PermissionError:
                return not_authorized(path)
        elif(http_method == "HEAD"):
            try:
                file_descriptor = open(path, 'r')
                return head_method(file_descriptor, path)
            except PermissionError:
                return not_authorized(path)
        else:
            return method_not_allowed(path)
    else:
        return not_found(path)

    # Get all other header values you want to support...
    host = ''
    for entries in headers:
        key = entries.split(' ')[0]
        if key == 'Host:':
            host = entries.split(' ')[1]
    # Get all other header values you want to support...

def main():
    if len(sys.argv) != 3:
        print("Please provide an address and port to start the server")
        return
    address = sys.argv[1]
    port = int(sys.argv[2])
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((address, port))
    server_socket.listen(5)
    myclients = []
    delimeter = b'\r\n\r\n'
    buffer = b''
    while True:
        (clientsocket, address) = server_socket.accept()
        myclients.append(clientsocket)
        print(clientsocket)
        while True:
            chunk = clientsocket.recv(512)
            # The client will send a FIN packet to signal the end of the connection. 
            # The next recv() call will return an empty byte string (b'') to indicate that the connection is closed.
            if chunk  == b'':
                print("CONNECTION TERMINATED BY CLIENT")
                buffer = b''
                break
            print(chunk)
            buffer = buffer + chunk
            index = buffer.find(delimeter)
            if index != -1:
                request = buffer[:index]
                buffer = buffer[index + len(delimeter):]
                clientsocket.send(process_request(request.decode('ascii')))
            else :
                print(buffer)

if __name__ == "__main__":
    main()


