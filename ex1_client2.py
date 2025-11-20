"""
TCP Client for Multi-Client Server

Interactive client that connects to the TCP server, authenticates,
and sends commands for processing.

The client provides a command-line interface for:
    - Authentication (username/password)
    - Command input (parentheses, lcm, caesar, quit)
    - Response display

Usage:
    python ex1_client.py [hostname] [port]
    
    hostname: Server hostname or IP (default: localhost)
    port: Server port number (default: 1337)

Examples:
    python ex1_client.py
    python ex1_client.py example.com
    python ex1_client.py 192.168.1.100 8080

Author:
    Guy Harem, Karen Goldberg
"""

import sys
import socket
import select


def main():
    """
    Main client function - handles connection, authentication, and commands.
    
    Flow:
        1. Parse command-line arguments (hostname, port)
        2. Create TCP socket and connect to server
        3. Receive welcome message
        4. Authentication loop (retry on failure)
        5. Command loop (send commands, receive responses)
        6. Close connection on quit or disconnect
    
    Exit Codes:
        0: Normal exit (user quit)
        1: Connection error (server not reachable)
    """
    
    # Configuration
    buffer_size = 1024
    
    # Default connection parameters
    hostname = "localhost"  # Default server hostname
    port = 1337  # Default server port
    
    # Parse command-line arguments
    if len(sys.argv) == 2:  # Hostname provided, use default port
        hostname = sys.argv[1]
    
    elif len(sys.argv) == 3:  # Both hostname and port provided
        hostname = sys.argv[1]
        port = int(sys.argv[2])
    
    # Create TCP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    ## LOGIN SEQUENCE ##
    try:
        # Connect to server
        sock.connect((hostname, port))
        
        
        
        # Receive and display welcome message
        in_msg = sock.recv(buffer_size).decode()
        print(in_msg, end='')  # Welcome message includes newline
        
        # Authentication loop - retry until success
        while True:
            # Get credentials from user
            username = input("Username: ")
            password = input("Password: ")
            
            # Format credentials according to protocol
            # Format: "User: <username>\nPassword: <password>"
            username_info = f"User: {username}"
            password_info = f"Password: {password}"
            
            # Send username to server
            sock.send(username_info.encode())
            
            readable, _, _, = select.select([sock], [], [], 5)
                        
            # Receive authentication response
            in_msg = sock.recv(buffer_size).decode()
            
            # Check authentication result
            if in_msg == "Failed to login.\n":
                print(in_msg, end='')  # Display error and retry
            else:
                # Successful login - display welcome message and exit loop
                print(in_msg, end='')  # Success message from server
                break
            
    except ConnectionRefusedError as e:
        # Server is not running or unreachable
        print("Couldn't connect to server")
        sys.exit(1)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    ## COMMANDS SEQUENCE (AFTER LOGIN) ##
    while True:
        # Prompt user for command
        user_command = input("Enter command (parentheses/lcm/caesar/quit): ")
        
        # Handle quit command immediately
        if user_command.strip() == "quit":
            # Send quit to server (protocol requirement)
            sock.send(user_command.encode())
            break  # Exit command loop
        
        # Send command to server
        sock.send(user_command.encode())
        
        # Receive response from server
        in_msg = sock.recv(buffer_size)
        
        # Check if server disconnected
        if not in_msg:  # Empty response means server closed connection
            print("Server disconnected")
            break
        else:
            # Display server response
            decoded_msg = in_msg.decode()
            print(decoded_msg, end='')  # Server responses include newlines
    
    # Clean up - close socket
    sock.close()


if __name__ == "__main__":
    main()