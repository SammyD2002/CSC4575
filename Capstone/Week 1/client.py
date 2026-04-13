import socket
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

# PRE-SHARED KEY (Week 1 Only. We will transition to ECDH in Week 2)
PSK = b'THisIsASecretKeyThatIs32Bytes!!!'

#AES-256-GCM encryption.
# https://cryptography.io/en/latest/hazmat/primitives/symmetric-encryption/#cryptography.hazmat.primitives.ciphers.modes.GCM
def encrypt_payload(plaintext: bytes, key: bytes) -> tuple[bytes, bytes, bytes]:
    #1. Generate a secure 12-byte nonce using os.urandom().
    nonce = os.urandom(12)
    #2. Construct the Cipher object using algorithms.AES(key) and modes.GCM(nonce).
    sypher = Cipher(algorithms.AES(key), modes.GCM(nonce))
    #3. Create an encryptor object and encrypt the plaintext.
    incripter = sypher.encryptor()
    ciphertext = incripter.update(plaintext) + incripter.finalize()
    #4. Return the (nonce, ciphertext, tag).
    return nonce, ciphertext, incripter.tag

def start_client():
    # Docker automatically resolves container names to internal IPs
    host = 'bob_node' 
    port = 65432
    
    # The payload we want to protect from Wireshark
    message = b"CLASSIFIED: The Eagle flies at midnight."
    
    # --- Cryptographic Implementation goes here ---
    # TODO: Call encrypt_payload() with the message and PSK.
    nonce, ciphertext, tag = encrypt_payload(message, PSK)
    # Network Transmission
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((host, port))
            print(f"[*] Connected to Bob at {host}:{port}")
            # Format requirement: nonce (12 bytes) + tag (16 bytes) + ciphertext
            # Example: s.sendall(nonce + tag + ciphertext)          
            s.sendall(nonce + tag + ciphertext)
            print("[*] Encrypted payload sent over the wire.")
        except ConnectionRefusedError:
            print("[-] Connection refused. Is Bob's node running the server script?")

if __name__ == "__main__":
    start_client()
