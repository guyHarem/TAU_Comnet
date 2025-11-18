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
        
    Example:
        >>> parentheses("(())")
        "the parentheses are balanced: yes"
        >>> parentheses("(()")
        "the parentheses are balanced: no"
        >>> parentheses(")(")
        "the parentheses are balanced: no"
        >>> parentheses("abc")
        "ERROR: The string isn't only parentheses"
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
    
    Args:
        plaintext (str): Text containing only letters and spaces
        X (int): Shift amount (can be positive or negative)
        
    Returns:
        str: Encrypted ciphertext
        
    Example:
        >>> caesar("hello", 3)
        "khoor"
        >>> caesar("Hello World", 1)
        "Ifmmp Xpsme"
        >>> caesar("abc", -1)
        "zab"
    """
    result = ""
    
    for char in plaintext:
        if char.isalpha():  # Letter character
            # Determine if lowercase or uppercase and set base character
            base = ord('a') if char.islower() else ord('A')
            
            # Get position in alphabet (0-25)
            pos = ord(char) - base
            
            # Apply shift and wrap around using modulo 26
            new_pos = (pos + X) % 26
            
            # Convert back to character
            new_char = chr(new_pos + base)
            result += new_char
        else:  # Space character
            result += char
    
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
        - Invalid command format (missing ':')
        - Unknown command
        - quit command
    """
    # Check for valid command format
    if ':' not in command_data:
        return None  # Invalid format - disconnect client
    
    # Split command name and parameters
    parts = command_data.split(':')
    command_name = parts[0].strip()
    params_raw = parts[1]  # Safe: guaranteed to exist from ':' check
    
    match command_name:
        case "parentheses":
            # Extract parameter
            X = params_raw.strip()
            if not X:
                return "ERROR: parentheses requires a parameter\n"
            
            # Execute and return result
            answer = parentheses(X)
            return f"{answer}\n"
        
        case "lcm":
            # Parse two integer parameters
            params_list = params_raw.strip().split()
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
            params_list = params_raw.strip().rsplit(' ', 1)
            
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
        
        case "quit":
            # Signal to disconnect client
            return None
        
        case _:
            # Unknown command - disconnect client
            return None


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
    timeout = 0.001  # Select timeout in seconds
    
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
    
    # Main server loop
    while True:
        # Monitor sockets for activity
        # Returns: (readable sockets, writable sockets, error sockets)
        readable, writeable, _ = select.select(rlist, wlist, [], timeout)
        
        # Handle new client connections
        if server_socket in readable:
            client_socket, client_address = server_socket.accept()
            rlist.append(client_socket)  # Add to monitoring list
            client_socket.send(welcome_msg.encode())
        
        # Handle existing client sockets
        for client_sock in readable:
            # Skip the server socket (already handled above)
            if client_sock is not server_socket:
                # Receive data from client
                client_data = client_sock.recv(buffer_size)
                
                # Check if client disconnected
                if not client_data:
                    rlist.remove(client_sock)
                    client_sock.close()
                else:
                    # Authentication loop - allow unlimited retries
                    logged_in = False
                    
                    while not logged_in:
                        try:
                            # Parse login credentials
                            # Expected format: "User: username\nPassword: password"
                            decoded_data = client_data.decode()
                            lines = decoded_data.split('\n')
                            username = lines[0].split(':')[1].strip()
                            password = lines[1].split(':')[1].strip()
                            
                            # Verify credentials
                            if username in users_dict and users_dict[username] == password:
                                # Successful login
                                client_sock.send(f"Hi {username}, good to see you\n".encode())
                                logged_in = True
                                
                                # Command processing loop
                                while True:
                                    command_data = client_sock.recv(buffer_size)
                                    
                                    # Client disconnected
                                    if not command_data:
                                        break
                                    
                                    # Process command
                                    response = command_handler(command_data.decode())
                                    
                                    # None response means quit or invalid command
                                    if response is None:
                                        rlist.remove(client_sock)
                                        client_sock.close()
                                        break
                                    
                                    # Send response to client
                                    client_sock.send(response.encode())
                            
                            else:
                                # Failed login - allow retry
                                client_sock.send("Failed to login.\n".encode())
                                
                                # Wait for client to retry
                                client_data = client_sock.recv(buffer_size)
                                if not client_data:  # Client gave up
                                    rlist.remove(client_sock)
                                    client_sock.close()
                                    break
                        
                        except (IndexError, ValueError) as e:
                            # Invalid login format - allow retry
                            client_sock.send("Invalid login format\n".encode())
                            
                            # Wait for client to retry
                            client_data = client_sock.recv(buffer_size)
                            if not client_data:  # Client gave up
                                rlist.remove(client_sock)
                                client_sock.close()
                                break


if __name__ == "__main__":
    main()