import socket
import threading
import time
from dataclasses import dataclass, field

@dataclass
class Message:
    """
    Message struct.
    """
    user: str
    text: str
    dedupe_id: str = None

    def __post_init__(self):
        self.dedupe_id = self.dedupe_id or str(time.time())

    def serialize(self) -> bytes:
        return f"{self.user}%%{self.text}%%{self.dedupe_id}".encode('utf-8')

    @staticmethod
    def deserialize(data: bytes) -> "Message":
        user, text, dedupe_id = data.decode('utf-8').split("%%")
        return Message(user, text, dedupe_id)

    def fmt_string(self) -> str:
        return f"[{self.user}] {self.text}"


class RingBuf:
    """
    Simple ring-buffer.
    """

    def __init__(self, size=100):
        self._buffer = [None] * size
        self._curr_pos = 0
        self.size = size
    
    def add(self, value):
        if self._curr_pos >= self.size:
            self._curr_pos = 0
        self._buffer[self._curr_pos] = value
        self._curr_pos += 1

    def __contains__(self, value):
        return value in self._buffer


@dataclass
class ChatSession:
    """
    A user chat session.
    """
    user: str
    port: int
    delivery_attempts: int = 5
    seen: set = field(default_factory=RingBuf)


    def prompt_and_send_message(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as send_sock:
            send_sock.settimeout(0.2)
            send_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            send_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            while True:
                msg_text = input("> ")
                msg = Message(self.user, msg_text)
                for _ in range(self.delivery_attempts):
                    send_sock.sendto(msg.serialize(), ("<broadcast>", self.port))
                time.sleep(0.2)

    def listen(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as recv_sock:
            recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            recv_sock.bind(("", self.port))
            while True:
                data, addr = recv_sock.recvfrom(1024)
                if data:
                    msg = Message.deserialize(data)
                    if msg.dedupe_id not in self.seen:
                        print(msg.fmt_string())
                        self.seen.add(msg.dedupe_id)
                time.sleep(0.01)

    def start(self):
        listening_thread = threading.Thread(target=self.listen)
        prompting_thread = threading.Thread(target=self.prompt_and_send_message)
        print(f"Welcome, {user_name}. You are now connected to {port}!")
        listening_thread.start()
        prompting_thread.start()
    

if __name__ == "__main__":
    user_name = input("Please input a user name: ")
    port = int(input("What port would you like to connect to?: "))
    session = ChatSession(user_name, port)
    session.start()
