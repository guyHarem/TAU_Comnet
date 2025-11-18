# Exercise 1: Multi-Client TCP Server

A multi-client TCP server implementation using Python's `select()` for I/O multiplexing. The server provides authentication and command processing capabilities for multiple simultaneous clients.

## Authors
- Guy Harem
- Karen Goldberg

## Files Submitted
- `ex1_server.py` - Multi-client TCP server with select()
- `ex1_client.py` - Interactive TCP client

## Protocol Design

### Transport Protocol: TCP

**Why TCP was chosen:**

1. **Reliability Required**: The application requires guaranteed delivery of commands and responses. Lost packets would cause:
   - Failed authentication attempts
   - Missing command responses
   - Inconsistent application state

2. **Ordered Delivery**: Commands and responses must arrive in sequence. TCP's ordering guarantees that:
   - Login credentials arrive before commands
   - Command responses match their requests
   - Multi-packet messages arrive in correct order

3. **Connection-Oriented**: The server maintains state for each client (authentication status, session). TCP's connection-oriented nature provides:
   - Clear client identification
   - Session boundaries (connect/disconnect events)
   - Built-in connection management

4. **Flow Control**: TCP's flow control prevents:
   - Server overload from fast clients
   - Buffer overflow issues
   - Data loss during transmission

5. **Error Detection**: TCP's checksums ensure data integrity, critical for:
   - Password validation (corrupted passwords would fail authentication)
   - Command parsing (corrupted commands could crash server)
   - Numerical calculations (LCM, Caesar shift values)

**Trade-offs Accepted:**
- Higher overhead than UDP (acceptable for command-response pattern)
- Connection establishment latency (one-time cost per client)
- No broadcast capability (not needed for this application)

### Application Protocol Specification

#### Message Format

All messages are UTF-8 encoded strings terminated with newline (`\n`).

#### Authentication Phase

**Client → Server (Login Request):**
```
This is the code block that represents the suggested code change:
````markdown
User: <username>\nPassword: <password>
```

**Server → Client (Login Response):**
- Success: `Hi <username>, good to see you\n`
- Failure: `Failed to login.\n`
- Invalid format: `Invalid login format\n`

**Authentication Rules:**
- Unlimited retry attempts allowed
- Client must authenticate before sending commands
- Server disconnects client on invalid command format

#### Command Phase

**Command Format:**
```
<command_name>: <parameters>
```

**Supported Commands:**

1. **Parentheses Validation**
   ```
   Client: parentheses: ((()))
   Server: the parentheses are balanced: yes\n
   
   Client: parentheses: ((()
   Server: the parentheses are balanced: no\n
   
   Client: parentheses: abc
   Server: ERROR: The string isn't only parentheses\n
   ```

2. **Least Common Multiple (LCM)**
   ```
   Client: lcm: 12 18
   Server: the lcm is: 36\n
   
   Client: lcm: 15 25
   Server: the lcm is: 75\n
   
   Client: lcm: abc def
   Server: ERROR: lcm parameters must be integers\n
   ```

3. **Caesar Cipher**
   ```
   Client: caesar: hello 3
   Server: The ciphertext is: khoor\n
   
   Client: caesar: Hello World 1
   Server: The ciphertext is: Ifmmp Xpsme\n
   
   Client: caesar: hello123 3
   Server: error: invalid input
   ```

4. **Quit**
   ```
   Client: quit
   Server: (closes connection)
   ```

**Error Handling:**
- Invalid command format (missing `:`) → Server disconnects client
- Unknown command → Server disconnects client
- Invalid parameters → Error message sent, connection remains open

#### Connection Termination

**Client-Initiated:**
- Send `quit` command
- Close socket
- Server removes client from monitoring list

**Server-Initiated:**
- Invalid command received
- Socket error or client disconnect detected
- Server removes client and closes socket

### Protocol State Machine

```
[DISCONNECTED]
    |
    | Client connects
    v
[CONNECTED - Waiting for Login]
    |
    | Receive credentials
    v
[AUTHENTICATING]
    |
    ├─ Valid credentials → [AUTHENTICATED]
    |                           |
    |                           | Receive command
    |                           v
    |                      [PROCESSING COMMAND]
    |                           |
    |                           ├─ Valid command → Send response → [AUTHENTICATED]
    |                           ├─ quit command → [DISCONNECTED]
    |                           └─ Invalid command → [DISCONNECTED]
    |
    └─ Invalid credentials → Send error → [CONNECTED]
```

