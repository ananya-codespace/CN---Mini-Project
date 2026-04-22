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

time.sleep(2)   # important for sync

client_socket.sendto(encrypt("SEND"), (server_ip, server_port))

print("Waiting for messages...")
print("========================================\n")

# -------- DISPLAY --------

def display(t, s, m, status):
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
        print("[DEBUG] Packet received")   # 🔥 IMPORTANT DEBUG
    except:
        continue

    # -------- DECRYPT --------
    try:
        message = decrypt(data)
        print("[DEBUG] Decrypted:", message)   # 🔥 DEBUG
    except Exception as e:
        print("[ERROR] Decryption failed:", e)
        continue

    # -------- PARSE --------
    try:
        seq, msg = message.split("|")
        seq = int(seq)
        t = "NOTIFICATION"   # since server sends only seq|msg
    except Exception as e:
        print("[ERROR] Parse failed:", e)
        continue

    # -------- DUPLICATE --------
    if seq in received:
        display(t, seq, msg, "DUPLICATE")

    else:
        if seq == expected_seq:
            display(t, seq, msg, "RECEIVED")
            received.add(seq)
            expected_seq += 1

            while expected_seq in buffer:
                bm = buffer.pop(expected_seq)
                display(t, expected_seq, bm, "BUFFERED")
                received.add(expected_seq)
                expected_seq += 1

        else:
            buffer[seq] = msg
            display(t, seq, msg, "OUT-OF-ORDER")

    # -------- ACK --------
    ack = f"ACK|{seq}"
    client_socket.sendto(encrypt(ack), (server_ip, server_port))
    print(f"[ACK SENT] {seq}\n")