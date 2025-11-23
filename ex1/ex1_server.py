#!/usr/bin/python3
"""
Multi-Client TCP Server with Authentication and Command Processing

This server handles multiple simultaneous clients using select() for I/O multiplexing.
Clients must authenticate before accessing commands.

Supported Commands:
    - parentheses: X - Check if parentheses string is balanced
    - lcm: X Y - Calculate least common multiple of two integers
    - caesar: plaintext X - Encrypt text using Caesar cipher with shift X
    - quit - Disconnect from server

Usage:
    python ex1_server.py <users_file> [port]
    
    users_file: Tab-delimited file with username<TAB>password per line
    port: Optional listening port (default: 1337)

Example:
    python ex1_server.py users_list.txt 8080

Authentication Protocol:
    - Client sends: "User: <username>"
    - Server replies: "OK"
    - Client sends: "Password: <password>"
    - Server replies: success or failure message

Command Format:
    - All commands must be sent as: "command: parameters"
    - On invalid input or authentication failure, the server responds with an error and may disconnect the client.
"""

import sys
import socket
import select
import math
import string


def parentheses(X):
    """
    Check if a string of parentheses is balanced.
    
    A balanced string means:
    - Every opening '(' has a matching closing ')'
    - Closing ')' never appears before its matching opening '('
    
    Args:
        X (str): String containing only '(' and ')' characters
        
    Returns:
        str: Success message indicating if balanced (yes/no), or error message
    """
    open_count = 0  # Counter for unmatched opening parentheses
    
    # Check each character
    for char in X:
        if char not in '()':
            return "ERROR: The string isn't only parentheses"
        elif char == '(':
            open_count += 1  # Found opening - increment counter
        else:  # char == ')'
            open_count -= 1  # Found closing - decrement counter
            
            # If counter goes negative, we have a closing ')' without matching '('
            if open_count < 0:
                return "the parentheses are balanced: no"
    
    # At the end, counter should be 0 (all opens matched with closes)
    if open_count == 0:
        return "the parentheses are balanced: yes"
    else:
        return "the parentheses are balanced: no"


def caesar(plaintext, X):
    """
    Encrypt plaintext using Caesar cipher with shift X.
    Only English letters are allowed. Output is all lowercase.

    Args:
        plaintext (str): The text to encrypt (letters and spaces only)
        X (int): The shift amount (can be positive or negative)

    Returns:
        str: The encrypted text in all lowercase, or an error message if input is invalid
    """
    result = ""
    for char in plaintext:
        if char.isalpha():
            # Only allow English letters
            if ('a' <= char.lower() <= 'z'):
                base = ord('a')
                pos = ord(char.lower()) - base
                new_pos = (pos + X) % 26
                new_char = chr(new_pos + base)
                result += new_char
            else:
                return "error: invalid input\n"  # Non-English letter
        elif char.isspace():
            result += char
        else:
            return "error: invalid input\n"  # Not a letter or space
    return result


def command_handler(command_data):
    """
    Parse and execute client commands.
    
    Args:
        command_data (str): Command string in format "command: parameters"
        
    Returns:
        str: Response message to send to client, or None to disconnect client
        
    Commands:
        parentheses: X - Validate parentheses balance
        lcm: X Y - Calculate least common multiple
        caesar: plaintext X - Caesar cipher encryption
        quit - Signal disconnect
        
    Returns None for:
        - Unknown command
        - quit command
    """    
    command_data = command_data.strip()
    
    if command_data == "quit":
        return None
    
    if ':' not in command_data:
        return "ERROR: Invalid command format\n"
    
    match command_data.split(':', 1)[0].strip():
        case "parentheses":
            # Extract parameter
            X = command_data.split(':', 1)[1].strip()
            if not X:
                return "ERROR: parentheses requires a parameter\n"
            
            # Execute and return result
            answer = parentheses(X)
            return f"{answer}\n"
        
        case "lcm":
            # Parse two integer parameters
            params_list = command_data.split(':', 1)[1].strip().split()
            if len(params_list) != 2:
                return "ERROR: lcm requires exactly 2 parameters\n"
            
            # Validate both are integers
            try:
                X = int(params_list[0])
                Y = int(params_list[1])
            except ValueError:
                return "ERROR: lcm parameters must be integers\n"

            # Calculate and return LCM
            answer = math.lcm(X, Y)
            return f"the lcm is: {answer}\n"
        
        case "caesar":
            # Parse plaintext and shift (split from right to handle spaces in plaintext)
            params_list = command_data.split(':', 1)[1].strip().rsplit(' ', 1)
            
            if len(params_list) != 2:
                return "ERROR: caesar requires plaintext and shift\n"
            
            # Validate shift is integer
            try:
                X = int(params_list[1])
            except ValueError:
                return "ERROR: shift must be an integer\n"
            
            plaintext = params_list[0]
            
            # Validate plaintext contains only letters and spaces
            for char in plaintext:
                if not (char.isalpha() or char.isspace()):
                    return "error: invalid input\n"  # Assignment requirement
            
            # Encrypt and return result
            answer = caesar(plaintext, X)
            return f"The ciphertext is: {answer}\n"
        
        case _:
            return "ERROR: Unknown command\n"


