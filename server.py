import socket
import threading
import json

from app.utils.socket import get_local_LAN_ip
from app.enums.message import MessageType, PlayerStatusType

from app._class.Grid import LogicGrid

from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
from xmlrpc.client import ServerProxy
import threading

class RPCServer:
    def __init__(self, host='0.0.0.0', port=8000):
        self.lock = threading.Lock()
        self.host = host
        self.port = port

        self.conn_white = None
        self.conn_black = None

        self.grid = LogicGrid(8, 8)
        self.turn = -1
        self.game_over = False
        self.white_score = 2
        self.black_score = 2

    def register(self, callback_address):
        """
        Registra o cliente como 1 ou -1.
        """
        with self.lock: # thread-safe
            if self.conn_white is None:
                self.conn_white = ServerProxy(callback_address)
                return self.get_setup(1)
            elif self.conn_black is None:
                self.conn_black = ServerProxy(callback_address)
                return self.get_setup(-1)
            else:
                return 0  # Não há espaço para mais clientes

    def send_message(self, sender, message):
        """
        Recebe a mensagem de um cliente e a encaminha ao outro.
        """
        if sender == 1:
            recipient_conn = self.conn_black  # O destinatário é o cliente -1
            client = 1
        else:
            recipient_conn = self.conn_white  # O destinatário é o cliente 1
            client = -1

        if recipient_conn is not None:
            try:
                data = json.loads(message)
                self.handle_message(data, sender)  # Processa a mensagem
            except (BrokenPipeError, ConnectionResetError):
                print(f"Connection error with recipient client {client}.")
            except json.JSONDecodeError:
                print("Error decoding the JSON message.")
        return f"Client {client} not connected."
    
    def send_message_to(self, message, client):
        if conn := self.conn_white if client == 1 else self.conn_black:
            try:
                conn.receive_message(json.dumps(message))
            except (BrokenPipeError, ConnectionResetError, ConnectionRefusedError):
                print(f"Connection error with client {client}. Removing client.")
                self.handle_disconnection(client)

    def get_setup(self, client):
        rival_status = PlayerStatusType.CONNECTED.value if (
            self.conn_white if client == -1 else self.conn_black
        ) else PlayerStatusType.DISCONNECTED.value

        message = {
            "type": MessageType.SETUP.value,
            "current_player": client, 
            "grid": self.grid.logic_grid, 
            "turn": -1,
            "rival_status": rival_status
        }

        if client == 1 and self.conn_black != None:
            self.send_rival_connected(-1)
        elif client == -1 and self.conn_white != None:
            self.send_rival_connected(1)

        return json.dumps(message)
    
    def send_setup(self, client):
        setup = self.get_setup(client)
        self.send_message_to(json.loads(setup), client)

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
        self.send_message_to(message, client)

    def send_game_over(self):
        message = {
            "type": MessageType.GAME_OVER.value,
        }
        self.send_message_to(message, 1)
        self.send_message_to(message, -1)

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

    def process_restart(self):
        self.grid.reset_logic_grid()
        self.turn = -1
        self.game_over = False
        self.send_setup(1)
        self.send_setup(-1)
    
    def process_give_up(self, client, message):
        rival_status = message.get('rival_status')
        message = {
            "type": MessageType.GIVE_UP.value,
            "rival_status": rival_status
        }
        if rival_status == PlayerStatusType.DISCONNECTED.value:
            return self.handle_disconnection(client)
        self.send_message_to(message, client*-1)

    def handle_disconnection(self, client):
        self.grid.reset_logic_grid()
        self.turn = -1
        self.game_over = False
        if client == 1:
            self.conn_white = None
        else: self.conn_black = None

        self.send_message_to({"type": MessageType.GIVE_UP.value, "rival_status": PlayerStatusType.DISCONNECTED.value}, client*-1)

    def handle_message(self, message, client):
        message_type = message.get('type')
        
        if message_type == MessageType.MOVE.value:
            self.process_move(message)

        elif message_type == MessageType.CHAT.value:
            self.process_chat(message)
        
        elif message_type == MessageType.RESTART.value:
            self.process_restart()
        
        elif message_type == MessageType.GIVE_UP.value:
            self.process_give_up(client, message)

        else:
            print("Unknown message type", message)

    def run(self):
        port = input("Enter the server port:").strip()
        self.port = int(port)

        with SimpleXMLRPCServer((self.host, self.port), allow_none=True) as server:
            # server.register_instance(self)
            server.register_function(self.register, 'register')
            server.register_function(self.send_message, 'send_message')

            print(f"Othello-RPC-Server Running: {get_local_LAN_ip()}:{self.port}")
            
            server.serve_forever()

if __name__ == "__main__":
    server = RPCServer()
    server.run()
