import sys
import socket
import select

def main():
    
    buffer_size = 1024
    
    hostname = "localhost" #default hostname
    port = 1337 #default port
    
    if len(sys.argv) == 2: #hostname provided, no port
        hostname = sys.argv[1]
    
    if len(sys.argv) == 3: #both hostname and port provided
        hostname = sys.argv[1]
        port = int(sys.argv[2])
    
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    
    ##LOGIN SEQUENCE ##
    try:
        sock.connect((hostname, port))
        in_msg = sock.recv(buffer_size).decode()
        print(in_msg)
        
        while True:
            username = input("Username: ")
            password = input("Password: ")
            user_info = f"User: {username}\nPassword: {password}"
            sock.send(user_info.encode())
            in_msg = sock.recv(buffer_size).decode()
            
            if in_msg == "Failed to login.":
                print(in_msg)
            else:
                print(in_msg)
                break
            
    except (ConnectionRefusedError) as e:
        print("Couldn't connect to server")
        sys.exit(1)
        
    
    ## COMMANDS SEQUENCE (AFTER LOGIN) ##
    while True:
        user_command = input("Enter command (parentheses/lcm/caesar/quit): ")
        
        
        if user_command.strip() == "quit": #quit command, break immidieatlty
            sock.send(user_command.encode())
            break
        
        
        sock.send(user_command.encode())
        in_msg = sock.recv(buffer_size)
        
        if not in_msg: #message is empty
            print("Server disconnected")
            break
        else:
            decoded_msg = in_msg.decode()
            print(decoded_msg)
            
    sock.close()
    
if __name__ == "__main__":
    main()