## Implementation Details

### Server Architecture

**Concurrency Model:** I/O Multiplexing with `select()`
- Single-threaded, event-driven architecture
- No threads or processes needed
- Efficient handling of multiple clients

**Socket Management:**
- `rlist`: Monitored for readable events (incoming data)
- `wlist`: Unused (all writes are immediate and small)
- Server socket and all client sockets in `rlist`

**Client Lifecycle:**
1. `select()` detects new connection on server socket
2. `accept()` creates client socket
3. Client socket added to `rlist`
4. Client authenticates (unlimited retries)
5. Client sends commands, server responds
6. Client quits or disconnects
7. Socket removed from `rlist` and closed

### Client Architecture

**Connection Flow:**
1. Parse command-line arguments (hostname, port)
2. Create TCP socket
3. Connect to server
4. Receive welcome message
5. Enter login loop (retry on failure)
6. Enter command loop (interactive input)
7. Send quit and close on exit

**User Interface:**
- Interactive prompts for username/password
- Clear command prompt with available commands
- Immediate feedback on responses
- Graceful handling of server disconnect

### Security Considerations

**Implemented:**
- Tab-delimited user file (username\tpassword)
- Password verification before command access
- Input validation for all commands

**Not Implemented (out of scope):**
- Password encryption/hashing
- TLS/SSL encryption
- Rate limiting or DOS protection
- Session timeouts

## Usage

### Server

```bash
python ex1_server.py <users_file> [port]
```

**Arguments:**
- `users_file`: Path to tab-delimited file (username\tpassword per line)
- `port`: Optional listening port (default: 1337)

**Example:**
```bash
python ex1_server.py users_list.txt 8080
```

**Output:**
```
Loaded 2 users
Server listening on port 8080
```

### Client

```bash
python ex1_client.py [hostname] [port]
```

**Arguments:**
- `hostname`: Server hostname/IP (default: localhost)
- `port`: Server port (default: 1337)

**Example:**
```bash
python ex1_client.py localhost 8080
```

**Example Session:**
```
Welcome! Please log in
Username: Bob
Password: simplepass
Hi Bob, good to see you

Enter command (parentheses/lcm/caesar/quit): parentheses: (())
the parentheses are balanced: yes

Enter command (parentheses/lcm/caesar/quit): lcm: 12 18
the lcm is: 36

Enter command (parentheses/lcm/caesar/quit): caesar: hello 3
The ciphertext is: khoor

Enter command (parentheses/lcm/caesar/quit): quit
```

## Testing

### Single Client
```bash
# Terminal 1
python ex1_server.py users_list.txt 1337

# Terminal 2
python ex1_client.py localhost 1337
```

### Multiple Clients
```bash
# Terminal 1 - Server
python ex1_server.py users_list.txt 1337

# Terminal 2, 3, 4... - Clients
python ex1_client.py localhost 1337
```

All clients can connect and operate simultaneously.

### Test Cases

**Authentication:**
- ✅ Valid credentials → Success
- ✅ Invalid credentials → Retry allowed
- ✅ Malformed login → Retry allowed
- ✅ Client disconnect during login → Cleanup

**Commands:**
- ✅ `parentheses: (())` → balanced: yes
- ✅ `parentheses: (()` → balanced: no
- ✅ `parentheses: abc` → error
- ✅ `lcm: 12 18` → 36
- ✅ `lcm: 15 25` → 75
- ✅ `lcm: abc def` → error
- ✅ `caesar: hello 3` → khoor
- ✅ `caesar: Hello World 1` → Ifmmp Xpsme
- ✅ `caesar: hello123 3` → error
- ✅ `quit` → disconnect
- ✅ Unknown command → disconnect

**Concurrency:**
- ✅ Multiple clients connect simultaneously
- ✅ Commands from different clients don't interfere
- ✅ Client disconnect doesn't affect others

**Error Handling:**
- ✅ Invalid command format → disconnect
- ✅ Server not running → connection error
- ✅ Server disconnect → client notified
- ✅ Network interruption → graceful handling

