class TokenBase:
    def __init__(self, player, grid_x, grid_y):
        self.player = player
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.pos_x = 80 + (grid_y * 80)
        self.pos_y = 80 + (grid_x * 80)

class Token(TokenBase):
    def __init__(self, player, grid_x, grid_y, image, game):
        super().__init__(player, grid_x, grid_y)
        self.image = image
        self.game = game

    def animate_transition(self, transition_images, final_image):
        for i in range(30):
            self.image = transition_images[i // 10]
            self.game.draw()
        self.image = final_image

    def draw(self, window):
        window.blit(self.image, (self.pos_x, self.pos_y))
