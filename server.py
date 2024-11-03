import socket
import threading
import json

from app.utils.socket import get_local_LAN_ip
from app.enums.message import MessageType, PlayerStatusType

from app._class.Grid import LogicGrid


class Server:
    def __init__(self, host='0.0.0.0', port=5555):
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen(2)

        self.conn_white = None
        self.conn_black = None

        self.grid = LogicGrid(8, 8)
        self.turn = -1
        self.game_over = False
        self.white_score = 2
        self.black_score = 2
    
    def send_message_to(self, message, client):
        if conn := self.conn_white if client == 1 else self.conn_black:
            try:
                conn.send(json.dumps(message).encode())
            except (BrokenPipeError, ConnectionResetError):
                print(f"Connection error with client {client}. Removing client.")
                # handler
            except Exception as e:
                print(f"Failed to send update to client {client}: {e}")

    def send_setup(self, client):
        rival_status = PlayerStatusType.CONNECTED.value
        if not self.conn_white or not self.conn_black:
            rival_status = PlayerStatusType.DISCONNECTED.value
        message = {
            "type": MessageType.SETUP.value,
            "current_player": client, 
            "grid": self.grid.logic_grid, 
            "turn": -1,
            "rival_status": rival_status
        }
        self.send_message_to(message, client)

        if self.conn_white and self.conn_black:
            self.send_rival_connected(client)

    def send_game_over(self):
        message = {
            "type": MessageType.GAME_OVER.value,
        }
        self.send_message_to(message, 1)
        self.send_message_to(message, -1)

    def send_update(self):
        message = {
            "type": MessageType.UPDATE.value,
            "grid": self.grid.logic_grid,
            "turn": self.turn
        }
        self.send_message_to(message, self.turn)
    
    def send_rival_connected(self, client):
        message = {
            "type": MessageType.RIVAL_CONNECTED.value,
            "grid": self.grid.logic_grid,
        }
        self.send_message_to(message, client*-1)

    def process_move(self, message):
        x = message.get('x')
        y = message.get('y')
        if valid_cells := self.grid.find_available_moves(self.grid.logic_grid, self.turn):
            if (y, x) in valid_cells:
                self.grid.insert_token(self.grid.logic_grid, self.turn, y, x)
                swappable_tiles = self.grid.get_swappable_tiles(y, x, self.grid.logic_grid, self.turn)
                for tile in swappable_tiles:
                    self.grid.logic_grid[tile[0]][tile[1]] *= -1
                self.turn *= -1
                self.send_update()

                if not self.grid.find_available_moves(self.grid.logic_grid, self.turn):
                    self.game_over = True
                    self.send_game_over()

    def process_chat(self, message):
        content = message.get('content')
        client = message.get('player')
        message = {
        "type": MessageType.CHAT.value,
        "content": content, 
        }
        self.send_message_to(message, client)

    def process_give_up(self, conn, client, message):
        rival_status = message.get('rival_status')
        message = {
            "type": MessageType.GIVE_UP.value,
            "rival_status": rival_status
        }
        self.send_message_to(message, client*-1)
        if rival_status == PlayerStatusType.DISCONNECTED.value:
            self.grid.reset_logic_grid()
            self.turn = -1
            self.game_over = False
            conn.close()

    def process_restart(self):
        self.grid.reset_logic_grid()
        self.turn = -1
        self.game_over = False
        self.send_setup(1)
        self.send_setup(-1)
    
    def handle_message(self, conn, message, client):
        message_type = message.get('type')
        
        if message_type == MessageType.MOVE.value:
            self.process_move(message)
            
        elif message_type == MessageType.CHAT.value:
            self.process_chat(message)

        elif message_type == MessageType.GIVE_UP.value:
            self.process_give_up(conn, client, message)

        elif message_type == MessageType.RESTART.value:
            self.process_restart()

        else:
            print("Unknown message type", message)
            
    def handle_client(self, conn, client):
        self.send_setup(client)
        
        try:
            while True:
                data = conn.recv(1024).decode()
                if data:
                    print(f'{client}: {data}')
                    try:
                        message = json.loads(data)
                        self.handle_message(conn, message, client)
                    except json.JSONDecodeError:
                        print("Error decoding the JSON message.")
        except (ConnectionResetError, BrokenPipeError, OSError):
            print(f"Client {client} disconnected.")
            self.remove_client(client)
        finally:
            conn.close()

    def remove_client(self, client):
        """Remove the specified client and set up the server to accept a new client in that position."""
        if client == 1:
            self.conn_white = None
        else:
            self.conn_black = None
        print(f"Client {client} removed. Waiting for new connection.")

        # Start a new thread to accept a new client to fill the spot
        threading.Thread(target=self.accept_new_client, args=(client,)).start()

    def accept_new_client(self, client_color):
        """Accepts a new client and assigns it to the specified color position."""
        conn, addr = self.server.accept()
        print(f"New client connected: {addr} as {'white' if client_color == 1 else 'black'}")
        if client_color == 1:
            self.conn_white = conn
        else:
            self.conn_black = conn

        threading.Thread(target=self.handle_client, args=(conn, client_color)).start()

    def run(self):
        print(f"Othello-Server Running: ('{get_local_LAN_ip()}', {self.port})")
        
        # Initial client connections for white and black
        self.accept_new_client(1)
        self.accept_new_client(-1)

# Iniciar o servidor
if __name__ == "__main__":
    server = Server()
    server.run()
