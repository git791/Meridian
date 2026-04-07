import socket

def run_sink():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('127.0.0.1', 1025))
        s.listen()
        print("Raw SMTP Sink Listening on 1025...")
        while True:
            conn, addr = s.accept()
            with conn:
                conn.sendall(b"220 localhost SMTP Ready\r\n")
                while True:
                    data = conn.recv(4096)
                    if not data: break
                    with open("raw_smtp.log", "a", encoding="utf-8") as f:
                        f.write(f"{data.decode(errors='ignore')}\n")
                    
                    if data.startswith(b"HELO") or data.startswith(b"EHLO"):
                        conn.sendall(b"250 localhost\r\n")
                    elif data.startswith(b"MAIL") or data.startswith(b"RCPT"):
                        conn.sendall(b"250 OK\r\n")
                    elif data.startswith(b"DATA"):
                        conn.sendall(b"354 Start\r\n")
                    elif data.strip() == b".":
                        conn.sendall(b"250 OK\r\n")
                    elif data.startswith(b"QUIT"):
                        conn.sendall(b"221 Bye\r\n")
                        break
                    else:
                        conn.sendall(b"250 OK\r\n")

if __name__ == "__main__":
    run_sink()
