import socket
import time
import random

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind(("0.0.0.0", 5000))

clients = set()
last_seen = {}   # client → last active time

seq = 1
ack_tracker = {}
message_buffer = {}

TIMEOUT = 3
CLIENT_TIMEOUT = 10   # remove inactive clients
LOSS_PROB = 0.2       # 20% packet loss simulation

print("[SERVER] Listening...")

# ---------------- CLEANUP DEAD CLIENTS ----------------
def remove_inactive_clients():
    current = time.time()
    for client in list(clients):
        if current - last_seen.get(client, 0) > CLIENT_TIMEOUT:
            clients.remove(client)
            print(f"[REMOVE] Inactive client {client}")

# ---------------- SEND WITH LOSS SIMULATION ----------------
def unreliable_send(msg, client):
    if random.random() > LOSS_PROB:
        server_socket.sendto(msg.encode(), client)
    else:
        print(f"[LOSS] Simulated loss to {client}")

while True:
    data, addr = server_socket.recvfrom(1024)
    message = data.decode()

    last_seen[addr] = time.time()  # update activity

    # ---------------- JOIN ----------------
    if message == "JOIN":
        clients.add(addr)
        print(f"[JOIN] {addr}")

    # ---------------- SEND ----------------
    elif message == "SEND":
        print(f"[SEND request from {addr}]")

        msg = f"{seq}|Hello clients!"
        ack_tracker[seq] = set()
        message_buffer[seq] = msg

        # send to all clients
        for client in clients:
            unreliable_send(msg, client)

        print(f"[SERVER] Sent seq {seq}")

        start_time = time.time()
        retransmissions = 0

        # -------- WAIT FOR ACKs --------
        while ack_tracker[seq] != clients:
            server_socket.settimeout(1)

            try:
                data_ack, addr_ack = server_socket.recvfrom(1024)
                ack_msg = data_ack.decode()

                if ack_msg.startswith("ACK"):
                    _, ack_seq = ack_msg.split("|")
                    ack_seq = int(ack_seq)

                    if ack_seq == seq:
                        if addr_ack not in ack_tracker[seq]:
                            ack_tracker[seq].add(addr_ack)
                            print(f"[ACK] {addr_ack}")

            except socket.timeout:
                pass

            # -------- TIMEOUT --------
            if time.time() - start_time > TIMEOUT:
                print("[TIMEOUT] Retransmitting...")

                for client in clients:
                    if client not in ack_tracker[seq]:
                        unreliable_send(message_buffer[seq], client)
                        retransmissions += 1

                start_time = time.time()

            # remove dead clients dynamically
            remove_inactive_clients()

        print(f"[SUCCESS] Seq {seq} delivered")
        print(f"[STATS] Retransmissions: {retransmissions}")

        seq += 1
        server_socket.settimeout(None)

    # ---------------- ACK ----------------
    elif message.startswith("ACK"):
        _, ack_seq = message.split("|")
        ack_seq = int(ack_seq)

        if ack_seq in ack_tracker:
            ack_tracker[ack_seq].add(addr)

        print(f"[ACK OUTSIDE] {addr}")

    else:
        print(f"[MSG] {addr}: {message}")