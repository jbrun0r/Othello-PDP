import socket
import json
import pygame
import threading

from app.enums.message import MessageType
from app._class.Grid import DrawableGrid


class Client:
    def __init__(self, host='0.0.0.0', port=5555):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        pygame.init()
        self.screen = pygame.display.set_mode((1100, 800), pygame.DOUBLEBUF)
        self.clock = pygame.time.Clock()

        self.current_player = 1
        self.turn = 1

        self.grid = DrawableGrid(8, 8, (80, 80), self)

        self.RUN = True

        self.INPUT_TEXT = ''
        self.FONT = pygame.font.SysFont('arial', 18)
        self.chat_history = []

        self.white = '2: white'
        self.black = '2: black'

    def connect(self):
        try:
            self.socket.connect((self.host, self.port))
            print("Connected.")
        except ConnectionRefusedError:
            print("Failed to connect to the server.")
            return

    def run(self):
        """Inicia a thread de recebimento de mensagens."""
        self.get_server_address()
        self.connect()
        receive_thread = threading.Thread(target=self.receive_messages)
        receive_thread.daemon = True
        receive_thread.start()

    def run_GUI(self):
        client_host, client_port = self.socket.getsockname()
        server_host, server_port = self.socket.getpeername()
        pygame.display.set_caption(f"Othello-client {client_host}:{client_port} connected to server {server_host}:{server_port}")
        while self.RUN == True:
            self.input()
            self.draw()
            self.clock.tick(60)

    def input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.RUN = False
            
            if event.type == pygame.TEXTINPUT:
                if len(self.INPUT_TEXT) < 19:
                    self.INPUT_TEXT += event.text
            
            #handle special keys
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    self.INPUT_TEXT = self.INPUT_TEXT[:-1]
                if event.key == pygame.K_RETURN and self.INPUT_TEXT != '':
                    self.send_message_chat(self.INPUT_TEXT)
                    self.chat_history.append(["s", self.INPUT_TEXT])
                    self.INPUT_TEXT = ''

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if self.turn == self.current_player:
                        x, y = pygame.mouse.get_pos()
                        x, y = (x - 80) // 80, (y - 80) // 80
                        valid_cells = self.grid.find_available_moves(self.grid.logic_grid, self.turn)
                        if not valid_cells:
                            pass
                        else:
                            if (y, x) in valid_cells:
                                self.grid.insert_token(self.grid.logic_grid, self.turn, y, x)
                                swappable_tiles = self.grid.get_swappable_tiles(y, x, self.grid.logic_grid, self.turn)
                                for tile in swappable_tiles:
                                    self.grid.animate_transitions(tile, self.turn)
                                    self.grid.logic_grid[tile[0]][tile[1]] *= -1
                                
                                self.send_move(x, y)
                                self.turn *= -1
                # if event.button == with:
                #     self.grid.print_logic_board()

    def update(self, logic_grid, turn):
        self.grid.logic_grid = logic_grid  # Atualiza o grid com a nova lógica

        # Percorre o logic_grid
        for y in range(len(logic_grid)):        # Percorre as linhas
            for x in range(len(logic_grid[y])):  # Percorre as colunas
                if logic_grid[y][x] != 0:  # Verifica se o valor na posição (y, x) não é 0
                    player = logic_grid[y][x]  # Define o jogador (-1 ou 1)
                    # Chama a função insertToken com o jogador e as coordenadas
                    self.grid.insert_token(self.grid.logic_grid, player, y, x)
                    
        self.turn = turn
            
        # pygame.display.update()x  # Atualiza a exibição do pygame
    
    def draw_text(self, text, x, y, color=(250, 250, 250)):
        text_as_image = self.FONT.render(text, True, color)
        self.screen.blit(text_as_image, (x, y))
    
    def draw_chat(self):
        y = 670
        # Pegando as últimas 14 entradas do chat_history, de trás para frente
        for type, content in reversed(self.chat_history[-14:]):
            if type == 'r':
                content = 'r: ' + content
                self.draw_text(content, 805, y, (0, 248, 77))
            else: self.draw_text(content, 805, y)
            y -= 35 # espaco entre cada msg

    def draw(self):
        self.screen.fill((0, 0, 0))  # Clear screen

        # Draw the grid
        self.grid.draw_grid(self.screen)

        # Draw the chat box
        pygame.draw.rect(self.screen, (50, 50, 50), [800, 200, 250, 500])
        pygame.draw.rect(self.screen, (50, 50, 50), [800, 720, 250, 30])
        
        # Draw static text
        self.draw_text('chat', 800, 175)

        # Draw placar
        self.draw_text(self.white, 800, 60)
        self.draw_text(self.black, 800, 95)

        # Draw chat history
        self.draw_chat()

        # Draw input text
        self.draw_text(self.INPUT_TEXT, 805, 725)

        # Update the display
        pygame.display.flip()

    def receive_messages(self):
        try:
            while True:
                if _message := self.socket.recv(4096).decode():
                    try:
                        message = json.loads(_message)
                        self.handle_message(message)
                    except json.JSONDecodeError:
                        print("Error decoding the JSON message.")
        except ConnectionResetError:
            print("Connection lost with the server.")
        finally:
            self.socket.close()
    
    def send_move(self, x, y):
        message = {
            "type": MessageType.MOVE.value,
            "x": x,
            "y": y
        }
        json_message = json.dumps(message)
        self.socket.send(json_message.encode())  
    
    def send_message_chat(self, content):
        message = {
            "type": MessageType.CHAT.value,
            "content": content,
            "player": self.current_player * -1
        }
        json_message = json.dumps(message)
        self.socket.send(json_message.encode())

    def process_setup(self, message):
        current_player = message.get('current_player')
        self.current_player = current_player
        if self.current_player == 1:
            self.white += ' *you'
        else: self.black += ' *you'
        self.process_update(message)

    def process_update(self, message):
        grid_logic = message.get('grid')
        turn = message.get('turn')
        self.update(grid_logic, turn)

    def process_chat(self, message):
        content = message.get('content')
        self.chat_history.append(['r', content])

    def handle_message(self, message):

        message_type = message.get('type')
        
        if message_type == MessageType.UPDATE.value:
            self.process_update(message)
            

        elif message_type == MessageType.SETUP.value:
            self.process_setup(message)

        elif message_type == MessageType.CHAT.value:
            self.process_chat(message)

        else:
            print("Unknown message type", message)
    
    def get_server_address(self):
        host = input('host: ')
        port = input('port: ')
        self.host = host
        self.port = int(port)

if __name__ == "__main__":
    client = Client()
    client.run()
    client.run_GUI()    
