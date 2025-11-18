import sys
import socket
import select
import math
import string

def parentheses(X):
    L_PAREN = 0
    R_PAREN = 0
    for char in X:
        if char not in '()':
            return "ERROR: The string isn't only parentheses"
        elif char == '(':
            L_PAREN += 1
        else:
            R_PAREN += 1
                    
    if(L_PAREN == R_PAREN):
        return "the parentheses are balanced: yes"
    else:
        return "the parentheses are balanced: no"
                
    
def caesar(plaintext, X):
    result = ""
    
    for char in plaintext:
        if char.isalpha(): #alphabet char
            base = ord('a') if char.islower() else ord('A')
            pos = ord(char) - base
            new_pos = (pos + X)%26
            new_char = chr(new_pos + base)
            result += new_char
        else: #Space
            result += char
    
    return result
    
    
def command_handler(command_data):
    if ':' not in command_data:
        return None ##WHY NONE??##
    
    parts = command_data.split(':')
    command_name = parts[0].strip()
    params_raw = parts[1] #its safe, we know parts[1] exist from the if ':' in command_data
    
    match command_name:
        case "parentheses":
            X = params_raw.strip()
            if not X:
                return "ERROR: parentheses requires a parameter\n"
            answer = parentheses(X)
            return f"{answer}\n"
        
        case "lcm":
            params_list = params_raw.strip().split()
            if len(params_list) != 2:
                return "ERROR: lcm requires exactly 2 parameters\n"
            
            try:
                X = int(params_list[0])
                Y = int(params_list[1])
            except ValueError:
                return "ERROR: lcm parameters must be integers\n"

            answer = math.lcm(X, Y)
            return f"the lcm is: {answer}\n"
            
            
        case "caesar":
            params_list = params_raw.strip().rsplit(' ', 1)
            
            if len(params_list) != 2:
                return "ERROR: caesar requires plaintext and shift\n"
            
            try:
                X = int(params_list[1])
            except ValueError:
                return "ERROR: shift must be an integer\n"
            
            plaintext = params_list[0]
            
            for char in plaintext:
                if not (char.isalpha() or char.isspace()):
                    return "error: invalid input" #assigment requiremet, not very informative 
               
            answer = caesar(plaintext, X)
            return f"The ciphertext is: {answer}\n"
        
        case "quit":
            return None
            
        case _:
            return None
        
    
def main():
    welcome_msg = "Welcome! Please log in"
    buffer_size = 1024
    
    if len(sys.argv) < 2: #argument fault
        print("ERROR: no users list")
        sys.exit(1)
        
    ## PORT HANDLE##
    listen_port = 1337 #default value
    if len(sys.argv) == 3:
        listen_port = int(sys.argv[2])
    
    
    ##USERES HANDLE##
    users_file = sys.argv[1]
    users_dict = {}
    try:
        with open(users_file, 'r') as f:
            for line in f:
                line = line.strip()
                parts = line.split('\t')
                if len(parts) ==2: #Only add valid users with username and password
                    username = parts[0]
                    password = parts[1]
                    users_dict[username] = password
            print(f"Loaded {len(users_dict)} users")
    except FileNotFoundError:
        print(f"ERROR: file '{users_file}' not found")
        sys.exit(1)
        
        
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    server_socket.bind(('',listen_port))
    
    server_socket.listen(5)
    print(f"Server listening on port {listen_port}")
    
    rlist = [server_socket]
    wlist = []
    
    ## SERVER RUN ##
    while (True):
        readable, writeable, _ = select.select(rlist, wlist, [], 0.001)
        
        ## NEW CLIENT ACCEPT ##
        if server_socket in readable:
            client_socket, client_address = server_socket.accept()
            rlist.append(client_socket)
            client_socket.send(welcome_msg.encode())
        
        ##CLIENT SOCK HANDLE ##
        for client_sock in readable:
            if client_sock is not server_socket:
                client_data = client_sock.recv(buffer_size)
                if not client_data:
                    rlist.remove(client_sock)
                    client_sock.close()
                else:
                    logged_in = False
                    
                    while not logged_in:
                        try:
                            decoded_data = client_data.decode()
                            lines = decoded_data.split('\n')
                            username = lines[0].split(':')[1].strip()
                            password = lines[1].split(':')[1].strip()
                            
                            #LOGIN VERIFICATION#
                            if username in users_dict and users_dict[username] == password:
                                client_sock.send(f"Hi {username}, good to see you\n".encode())
                                logged_in = True
                                
                                while True:
                                    command_data = client_sock.recv(buffer_size)
                                    if not command_data:
                                        break
                                    
                                    response = command_handler(command_data.decode())
                                    
                                    if response is None:
                                        rlist.remove(client_sock)
                                        client_sock.close()
                                        break
                                    
                                    client_sock.send(response.encode())
                                    
                            else:
                                client_sock.send("Failed to login.\n".encode())
                                client_data = client_sock.recv(buffer_size)
                                if not client_data:
                                    rlist.remove(client_sock)
                                    client_sock.close()
                                    break
                                    
                        except (IndexError, ValueError) as e:
                            client_sock.send("Invalid login format\n".encode())
                            client_data = client_sock.recv(buffer_size)  # Wait for client to retry
                            if not client_data:  # Client disconnected instead of retrying
                                rlist.remove(client_sock)
                                client_sock.close()
                                break

if __name__ == "__main__":
    main()