# Othello Game

![client2](https://github.com/jbrun0r/assets/blob/main/Othello/Screenshot%202025-01-06%20at%2020.18.30.png?raw=true)

A multiplayer Othello (Reversi) game implemented in Python, using RPC for real-time communication between server and clients. The game features a GUI built with `pygame`, supporting two players connected over a local network.

## Clone the Repository

```bash
git clone https://github.com/jbrun0r/Othello-PDP.git
cd Othello-PDP
```

## Set Up a Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Start the Server

```bash
python server.py
```

output:

```bash
pygame-ce 2.5.1 (SDL 2.30.6, Python 3.9.6)
Enter the server port:12345
Othello-Server Running: ('192.168.x.x', 12345)
```

## Start the Clients

To play the game, you need to start two clients. The clients can run on any machine within the local network. When you execute the client, you will need to enter the host (IP address) of the server and the port number.

### Start the clients:

```bash
python client.py
```

output:

```bash
pygame-ce 2.5.1 (SDL 2.30.6, Python 3.9.6)
Enter the server IP to connect: 192.168.x.x
Enter the server port to connect: 12345
Connected.
```

"Note that the chat and the give up buttons will only be displayed when the opponent connects."

## Features

- **Multiplayer Gameplay**: Connects two players over a network
- **Real-Time Updates**: Both players see moves in real-time
- **In-Game Chat**: Basic chat functionality between players
- **Game Options**: Options to give up or restart the game

## Requirements

- **Python**: Version 3.9 or higher
- **pygame**: Community (for GUI support)
