import pygame
from app.utils.logic_game import load_image, get_valid_directions, load_sprite_sheet
from app._class.Token import TokenBase, Token


class LogicGrid:
    def __init__(self, rows, columns):
        self.num_rows = rows
        self.num_columns = columns
        self.tokens = {}
        self.logic_grid = self.generate_grid(rows, columns)

    def generate_grid(self, rows, columns):
        """Generates an empty grid for logical operations."""
        grid = [[0 for _ in range(columns)] for _ in range(rows)]
        self.insert_token(grid, 1, 3, 3)
        self.insert_token(grid, -1, 3, 4)
        self.insert_token(grid, 1, 4, 4)
        self.insert_token(grid, -1, 4, 3)
        return grid

    def print_logic_board(self):
        """Prints the current logic board state."""
        print('  | A | B | C | D | E | F | G | H |')
        for i, row in enumerate(self.logic_grid):
            line = f'{i} |'.ljust(3, " ")
            for item in row:
                line += f"{item}".center(3, " ") + '|'
            print(line)
        print()

    def insert_token(self, grid, current_player, y, x):
        """Inserts a token into the grid at specified coordinates."""
        self.tokens[(y, x)] = TokenBase(current_player, y, x)
        grid[y][x] = self.tokens[(y, x)].player

    def find_available_moves(self, grid, turn):
        """Identifies playable cells based on valid adjacent cells."""
        valid_cells = self.find_valid_cells(grid, turn)
        playable_cells = []

        for cell in valid_cells:
            x, y = cell
            if cell in playable_cells:
                continue
            swappable_tiles = self.get_swappable_tiles(x, y, grid, turn)

            if swappable_tiles:
                playable_cells.append(cell)

        return playable_cells

    def find_valid_cells(self, grid, current_player):
        """Finds all empty cells adjacent to opposing player's tokens."""
        valid_cells_to_click = []
        for grid_x, row in enumerate(grid):
            for grid_y, col in enumerate(row):
                if grid[grid_x][grid_y] != 0:
                    continue
                directions = get_valid_directions(grid_x, grid_y)

                for direction in directions:
                    dir_x, dir_y = direction
                    checked_cell = grid[dir_x][dir_y]

                    if checked_cell == 0 or checked_cell == current_player:
                        continue

                    if (grid_x, grid_y) in valid_cells_to_click:
                        continue

                    valid_cells_to_click.append((grid_x, grid_y))
        return valid_cells_to_click

    def get_swappable_tiles(self, x, y, grid, player):
        """Finds tiles that can be swapped for the current player."""
        surrounding_cells = get_valid_directions(x, y)
        if not surrounding_cells:
            return []

        swappable_tiles = []
        for check_cell in surrounding_cells:
            check_x, check_y = check_cell
            delta_x, delta_y = check_x - x, check_y - y
            current_line = []

            while True:
                if grid[check_x][check_y] == -player:  # Opponent's token
                    current_line.append((check_x, check_y))
                elif grid[check_x][check_y] == player:
                    break
                elif grid[check_x][check_y] == 0:
                    current_line.clear()
                    break

                check_x += delta_x
                check_y += delta_y

                if check_x < 0 or check_x >= self.num_columns or check_y < 0 or check_y >= self.num_rows:
                    current_line.clear()
                    break

            if current_line:
                swappable_tiles.extend(current_line)

        return swappable_tiles


