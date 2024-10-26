import socket


def get_local_LAN_ip():
    LAN_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    LAN_socket.settimeout(0)
    try:
        # Attempt to connect to any IP address (it doesn't matter which)
        LAN_socket.connect(('10.254.254.254', 1))
        local_ip = LAN_socket.getsockname()[0]  # Returns the local IP
    except Exception:
        local_ip = '127.0.0.1'  # Fallback to localhost if it fails
    finally:
        LAN_socket.close()
    return local_ip