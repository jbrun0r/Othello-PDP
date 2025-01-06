import socket
import json
import pygame
import threading

from app.enums.message import MessageType, PlayerStatusType
from app._class.Grid import DrawableGrid

from xmlrpc.client import ServerProxy
from xmlrpc.server import SimpleXMLRPCServer

class Client:
    def __init__(self, host='0.0.0.0', port=5555):
        self.host = host
        self.port = port

        pygame.init()
        self.screen = pygame.display.set_mode((1100, 800), pygame.DOUBLEBUF)
        self.clock = pygame.time.Clock()

        self.current_player = 1
        self.turn = -1

        self.grid = DrawableGrid(8, 8, (80, 80), self)
        self.game_over = False
        self.RUN = True

        self.INPUT_TEXT = ''
        self.FONT = pygame.font.SysFont('arial', 18)
        self.chat_history = []

        self.white_score = 2
        self.white_score_text = 'white'
        self.black_score = 2
        self.black_score_text = 'black'

        self.rival_status = PlayerStatusType.DISCONNECTED.value

        self.remote_server = None
        self.callback_address = None

    def start_callback_server(self, port=0):
        """
        Inicia um servidor de callback XML-RPC para receber mensagens.
        """
        def receive_message(message):
            print(message)
            msg = json.loads(message)
            print(f"\nMessage received: {msg}")
            self.handle_message(msg)
            return True

        # Inicia o servidor e captura o endereço
        callback_server = SimpleXMLRPCServer(("0.0.0.0", port), allow_none=True, logRequests=False)
        callback_server.register_function(receive_message, "receive_message")

        # Obtém a porta usada se `port=0` foi passado
        assigned_port = callback_server.server_address[1]

        threading.Thread(target=callback_server.serve_forever, daemon=True).start()
        return f"http://{self.host}:{assigned_port}"

    def register(self):
        setup_data = self.remote_server.register()
        print(json.loads(setup_data))
        self.process_setup(json.loads(setup_data))

        print(f"Connected as Client {self.current_player}")


        self.callback_address = self.start_callback_server()
        print(f"Listening for messages on {self.callback_address}...")
        self.remote_server.receive_callback(self.current_player, self.callback_address)

    def run(self):
        host = input('Enter the server IP to connect: ').strip()
        port = input('Enter the server port to connect: ').strip()
        self.host = host
        self.port = int(port)
        self.remote_server = ServerProxy(f"http://{self.host}:{self.port}/", allow_none=True)
        self.register()

    def run_GUI(self):
        pygame.display.set_caption(f"Othello-Client-RPC, Listening on: {self.callback_address}, Calling on: http://{self.host}:{self.port}")

        while self.RUN:
            self.input()
            self.draw()
            self.clock.tick(60)

    def receive_messages(self):
        try:
            while self.RUN:
                if _message := self.socket.recv(4096).decode():
                    print()
                    print(_message)
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
        self.remote_server.send_message(self.current_player*-1, json.dumps(message))
    
    def send_message_chat(self, content):
        message = {
            "type": MessageType.CHAT.value,
            "content": content,
            "player": self.current_player * -1
        }
        self.remote_server.send_message(self.current_player*-1, json.dumps(message))

    def send_give_up(self, rival_status):
        message = {
            "type": MessageType.GIVE_UP.value,
            "rival_status": rival_status
        }
        self.remote_server.send_message(self.current_player*-1, json.dumps(message))
        self.game_over = True

    def send_restart(self):
        message = {
            "type": MessageType.RESTART.value,
        }
        self.remote_server.send_message(self.current_player*-1, json.dumps(message))

    def process_setup(self, message):
        current_player = message.get('current_player')
        rival_status = message.get('rival_status')

        self.game_over = False

        self.current_player = current_player
        self.rival_status = rival_status
        self.turn = -1
        self.white_score = 2
        self.black_score = 2

        self.process_score()

        if self.rival_status == PlayerStatusType.CONNECTED.value:
            rival_status = ''
        
        if self.current_player == 1:
            self.white_score_text = 'white # YOU'
            self.black_score_text = 'black ' + rival_status
        else: 
            self.black_score_text = 'black # YOU'
            self.white_score_text = 'white ' + rival_status

        self.grid.tokens.clear()
        grid_logic = message.get('grid')
        self.update(grid_logic, -1)
        self.game_over = False

    def process_update(self, message):
        grid_logic = message.get('grid')
        turn = message.get('turn')
        self.update(grid_logic, turn)

    def process_rival_connected(self, message):
        self.turn = -1
        self.white_score = 2
        self.black_score = 2

        if self.current_player == 1:
            self.white_score_text = 'white # YOU'
            self.black_score_text = 'black '
        else: 
            self.black_score_text = 'black # YOU'
            self.white_score_text = 'white '
        
        self.grid.tokens.clear()
        grid_logic = message.get('grid')
        self.update(grid_logic, -1)
        self.game_over = False
        self.rival_status = PlayerStatusType.CONNECTED.value
        # self.chat_history.append(['i', f'[INFO] rival CONNECTED'])
    
    def process_chat(self, message):
        content = message.get('content')
        self.chat_history.append(['r', content])
    
    def process_gamer_over(self):
        self.game_over = True
        if self.white_score > self.black_score:
                self.white_score_text += ' WON!'
                self.black_score_text += ' LOST!'
        
        elif self.white_score < self.black_score:
            self.black_score_text += ' WON!'
            self.white_score_text += ' LOST!'
        
        else:
            self.black_score_text += ' DRAW'
            self.white_score_text += ' DRAW'
    
    def process_give_up(self, message):
        self.game_over = True
        rival_status = message.get('rival_status')

        if rival_status == PlayerStatusType.DISCONNECTED.value:
            self.rival_status = rival_status

        if self.current_player == -1:
            self.black_score_text += ' WON!'
            self.white_score_text += ' ' + rival_status
        else:
            self.white_score_text += ' WON!'
            self.black_score_text += ' ' + rival_status

    def handle_message(self, message):

        message_type = message.get('type')
        
        if message_type == MessageType.UPDATE.value:
            self.process_update(message)
            
        elif message_type == MessageType.SETUP.value:
            self.process_setup(message)

        elif message_type == MessageType.RIVAL_CONNECTED.value:
            self.process_rival_connected(message)
        
        elif message_type == MessageType.CHAT.value:
            self.process_chat(message)

        elif message_type == MessageType.GAME_OVER.value:
            self.process_gamer_over()
        
        elif message_type == MessageType.GIVE_UP.value:
            self.process_give_up(message)

        else:
            print("Unknown message type", message)
    
    def get_server_address(self):
        host = input('Enter the server IP to connect: ').strip()
        port = input('Enter the server port to connect: ').strip()
        self.host = host
        self.port = int(port)

    def input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.send_give_up(PlayerStatusType.DISCONNECTED.value)
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
                    x, y = pygame.mouse.get_pos()

                    if self.game_over:
                        # if tap restart button
                        if 800 <= x <= (800+250) and 130 <= y <= (130+30):
                            print()
                            self.send_restart()
                    else:
                        # if give up
                        if 800 <= x <= (800+250) and 130 <= y <= (130+30):
                            self.send_give_up(PlayerStatusType.GAVE_UP.value)
                            self.game_over = True
                            if self.current_player == 1:
                                self.black_score_text += ' WON!'
                                self.white_score_text += ' ' + PlayerStatusType.GAVE_UP.value
                            else:
                                self.white_score_text += ' WON!'
                                self.black_score_text += ' ' + PlayerStatusType.GAVE_UP.value
                        elif self.turn == self.current_player:
                            x, y = (x - 80) // 80, (y - 80) // 80
                            if valid_cells := self.grid.find_available_moves(self.grid.logic_grid, self.turn):
                                if (y, x) in valid_cells:
                                    self.grid.insert_token(self.grid.logic_grid, self.turn, y, x)
                                    swappable_tiles = self.grid.get_swappable_tiles(y, x, self.grid.logic_grid, self.turn)
                                    for tile in swappable_tiles:
                                        self.grid.animate_transitions(tile, self.turn)
                                        self.grid.logic_grid[tile[0]][tile[1]] *= -1
                                    
                                    self.send_move(x, y)
                                    self.turn *= -1
                                    self.process_score()
                
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
        self.process_score()
        
    def process_score(self):
        self.white_score, self.black_score, count_zeros = self.grid.calculate_score()
            
    def draw_text(self, text, x, y, color=(250, 250, 250)):
        text_as_image = self.FONT.render(text, True, color)
        self.screen.blit(text_as_image, (x, y))
    
    def draw_chat(self):
        # Draw the chat box
        pygame.draw.rect(self.screen, (20, 20, 20), [800, 200, 250, 500])
        pygame.draw.rect(self.screen, (20, 20, 20), [800, 720, 250, 30])
        # Draw static text
        self.draw_text('chat', 800, 175)
        y = 670
        # Pegando as últimas 14 entradas do chat_history, de trás para frente
        for type, content in reversed(self.chat_history[-14:]):
            if type == 'r':
                self.draw_text(content, 805, y)
            # elif type == 'i':
            #     self.draw_text(content, 805, y, (180, 180, 0))
            else: self.draw_text(content, 805, y, (30, 120, 30))
            y -= 35 # espaco entre cada msg
        # Draw input text
        self.draw_text(self.INPUT_TEXT, 805, 725)

    def draw_game_over(self):
        if self.game_over:
            pygame.draw.rect(self.screen, (30, 120, 30), (800, 130, 250, 30))
            self.draw_text('RESTART', 885, 134, (0, 0, 0))

    def draw_give_up(self):
        if not self.game_over:
            pygame.draw.rect(self.screen, (139, 0, 0), (800, 130, 250, 30))
            self.draw_text('GIVE UP', 885, 134)

    def draw(self):
        self.screen.fill((0, 0, 0))  # Clear screen

        # Draw the grid
        self.grid.draw_grid(self.screen)

        # Draw score
        self.draw_text(f'{self.white_score}: {self.white_score_text}', 800, 60)
        self.draw_text(f'{self.black_score}: {self.black_score_text}', 800, 95)

        if self.rival_status == PlayerStatusType.CONNECTED.value:
            # Draw chat history
            self.draw_chat()

            # if game over, draw
            self.draw_game_over()

            # if not game over draw give up button
            self.draw_give_up()

        # Update the display
        pygame.display.flip()

if __name__ == "__main__":
    client = Client()
    client.run()
    client.run_GUI()    
