import socket
import threading
import time
from dataclasses import dataclass

@dataclass
class Message:
    user: str
    text: str

    def serialize(self) -> bytes:
        return f"{self.user}#{self.text}".encode('utf-8')

    @staticmethod
    def deserialize(data: bytes) -> "Message":
        user, text = data.decode('utf-8').split("#")
        return Message(user, text)

    def fmt_string(self) -> str:
        return f"[{self.user}] {self.text}"


@dataclass
class ChatSession:
    user: str
    port: int

    def prompt_and_send_message(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as send_sock:
            send_sock.settimeout(0.2)
            send_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            send_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            while True:
                msg_text = input("> ")
                msg = Message(self.user, msg_text)
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
                    print(msg.fmt_string())
                time.sleep(0.2)

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
