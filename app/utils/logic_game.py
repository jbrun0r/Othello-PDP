import pygame

# Utility functions
def get_valid_directions(current_x, current_y, min_x=0, min_y=0, max_x=7, max_y=7):
    """
    Determine the valid movement directions from the current cell.

    Args:
        current_x (int): The current x-coordinate of the cell.
        current_y (int): The current y-coordinate of the cell.
        min_x (int, optional): The minimum x-coordinate boundary. Default is 0.
        min_y (int, optional): The minimum y-coordinate boundary. Default is 0.
        max_x (int, optional): The maximum x-coordinate boundary. Default is 7.
        max_y (int, optional): The maximum y-coordinate boundary. Default is 7.

    Returns:
        list of tuple: A list of valid (x, y) coordinates representing valid directions.
    """
    valid_directions = []
    
    # Check adjacent directions
    if current_x > min_x:
        valid_directions.append((current_x - 1, current_y))  # left
        if current_y > min_y:
            valid_directions.append((current_x - 1, current_y - 1))  # upper-left diagonal
        if current_y < max_y:
            valid_directions.append((current_x - 1, current_y + 1))  # lower-left diagonal
            
    if current_x < max_x:
        valid_directions.append((current_x + 1, current_y))  # right
        if current_y > min_y:
            valid_directions.append((current_x + 1, current_y - 1))  # upper-right diagonal
        if current_y < max_y:
            valid_directions.append((current_x + 1, current_y + 1))  # lower-right diagonal
            
    if current_y > min_y:
        valid_directions.append((current_x, current_y - 1))  # up
    if current_y < max_y:
        valid_directions.append((current_x, current_y + 1))  # down

    return valid_directions

def load_image(image_path, size):
    """
    Load an image from the specified path and scale it to the given size.

    Args:
        image_path (str): The file path to the image.
        size (tuple): The desired size to scale the image (width, height).

    Returns:
        Surface: A Pygame surface containing the scaled image.
    """
    image = pygame.image.load(image_path).convert_alpha()
    resized_image = pygame.transform.scale(image, size)
    return resized_image

def load_sprite_sheet(sprite_sheet, row, column, new_size, sprite_size):
    """
    Extract a specific sprite from a sprite sheet and scale it to the desired size.

    Args:
        sprite_sheet (Surface): The sprite sheet surface containing all sprites.
        row (int): The row index of the sprite in the sprite sheet.
        column (int): The column index of the sprite in the sprite sheet.
        new_size (tuple): The desired size to scale the extracted sprite (width, height).
        sprite_size (tuple): The size of each individual sprite in the sprite sheet (width, height).

    Returns:
        Surface: A Pygame surface containing the scaled sprite image.
    """
    surface = pygame.Surface((32, 32)).convert_alpha()
    surface.blit(sprite_sheet, (0, 0), (row * sprite_size[0], column * sprite_size[1], sprite_size[0], sprite_size[1]))
    scaled_image = pygame.transform.scale(surface, new_size)
    scaled_image.set_colorkey('Black')  # Set black as transparent
    return scaled_image