class DrawableGrid():
    def __init__(self, rows, columns, size, main):
        self.game = main
        self.num_rows = rows
        self.num_columns = columns
        self.cell_size = size
        self.white_token_image = load_image('app/assets/WhiteToken.png', size)
        self.black_token_image = load_image('app/assets/BlackToken.png', size)
        self.transition_white_to_black = [load_image(f'app/assets/BlackToWhite{i}.png', self.cell_size) for i in range(1, 4)]
        self.transition_black_to_white = [load_image(f'app/assets/WhiteToBlack{i}.png', self.cell_size) for i in range(1, 4)]
        self.background_images = self.load_background_images()

        self.tokens = {}
        self.background_image = self.create_background_image()

        self.logic_grid = self.generate_grid(rows, columns)


    def generate_grid(self, rows, columns):
        """Generates an empty grid for logical operations."""
        grid = [[0 for _ in range(columns)] for _ in range(rows)]
        self.insert_token(grid, 1, 3, 3)
        self.insert_token(grid, -1, 3, 4)
        self.insert_token(grid, 1, 4, 4)
        self.insert_token(grid, -1, 4, 3)
        return grid

    def print_logic_board(self):
        """Prints the current logic board state."""
        print('  | A | B | C | D | E | F | G | H |')
        for i, row in enumerate(self.logic_grid):
            line = f'{i} |'.ljust(3, " ")
            for item in row:
                line += f"{item}".center(3, " ") + '|'
            print(line)
        print()

    def insert_token(self, grid, current_player, y, x):
        """Inserts a token into the grid at specified coordinates."""
        token_image = self.white_token_image if current_player == 1 else self.black_token_image
        self.tokens[(y, x)] = Token(current_player, y, x, token_image, self.game)
        grid[y][x] = self.tokens[(y, x)].player

    def find_available_moves(self, grid, turn):
        """Identifies playable cells based on valid adjacent cells."""
        valid_cells = self.find_valid_cells(grid, turn)
        playable_cells = []

        for cell in valid_cells:
            x, y = cell
            if cell in playable_cells:
                continue
            swappable_tiles = self.get_swappable_tiles(x, y, grid, turn)

            if swappable_tiles:
                playable_cells.append(cell)

        return playable_cells

    def find_valid_cells(self, grid, current_player):
        """Finds all empty cells adjacent to opposing player's tokens."""
        valid_cells_to_click = []
        for grid_x, row in enumerate(grid):
            for grid_y, col in enumerate(row):
                if grid[grid_x][grid_y] != 0:
                    continue
                directions = get_valid_directions(grid_x, grid_y)

                for direction in directions:
                    dir_x, dir_y = direction
                    checked_cell = grid[dir_x][dir_y]

                    if checked_cell == 0 or checked_cell == current_player:
                        continue

                    if (grid_x, grid_y) in valid_cells_to_click:
                        continue

                    valid_cells_to_click.append((grid_x, grid_y))
        return valid_cells_to_click

    def get_swappable_tiles(self, x, y, grid, player):
        """Finds tiles that can be swapped for the current player."""
        surrounding_cells = get_valid_directions(x, y)
        if not surrounding_cells:
            return []

        swappable_tiles = []
        for check_cell in surrounding_cells:
            check_x, check_y = check_cell
            delta_x, delta_y = check_x - x, check_y - y
            current_line = []

            while True:
                if grid[check_x][check_y] == -player:  # Opponent's token
                    current_line.append((check_x, check_y))
                elif grid[check_x][check_y] == player:
                    break
                elif grid[check_x][check_y] == 0:
                    current_line.clear()
                    break

                check_x += delta_x
                check_y += delta_y

                if check_x < 0 or check_x >= self.num_columns or check_y < 0 or check_y >= self.num_rows:
                    current_line.clear()
                    break

            if current_line:
                swappable_tiles.extend(current_line)

        return swappable_tiles

    def load_background_images(self):
        """Loads and returns background images for the grid."""
        alpha = 'ABCDEFGHI'
        sprite_sheet = pygame.image.load('app/assets/image.png').convert_alpha()
        image_dict = {}
        for i in range(3):
            for j in range(7):
                image_dict[alpha[j] + str(i)] = load_sprite_sheet(sprite_sheet, j, i, (self.cell_size), (32, 32))
        return image_dict

    def create_background_image(self):
        """Creates the background image for the grid."""
        grid_bg = [
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
        for j, row in enumerate(grid_bg):
            for i, img in enumerate(row):
                image.blit(self.background_images[img], (i * self.cell_size[0], j * self.cell_size[1]))
        return image

    def draw_grid(self, window):
        """Draws the grid and tokens on the given window."""
        window.blit(self.background_image, (0, 0))

        for token in self.tokens.values():
            token.draw(window)

        available_moves = self.find_available_moves(self.logic_grid, self.game.turn)
        if self.game.turn == self.game.current_player:
            for move in available_moves:
                pygame.draw.rect(window, (240, 240, 240) if self.game.current_player == 1 else (50, 50, 50),
                                 (80 + (move[1] * 80) + 30, 80 + (move[0] * 80) + 30, 20, 20))

    def animate_transitions(self, cell, player):
        """Animates the transition of tokens from one color to another."""
        if player == 1:
            self.tokens[(cell[0], cell[1])].animate_transition(self.transition_white_to_black, self.white_token_image)
        else:
            self.tokens[(cell[0], cell[1])].animate_transition(self.transition_black_to_white, self.black_token_image)
