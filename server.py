import socket
import threading
import json

from app.utils.socket import get_local_LAN_ip
from app.enums.message import MessageType

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
        message = {
            "type": MessageType.SETUP.value,
            "current_player": client, 
            "grid": self.grid.logic_grid, 
            "turn": self.turn}
        self.send_message_to(message, client)

    def send_game_over(self,):
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

    def process_give_up(self, client):
        message = {
            "type": MessageType.GIVE_UP.value
        }
        self.send_message_to(message, client*-1)

    def process_restart(self):
        self.grid.reset_logic_grid()
        self.turn -1
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
            self.process_give_up(client)

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
                    try:
                        message = json.loads(data)
                        self.handle_message(conn, message, client)
                    except json.JSONDecodeError:
                        print("Error decoding the JSON message.")
        except ConnectionResetError:
            token = 'White' if client == 1 else 'Black'
            print(f"{token} token client disconnected.")
        finally:
            conn.close()

    def run(self):
        print(f"Server Running: ('{get_local_LAN_ip()}', {self.port})")
        
        self.conn_white, addr_white = self.server.accept()
        print(f"White token client connected: {addr_white}")
        thread_white = threading.Thread(target=self.handle_client, args=(self.conn_white, 1))
        thread_white.start()

        self.conn_black, addr_black = self.server.accept()
        print(f"Black token client connected: {addr_black}")
        thread_black = threading.Thread(target=self.handle_client, args=(self.conn_black, -1))
        thread_black.start()

# Iniciar o servidor
if __name__ == "__main__":
    server = Server()
    server.run()