def main():
    """
    Main server loop - handles multiple clients using select().
    
    Server Flow:
        1. Load user credentials from file
        2. Create and bind server socket
        3. Listen for connections
        4. Use select() to monitor all sockets (server + clients)
        5. Accept new clients and add to monitoring list
        6. Handle client authentication with retries
        7. Process client commands until quit or disconnect
        8. Clean up closed connections
    """
    # Configuration
    welcome_msg = "Welcome! Please log in.\n"
    buffer_size = 1024
    timeout = 5  # Select timeout in seconds
    
    
    # Validate command-line arguments
    if len(sys.argv) < 2:
        print("ERROR: no users list")
        sys.exit(1)
    
    # Parse port (optional argument)
    listen_port = 1337  # Default port
    if len(sys.argv) == 3:
        listen_port = int(sys.argv[2])
    
    # Load user credentials from file
    users_file = sys.argv[1]
    users_dict = {}  # username -> password mapping
    
    try:
        with open(users_file, 'r') as f:
            for line in f:
                line = line.strip()
                parts = line.split('\t')  # Tab-delimited format
                
                # Only add valid entries with both username and password
                if len(parts) == 2:
                    username = parts[0]
                    password = parts[1]
                    users_dict[username] = password
            
            print(f"Loaded {len(users_dict)} users")
    except FileNotFoundError:
        print(f"ERROR: file '{users_file}' not found")
        sys.exit(1)
    
    # Create server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('', listen_port))  # Bind to all interfaces
    server_socket.listen(5)  # Queue up to 5 connections
    print(f"Server listening on port {listen_port}")
    
    # Initialize socket lists for select()
    rlist = [server_socket]  # Sockets to monitor for reading
    wlist = []  # Sockets to monitor for writing (unused - immediate sends)
    client_states = {}      # client_sock: 'waiting_username' | 'waiting_password' | 'authenticated'
    client_usernames = {}   # client_sock: username (while authenticating)

    # Main server loop
    while True:
        # Monitor sockets for activity
        # Returns: (readable sockets, writable sockets, error sockets)
        readable, writeable, _ = select.select(rlist, wlist, [], timeout)
        
        # Handle new client connections
        if server_socket in readable:
            client_socket, client_address = server_socket.accept()
            rlist.append(client_socket)
            client_socket.send(welcome_msg.encode())
            client_states[client_socket] = 'waiting_username'

        # Handle existing client sockets
        for client_sock in readable:
            # Skip the server socket (already handled above)
            if client_sock is not server_socket:
                # Receive data from client
                client_data = client_sock.recv(buffer_size)
                
                # Check if client disconnected
                if not client_data:
                    rlist.remove(client_sock)
                    client_states.pop(client_sock, None)
                    client_usernames.pop(client_sock, None)
                    client_sock.close()
                    continue

                state = client_states.get(client_sock, 'waiting_username')

                if state == 'waiting_username':
                    # Expecting: "User: username"
                    try:
                        decoded = client_data.decode()
                        username = decoded.split(':', 1)[1].strip()
                        client_usernames[client_sock] = username
                        client_states[client_sock] = 'waiting_password'
                        client_sock.send(b'OK')
                    except Exception:
                        client_sock.send(b'Invalid login format\n')
                        rlist.remove(client_sock)
                        client_states.pop(client_sock, None)
                        client_usernames.pop(client_sock, None)
                        client_sock.close()

                elif state == 'waiting_password':
                    # Expecting: "Password: password"
                    try:
                        decoded = client_data.decode()
                        password = decoded.split(':', 1)[1].strip()
                        username = client_usernames.get(client_sock)
                        if username in users_dict and users_dict[username] == password:
                            client_sock.send(f"Hi {username}, good to see you\n".encode())
                            client_states[client_sock] = 'authenticated'
                            client_usernames.pop(client_sock, None)
                        else:
                            client_sock.send(b'Failed to login.\n')
                            client_states[client_sock] = 'waiting_username'
                            client_usernames.pop(client_sock, None)
                    except Exception:
                        client_sock.send(b'Invalid login format\n')
                        rlist.remove(client_sock)
                        client_states.pop(client_sock, None)
                        client_usernames.pop(client_sock, None)
                        client_sock.close()

                elif state == 'authenticated':
                    response = command_handler(client_data.decode())
                    if response is None:
                        rlist.remove(client_sock)
                        client_states.pop(client_sock, None)
                        client_sock.close()
                    elif response.lower().startswith("error:"): ## only because of caesar error message
                        client_sock.send(response.encode())
                        rlist.remove(client_sock)
                        client_states.pop(client_sock, None)
                        client_sock.close()
                    else:
                        client_sock.send(response.encode())

if __name__ == "__main__":
    main()