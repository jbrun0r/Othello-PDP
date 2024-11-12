from enum import Enum


class MessageType(Enum):
    UPDATE = "update"
    MOVE = "move"
    GAME_OVER = "game_over"
    ERROR = "error"
    CHAT = "chat"
    SETUP = "setup"
    GIVE_UP = "give_up"
    RESTART = "restart"
    RIVAL_CONNECTED = "rival_connected"

class PlayerStatusType(Enum):
    GAVE_UP = "GAVE UP"
    DISCONNECTED = "DISCONNECTED"
    CONNECTED = "CONNECTED"
