import socket
import json
from enum import Enum
import pygame
import threading


class MessageType(Enum):
    UPDATE = "update"
    MOVE = "move"
    GAME_OVER = "game_over"
    ERROR = "error"


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

def loadImages(path, size):
    """Load an image into the game, and scale the image"""
    img = pygame.image.load(f"{path}").convert_alpha()
    img = pygame.transform.scale(img, size)
    return img

def loadSpriteSheet(sheet, row, col, newSize, size):
    """creates an empty surface, loads a portion of the spritesheet onto the surface, then return that surface as img"""
    image = pygame.Surface((32, 32)).convert_alpha()
    image.blit(sheet, (0, 0), (row * size[0], col * size[1], size[0], size[1]))
    image = pygame.transform.scale(image, newSize)
    image.set_colorkey('Black')
    return image

#  Classes
class Othello:
    def __init__(self, host='localhost', port=5555):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect()

        pygame.init()
        self.screen = pygame.display.set_mode((1100, 800))
        pygame.display.set_caption('Othello-PPD-Socket')

        self.current_player = 1
        self.turn = 1

        self.time = 0

        self.rows = 8
        self.columns = 8

        self.grid = Grid(self.rows, self.columns, (80, 80), self)

        self.RUN = True

    def run(self):
        while self.RUN == True:
            self.input()
            self.draw()

    def input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.RUN = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 3:
                    self.grid.printGameLogicBoard()

                if event.button == 1:
                    if self.turn == self.current_player:
                        x, y = pygame.mouse.get_pos()
                        x, y = (x - 80) // 80, (y - 80) // 80
                        validCells = self.grid.findAvailMoves(self.grid.gridLogic, self.turn)
                        if not validCells:
                            pass
                        else:
                            if (y, x) in validCells:
                                print(f'{x}{y}')
                                self.grid.printGameLogicBoard()
                                self.grid.insertToken(self.grid.gridLogic, self.turn, y, x)
                                swappableTiles = self.grid.swappableTiles(y, x, self.grid.gridLogic, self.turn)
                                for tile in swappableTiles:
                                    self.grid.animateTransitions(tile, self.turn)
                                    self.grid.gridLogic[tile[0]][tile[1]] *= -1
                                
                                self.send_move(x, y)
                                self.turn *= -1

    def update(self, gridLogic, turn):
        self.grid.gridLogic = gridLogic  # Atualiza o grid com a nova lógica

        # Percorre o gridLogic
        for y in range(len(gridLogic)):        # Percorre as linhas
            for x in range(len(gridLogic[y])):  # Percorre as colunas
                if gridLogic[y][x] != 0:  # Verifica se o valor na posição (y, x) não é 0
                    player = gridLogic[y][x]  # Define o jogador (-1 ou 1)
                    # Chama a função insertToken com o jogador e as coordenadas
                    self.grid.insertToken(self.grid.gridLogic, player, y, x)
                    
        self.turn = turn
            
        # pygame.display.update()x  # Atualiza a exibição do pygame

    def draw(self):
        self.screen.fill((0, 0, 0))
        self.grid.drawGrid(self.screen)
        pygame.display.update()

    def connect(self):
        try:
            self.socket.connect((self.host, self.port))
            print("Conectado ao servidor.")
        except ConnectionRefusedError:
            print("Falha ao conectar ao servidor.")
            return

    def receive_messages(self):
        try:
            while True:
                data = self.socket.recv(4096).decode()
                if data:
                    try:
                        message = json.loads(data)  # Converter de JSON para dicionário
                        self.handle_message(message)
                    except json.JSONDecodeError:
                        print("Erro ao decodificar a mensagem JSON.")
        except ConnectionResetError:
            print("Conexão perdida com o servidor.")
        finally:
            self.socket.close()
    
    def send_move(self, x, y):
        message = {
            "type": "move",
            "x": x,
            "y": y
        }
        json_message = json.dumps(message)
        self.socket.send(json_message.encode())  

    def handle_message(self, message):
        # Processar a mensagem com base no tipo
        print("Mensagem recebida:", message)
        message_type = message.get('type')
        
        if message_type == "update":
            grid_logic = message.get('grid')
            turn = message.get('turn')
            self.update(grid_logic, turn)
            print(f'turn: {self.turn}')
            self.grid.printGameLogicBoard()
            

        elif message_type == "setup":
            current_player = message.get('current_player')
            self.current_player = current_player
            print(f'current_player: {self.current_player}')

        else:
            print("Tipo de mensagem desconhecido:", message)
    
    def start(self):
        """Inicia a thread de recebimento de mensagens."""
        receive_thread = threading.Thread(target=self.receive_messages)
        receive_thread.daemon = True
        receive_thread.start()

