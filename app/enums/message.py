from enum import Enum


class MessageType(Enum):
    UPDATE = "update"
    MOVE = "move"
    GAME_OVER = "game_over"
    ERROR = "error"
    CHAT = "chat"
    SETUP = "setup"