## Requirements

- Python 3.10+ (uses `match`/`case` statement)
- Standard library only (no external dependencies)

## File Structure

```
ex1/
├── ex1_server.py        # Server implementation
├── ex1_client.py        # Client implementation
├── users_list.txt       # User credentials (tab-delimited)
└── README.md           # This file
```

## Design Decisions

### Why `select()` over `threading`?
- More efficient for I/O-bound operations
- No race conditions or synchronization complexity
- Lower memory overhead per client
- Simpler debugging and testing

### Why immediate sends over buffering?
- Messages are small (<1KB typically)
- Request-response pattern (no streaming)
- Simplifies implementation
- `send()` unlikely to block with small data

### Why disconnect on invalid command?
- Assignment requirement
- Prevents protocol confusion
- Clear error handling semantics
- Forces clients to maintain valid state

### Why unlimited login retries?
- Better user experience (typos happen)
- Assignment requirement
- Client can choose to give up (disconnect)
- No DOS risk (single connection per client)

### Why UTF-8 encoding?
- Standard text encoding
- Supports international characters
- Compatible with Python's string handling
- Human-readable for debugging

### Why newline-terminated messages?
- Simple to parse
- Clear message boundaries
- Standard convention for text protocols
- Works well with `recv()` buffering

## Known Limitations

1. **No encryption**: Passwords sent in plaintext
2. **No session timeout**: Clients can stay connected indefinitely
3. **No rate limiting**: Fast clients could overload server
4. **No logging**: No audit trail of commands/connections
5. **Single-threaded**: CPU-bound commands block all clients briefly
6. **No message fragmentation handling**: Assumes messages arrive complete
7. **No maximum message size**: Potential buffer overflow with large inputs

## Future Enhancements

- Add TLS/SSL support for encrypted communication
- Implement session timeouts and automatic cleanup
- Add comprehensive logging system
- Support for more commands (file operations, etc.)
- Rate limiting per client
- User management commands (add/remove users)
- Message fragmentation handling for large payloads
- Persistent user database (not just flat file)
- Command history and replay
- Admin commands for server management

## Performance Considerations

**Scalability:**
- Single `select()` call supports hundreds of clients
- Limited by file descriptor limits (~1024 on most systems)
- Low memory overhead per client (~1KB)

**Bottlenecks:**
- Single-threaded: CPU-intensive commands block all clients
- File I/O: User file loaded once at startup
- No connection pooling or resource limits

**Optimization Opportunities:**
- Use `epoll` (Linux) or `kqueue` (BSD/Mac) for better scalability
- Add multi-threading for CPU-bound commands
- Implement connection pooling
- Add caching for frequent operations

## Error Handling Strategy

**Connection Errors:**
- Client disconnect: Remove from `rlist`, close socket, continue serving others
- Server socket error: Log and exit gracefully
- `recv()` returns empty: Client disconnected, cleanup

**Protocol Errors:**
- Invalid command format: Disconnect client
- Unknown command: Disconnect client
- Invalid parameters: Send error message, keep connection

**Authentication Errors:**
- Invalid credentials: Send error, allow retry
- Malformed login: Send error, allow retry
- Client gives up: Cleanup connection

**Exception Handling:**
- `IndexError`/`ValueError` during parsing: Send error, allow retry
- `FileNotFoundError` for user file: Exit with error message
- Network exceptions: Close affected connections

## Protocol Extensions (Not Implemented)

**Potential additions:**
- Binary protocol for efficiency
- Command pipelining (multiple commands in one message)
- Asynchronous responses (server pushes updates)
- Multi-line commands
- File transfer support
- Compression for large responses

## Assignment Requirements Met

✅ TCP server with multiple client support  
✅ Use of `select()` for I/O multiplexing  
✅ Authentication with login retries  
✅ Three computational commands (parentheses, LCM, Caesar)  
✅ Quit command  
✅ Proper error handling and validation  
✅ Command-line argument parsing  
✅ User credentials from file  
✅ Clean connection management  
✅ Documentation and README  

## License

Educational project for TAU Computer Networks course, 2025A.

## Acknowledgments

- Course materials and lectures from TAU Computer Networks
- Python `select` module documentation
- Socket programming best practices from Stevens' "Unix Network Programming"