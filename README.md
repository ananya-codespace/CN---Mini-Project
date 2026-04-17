***PROBLEM STATEMENT***



This project shows a reliable group notification system using UDP sockets.

UDP does not guarantee packets to be delivered correctly, so we are designing a protocol that "creates" reliability by using sequence numbers and ACKs. We will be transferring broadcast messages to multiple clients at the same time.







***WHAT IS REQUIRED?***



1\. Proper TCP/UDP Communication

2\. Concurrency with multiple clients (2 in our case)

3\. Protocol Design (the format of our packet)

4\. Using SSL and TLS for security

5\. Reliability over UDP (ACKs and retransmission)

6\. Performance evaluation





***SYSTEM ARCHITECTURE (what will the system, as a whole, look like?)***



There is one central server which will be listening for incoming UDP messages from clients. Clients will join the system and receive broadcast messages. The server looks for clients who are active and sends notifications to all of them.





***PROTOCOL DESIGN*** 



***(a) How and what will our packets look like?***



DATA: seq|message

ACK:  ACK|seq



***(b) Messages and their types***



JOIN: Client has registered with the server

SEND: Server can start broadcasting

`seq: message`

`ACK: seq`



***(c) How an example simulation will look like (flow)***



Client → Server: JOIN

Client → Server: SEND



Server → All Clients: 1|Hello clients!



Client → Server: ACK|1





***RELIABILITY MECHANISM (what makes our program reliable?)***



Each message is assigned a unique sequence number, and server maintains a record of what ACKs have been received. After they receive a packet, clients send an ACK.


