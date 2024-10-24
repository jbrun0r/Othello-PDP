import socket
import threading
from enum import Enum
import json

class MessageType(Enum):
    UPDATE = "update"
    MOVE = "move"
    GAME_OVER = "game_over"
    ERROR = "error"
    SETUP = "setup"


#  utility functions
def directions(x, y, minX=0, minY=0, maxX=7, maxY=7):
    """Check to determine which directions are valid from current cell"""
    validdirections = []
    if x != minX: validdirections.append((x-1, y))
    if x != minX and y != minY: validdirections.append((x-1, y-1))
    if x != minX and y != maxY: validdirections.append((x-1, y+1))

    if x!= maxX: validdirections.append((x+1, y))
    if x != maxX and y != minY: validdirections.append((x+1, y-1))
    if x != maxX and y != maxY: validdirections.append((x+1, y+1))

    if y != minY: validdirections.append((x, y-1))
    if y != maxY: validdirections.append((x, y+1))

    return validdirections

#  Classes
class Server:
    def __init__(self):
        self.turn = 1

        self.time = 0

        self.rows = 8
        self.columns = 8

        self.grid = Grid(self.rows, self.columns, (80, 80), self)

        self.RUN = True

    def run(self):
        while self.RUN == True:
            self.update()

    def update(self):
        pass

class Grid:
    def __init__(self, rows, columns, size, main):
        self.GAME = main
        self.y = rows
        self.x = columns
        self.size = size
        self.tokens = {}
        self.gridLogic = self.regenGrid(self.y, self.x)

    def regenGrid(self, rows, columns):
        """generate an empty grid for logic use"""
        grid = []
        for y in range(rows):
            line = []
            for x in range(columns):
                line.append(0)
            grid.append(line)
        self.insertToken(grid, 1, 3, 3)
        self.insertToken(grid, -1, 3, 4)
        self.insertToken(grid, 1, 4, 4)
        self.insertToken(grid, -1, 4, 3)

        return grid

    def printGameLogicBoard(self):
        print('  | A | B | C | D | E | F | G | H |')
        for i, row in enumerate(self.gridLogic):
            line = f'{i} |'.ljust(3, " ")
            for item in row:
                line += f"{item}".center(3, " ") + '|'
            print(line)
        print()

    def findValidCells(self, grid, curPlayer):
        """Performs a check to find all empty cells that are adjacent to opposing player"""
        validCellToClick = []
        for gridX, row in enumerate(grid):
            for gridY, col in enumerate(row):
                if grid[gridX][gridY] != 0:
                    continue
                DIRECTIONS = directions(gridX, gridY) # Encontra todas as celulas vazias

                for direction in DIRECTIONS:
                    dirX, dirY = direction
                    checkedCell = grid[dirX][dirY]

                    if checkedCell == 0 or checkedCell == curPlayer:
                        continue

                    if (gridX, gridY) in validCellToClick:
                        continue

                    validCellToClick.append((gridX, gridY))
        return validCellToClick

    def swappableTiles(self, x, y, grid, player):
        surroundCells = directions(x, y)
        if len(surroundCells) == 0:
            return []

        swappableTiles = []
        for checkCell in surroundCells:
            checkX, checkY = checkCell
            difX, difY = checkX - x, checkY - y
            currentLine = []

            RUN = True
            while RUN:
                if grid[checkX][checkY] == player * -1: # Se a primeira celula é igual ao jogador oposto
                    currentLine.append((checkX, checkY))
                elif grid[checkX][checkY] == player:
                    RUN = False
                    break
                elif grid[checkX][checkY] == 0:
                    currentLine.clear()
                    RUN = False
                checkX += difX
                checkY += difY

                if checkX < 0 or checkX > 7 or checkY < 0 or checkY > 7:
                    currentLine.clear()
                    RUN = False

            if len(currentLine) > 0:
                swappableTiles.extend(currentLine)

        return swappableTiles

    def findAvailMoves(self, grid, turn):
        """Takes the list of validCells and checks each to see if playable"""
        validCells = self.findValidCells(grid, turn)
        playableCells = []

        for cell in validCells:
            x, y = cell
            if cell in playableCells:
                continue
            swapTiles = self.swappableTiles(x, y, grid, turn)

            if len(swapTiles) > 0:
                playableCells.append(cell)

        return playableCells

    def insertToken(self, grid, curplayer, y, x):
        self.tokens[(y, x)] = Token(curplayer, y, x)
        grid[y][x] = self.tokens[(y, x)].player