class Grid:
    def __init__(self, rows, columns, size, main):
        self.GAME = main
        self.y = rows
        self.x = columns
        self.size = size
        self.whitetoken = loadImages('app/assets/WhiteToken.png', size)
        self.blacktoken = loadImages('app/assets/BlackToken.png', size)
        self.transitionWhiteToBlack = [loadImages(f'app/assets/BlackToWhite{i}.png', self.size) for i in range(1, 4)]
        self.transitionBlackToWhite = [loadImages(f'app/assets/WhiteToBlack{i}.png', self.size) for i in range(1, 4)]
        self.bg = self.loadBackGroundImages()

        self.tokens = {}

        self.gridBg = self.createbgimg()

        self.gridLogic = self.regenGrid(self.y, self.x)

    def loadBackGroundImages(self):
        alpha = 'ABCDEFGHI'
        spriteSheet = pygame.image.load('app/assets/image.png').convert_alpha()
        imageDict = {}
        for i in range(3):
            for j in range(7):
                imageDict[alpha[j]+str(i)] = loadSpriteSheet(spriteSheet, j, i, (self.size), (32, 32))
        return imageDict

    def createbgimg(self):
        gridBg = [
            ['C0', 'D0', 'D0', 'D0', 'D0', 'D0', 'D0', 'D0', 'D0', 'E0'],
            ['C1', 'A0', 'A0', 'A0', 'A0', 'A0', 'A0', 'A0', 'A0', 'E1'],
            ['C1', 'A0', 'A1', 'B1', 'A0', 'A0', 'A1', 'B1', 'A0', 'E1'],
            ['C1', 'A0', 'A2', 'B2', 'A0', 'A0', 'A2', 'B2', 'A0', 'E1'],
            ['C1', 'A0', 'A0', 'A0', 'A0', 'A0', 'A0', 'A0', 'A0', 'E1'],
            ['C1', 'A0', 'A0', 'A0', 'A0', 'A0', 'A0', 'A0', 'A0', 'E1'],
            ['C1', 'A0', 'A1', 'B1', 'A0', 'A0', 'A1', 'B1', 'A0', 'E1'],
            ['C1', 'A0', 'A2', 'B2', 'A0', 'A0', 'A2', 'B2', 'A0', 'E1'],
            ['C1', 'A0', 'A0', 'A0', 'A0', 'A0', 'A0', 'A0', 'A0', 'E1'],
            ['C2', 'D2', 'D2', 'D2', 'D2', 'D2', 'D2', 'D2', 'D2', 'E2'],
        ]
        image = pygame.Surface((960, 960))
        for j, row in enumerate(gridBg):
            for i, img in enumerate(row):
                image.blit(self.bg[img], (i * self.size[0], j * self.size[1]))
        return image

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

    def drawGrid(self, window):
        window.blit(self.gridBg, (0, 0))

        for token in self.tokens.values():
            token.draw(window)

        availMoves = self.findAvailMoves(self.gridLogic, self.GAME.turn)
        if self.GAME.turn == self.GAME.current_player :
            for move in availMoves:
                pygame.draw.rect(window, (240, 240, 240) if self.GAME.current_player == 1 else (50, 50, 50), (80 + (move[1] * 80) + 30, 80 + (move[0] * 80) + 30, 20, 20))

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

            #if len(swapTiles) > 0 and cell not in playableCells:
            if len(swapTiles) > 0:
                playableCells.append(cell)

        return playableCells

    def insertToken(self, grid, curplayer, y, x):
        tokenImage = self.whitetoken if curplayer == 1 else self.blacktoken
        self.tokens[(y, x)] = Token(curplayer, y, x, tokenImage, self.GAME)
        grid[y][x] = self.tokens[(y, x)].player

    def animateTransitions(self, cell, player):
        if player == 1:
            self.tokens[(cell[0], cell[1])].transition(self.transitionWhiteToBlack, self.whitetoken)
        else:
            self.tokens[(cell[0], cell[1])].transition(self.transitionBlackToWhite, self.blacktoken)

class Token:
    def __init__(self, player, gridX, gridY, image, main):
        self.player = player
        self.gridX = gridX
        self.gridY = gridY
        self.posX = 80 + (gridY * 80)
        self.posY = 80 + (gridX * 80)
        self.GAME = main

        self.image = image

    def transition(self, transitionImages, tokenImage):
        for i in range(30):
            self.image = transitionImages[i // 10]
            self.GAME.draw()
        self.image = tokenImage

    def draw(self, window):
        window.blit(self.image, (self.posX, self.posY))

# Iniciar o cliente
if __name__ == "__main__":
    # client = Othello()
    # client.start()
    game = Othello()
    game.start()  # Inicia a thread de recebimento de mensagens
    game.run()    
