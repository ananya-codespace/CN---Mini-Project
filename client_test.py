import socket
import time
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# -------- CONFIG --------

server_ip = input("Enter Server IP (Enter for localhost): ").strip()
if server_ip == "":
    server_ip = "127.0.0.1"

server_port = 5000

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

key = b'0123456789abcdef'
aesgcm = AESGCM(key)

received = set()
expected_seq = 1
buffer = {}

# -------- SECURITY --------

def encrypt(msg):
    nonce = os.urandom(12)
    return nonce + aesgcm.encrypt(nonce, msg.encode(), None)

def decrypt(data):
    nonce = data[:12]
    return aesgcm.decrypt(nonce, data[12:], None).decode()

# -------- JOIN --------

print("========================================")
client_socket.sendto(encrypt("JOIN"), (server_ip, server_port))
print("WELCOME USER 1")
print("User 1 connected to server")

# Slightly increased delay to ensure server registers client
time.sleep(2)

# Trigger sending
client_socket.sendto(encrypt("SEND"), (server_ip, server_port))

print("Waiting for messages...")
print("========================================\n")

# -------- DISPLAY --------

def display(t, s, m, status):
    print("----------------------------------------")
    
    if status == "RECEIVED":
        print("New Message")
    elif status == "DUPLICATE":
        print("Duplicate Message")
    elif status == "OUT-OF-ORDER":
        print("Out-of-Order Message")
    elif status == "BUFFERED":
        print("Buffered Message")
    
    print("----------------------------------------")
    
    print(f"Type      : {t}")
    print(f"Sequence  : {s}")
    print(f"Message   : {m}")
    print(f"Status    : {status}")
    
    print("----------------------------------------\n")

# -------- LOOP --------

while True:
    try:
        data, _ = client_socket.recvfrom(1024)
    except:
        continue

    try:
        message = decrypt(data)
        t, s, m = message.split("|")
        s = int(s)
    except:
        continue

    if s in received:
        display(t, s, m, "DUPLICATE")

    else:
        if s == expected_seq:
            display(t, s, m, "RECEIVED")
            received.add(s)
            expected_seq += 1

            while expected_seq in buffer:
                bt, bm = buffer.pop(expected_seq)
                display(bt, expected_seq, bm, "BUFFERED")
                received.add(expected_seq)
                expected_seq += 1

        else:
            buffer[s] = (t, m)
            display(t, s, m, "OUT-OF-ORDER")

    # ACK
    ack = f"ACK|{s}"
    client_socket.sendto(encrypt(ack), (server_ip, server_port))