class Token:
    def __init__(self, player, gridX, gridY):
        self.player = player
        self.gridX = gridX
        self.gridY = gridY
        self.posX = 80 + (gridY * 80)
        self.posY = 80 + (gridX * 80)

class OthelloServer:
    def __init__(self, host='localhost', port=5555):
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen(2)

        self.players = []  # Lista de conexões de jogadores
        self.game = Server()  # Instância do jogo Othello
    
    def send_json(self, conn, dados):
        conn.sendall(json.dumps(dados).encode())

    def handle_message(self, conn, message):
        # Processar a mensagem com base no tipo
        print("Mensagem recebida:", message)
        message_type = message.get('type')
        
        if message_type == "move":
            print(message_type)
            x = message.get('x')
            y = message.get('y')
            validCells = self.game.grid.findAvailMoves(self.game.grid.gridLogic, self.game.turn)
            if not validCells:
                pass
            else:
                if (y, x) in validCells:
                    print(f'{x}{y}')
                    self.game.grid.printGameLogicBoard()
                    print('passou')
                    self.game.grid.insertToken(self.game.grid.gridLogic, self.game.turn, y, x)
                    swappableTiles = self.game.grid.swappableTiles(y, x, self.game.grid.gridLogic, self.game.turn)
                    for tile in swappableTiles:
                        self.game.grid.gridLogic[tile[0]][tile[1]] *= -1
                    self.game.turn *= -1
            self.send_update(conn, self.game.grid.gridLogic)
            
            self.game.grid.printGameLogicBoard()

        else:
            print("Tipo de mensagem desconhecido:", message)

    ## Enviar gridLogic como JSON com seu type
    def send_setup(self, conn, player):
        message = {
            "type": "setup",
            "current_player": player
        }
        json_message = json.dumps(message)
        conn.send(json_message.encode())  # Enviar o JSON codificado como bytes

    def send_update(self, conn, grid_logic):
        print("enviando update")
        message = {
            "type": "update",  # Define o tipo de mensagem
            "grid": grid_logic,  # Envia o grid atual
            "turn": self.game.turn
        }
        self.send_update_to_all_clients(message)
        # json_message = json.dumps(message)
        
        # conn.sendall(json_message.encode())  # Enviar o JSON codificado como bytes
        print("update enviado")
    
    def send_update_to_all_clients(self, data):
        for client in self.players:
            try:
                json_message = json.dumps(data)
                client.send(json_message.encode())
            except Exception as e:
                print(f"Failed to send update to client: {e}")
                self.clients.remove(client)  # Remover cliente em caso de falha

    def handle_client(self, conn, player):
        print(f"Jogador {player} conectado.")

        self.send_setup(conn, player)
        
        self.game.grid.printGameLogicBoard()
        try:
            while True:
                # Recebe e processa mensagens aqui
                data = conn.recv(1024).decode()
                if data:
                    try:
                        message = json.loads(data)  # Converter de JSON para dicionário
                        self.handle_message(conn, message)
                    except json.JSONDecodeError:
                        print("Erro ao decodificar a mensagem JSON.")
        except ConnectionResetError:
            print(f"Jogador {player} desconectado.")
        finally:
            conn.close()

    def start(self):
        client_id = 1  # Primeiro cliente será 1, o segundo será -1
        while client_id >= -1:
            conn, addr = self.server.accept()
            self.players.append(conn)
            threading.Thread(target=self.handle_client, args=(conn, client_id)).start()
            client_id -= 2

# Iniciar o servidor
if __name__ == "__main__":
    server = OthelloServer()
    server.start()
