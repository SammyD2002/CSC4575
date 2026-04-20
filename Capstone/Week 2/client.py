import socket
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from sys import stderr
# Week 1 AES-256-GCM encryption.
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

def derive_aes_key(shared_secret: bytes) -> bytes:
    """
    TODO: Implement HKDF to derive a 32-byte AES key.
    Must match the Server's HKDF parameters exactly.
    """
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b'handshake data').derive(shared_secret)

def start_client():
    # Docker automatically resolves container names to internal IPs
    host, port = 'bob_node', 65432
    #host = '127.0.0.1' # Manual debug
    message = b"CLASSIFIED: The Eagle flies at midnight."    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        print(f'[*] Socket initialized, connecting to {host}:{port}')
        try:
            s.connect((host, port))
            #print(f"[*] Connected to Bob at {host}:{port}")
            # --- PHASE 1: ECDH HANDSHAKE ---
            # 1. Generate Alice's X25519PrivateKey
            akey = x25519.X25519PrivateKey.generate()
            # 2. Send Alice's public key (raw bytes) to Bob over 's'
            apub = akey.public_key()
            apbytes = apub.public_bytes_raw()
            s.sendall(apbytes)
            # 3. Receive Bob's 32-byte public key over 's'
            bpbytes = s.recv(32)
            # 4. Reconstruct Bob's public key object from the raw bytes
            bpub = x25519.X25519PublicKey.from_public_bytes(bpbytes)
            # 5. Compute the shared_secret using alice_private_key.exchange()
            skbytes = akey.exchange(bpub)
            # --- PHASE 2: KEY DERIVATION ---
            # Derive the AES key by calling derive_aes_key(shared_secret)
            aes = derive_aes_key(skbytes)
            # --- PHASE 3: SECURE PAYLOAD ---
            # Call your Week 1 encrypt_payload() using the NEW derived key.
            nonce, ciphertext, tag = encrypt_payload(message, aes)
            # TODO: Send the nonce, tag, and ciphertext to Bob.
            s.sendall(nonce + tag + ciphertext)
            print("[*] Handshake complete. Encrypted payload sent.")
            
        except ConnectionRefusedError:
            print("[-] Connection refused. Is Bob's server running?")
        except OSError as e:
            print (e.strerror, file=stderr)
            exit(e.errno)

if __name__ == "__main__":
    start_client()
