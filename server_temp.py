import socket
import time
import random
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM



server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind(("0.0.0.0", 5000))

clients = set()
last_seen = {}

seq = 1
ack_tracker = {}
message_buffer = {}

TIMEOUT = 3
CLIENT_TIMEOUT = 10
LOSS_PROB = 0.2



key = b'0123456789abcdef'
aesgcm = AESGCM(key)

def encrypt(msg):
    nonce = os.urandom(12)
    return nonce + aesgcm.encrypt(nonce, msg.encode(), None)

def decrypt(data):
    nonce = data[:12]
    return aesgcm.decrypt(nonce, data[12:], None).decode()

print("[SERVER] Listening...")



def remove_inactive_clients():
    current = time.time()
    for client in list(clients):
        if current - last_seen.get(client, 0) > CLIENT_TIMEOUT:
            clients.remove(client)
            print(f"[REMOVE] Inactive client {client}")



def unreliable_send(msg, client):
    if random.random() > LOSS_PROB:
        server_socket.sendto(encrypt(msg), client)   
    else:
        print(f"[LOSS] Simulated loss to {client}")



while True:
    data, addr = server_socket.recvfrom(1024)

    
    try:
        message = decrypt(data)
    except:
        print(f"[ERROR] Invalid packet from {addr}")
        continue

    last_seen[addr] = time.time()

   
    if message == "JOIN":
        clients.add(addr)
        print(f"[JOIN] {addr}")

    
    elif message == "SEND":
        print(f"[SEND request from {addr}]")

        msg = f"{seq}|Hello clients!"
        ack_tracker[seq] = set()
        message_buffer[seq] = msg

        for client in clients:
            unreliable_send(msg, client)

        print(f"[SERVER] Sent seq {seq}")

        start_time = time.time()
        retransmissions = 0

        
        while ack_tracker[seq] != clients:
            server_socket.settimeout(1)

            try:
                data_ack, addr_ack = server_socket.recvfrom(1024)

                
                try:
                    ack_msg = decrypt(data_ack)
                except:
                    continue

                if ack_msg.startswith("ACK"):
                    _, ack_seq = ack_msg.split("|")
                    ack_seq = int(ack_seq)

                    if ack_seq == seq:
                        if addr_ack not in ack_tracker[seq]:
                            ack_tracker[seq].add(addr_ack)
                            print(f"[ACK] {addr_ack}")

            except socket.timeout:
                pass

            
            if time.time() - start_time > TIMEOUT:
                print("[TIMEOUT] Retransmitting...")

                for client in clients:
                    if client not in ack_tracker[seq]:
                        unreliable_send(message_buffer[seq], client)
                        retransmissions += 1

                start_time = time.time()

            remove_inactive_clients()

        print(f"[SUCCESS] Seq {seq} delivered")
        print(f"[STATS] Retransmissions: {retransmissions}")

        seq += 1
        server_socket.settimeout(None)

    
    elif message.startswith("ACK"):
        _, ack_seq = message.split("|")
        ack_seq = int(ack_seq)

        if ack_seq in ack_tracker:
            ack_tracker[ack_seq].add(addr)

        print(f"[ACK OUTSIDE] {addr}")

    else:
        print(f"[MSG] {addr}: {message}")
