import socket
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.exceptions import InvalidTag
from sys import stderr
#Week 1 AES-256-GCM decryption.
def decrypt_payload(nonce: bytes, ciphertext: bytes, tag: bytes, key: bytes) -> bytes:
    #1. Construct the Cipher object using algorithms.AES(key) and modes.GCM(nonce, tag).
    sypher = Cipher(algorithms.AES(key), modes.GCM(nonce, tag))
    #2. Create a decryptor object.
    deekripter = sypher.decryptor()
    #3. Decrypt the ciphertext and return the plaintext.
    return deekripter.update(ciphertext) + deekripter.finalize()

def derive_aes_key(shared_secret: bytes) -> bytes:
    """
    TODO: Implement HKDF to derive a 32-byte AES key.
    Use SHA256 as the algorithm, length=32, salt=None, info=b'handshake data'.
    """
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b'handshake data').derive(shared_secret)

def start_server():
    host, port = '0.0.0.0', 65432
    #print(f'[*] Preparing to listen on {host}:{port}')    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # Allow immediate reuse of the port to prevent "Address already in use" errors
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        s.listen()
        print(f"[*] Bob (Server) listening on {host}:{port}...")        
        conn, addr = s.accept()
        with conn:
            print(f"[*] Connection established from {addr}")
            # --- PHASE 1: ECDH HANDSHAKE ---
            # TODO: 1. Generate Bob's X25519PrivateKey
            bkey = x25519.X25519PrivateKey.generate()
            # TODO: 2. Receive Alice's 32-byte public key over 'conn'
            apbytes = conn.recv(32)
            # TODO: 3. Reconstruct Alice's public key object from the raw bytes
            apub = x25519.X25519PublicKey.from_public_bytes(apbytes)
            # TODO: 4. Send Bob's public key (raw bytes) to Alice over 'conn'
            bpbytes = bkey.public_key().public_bytes_raw()
            conn.sendall(bpbytes)
            # TODO: 5. Compute the shared_secret using bob_private_key.exchange()
            skbytes = bkey.exchange(apub)
            # --- PHASE 2: KEY DERIVATION ---
            # TODO: Derive the AES key by calling derive_aes_key(shared_secret)
            aes = derive_aes_key(skbytes)
            # --- PHASE 3: RECEIVE PAYLOAD ---
            data = conn.recv(4096)
            if not data: print("[-] No data recieved.")
            elif len(data) < 28: print("[-] Recieved data malformed (Too short to contain nonce and tag).")
            else:
                # TODO: Extract nonce, tag, and ciphertext.
                nonce, tag, ciphertext = data[:12], data[12:28], data[28:]                
                # TODO: Call your Week 1 decrypt_payload() using the NEW derived key.
                try:
                    # TODO: Call decrypt_payload()
                    plaintext = decrypt_payload(nonce, ciphertext, tag, aes)
                    # TODO: Print the decoded plaintext to the console. Handle InvalidTag exceptions gracefully.
                    print("[*] Payload decrypted successfully.")
                    print(f"[*] Recieved Data: {plaintext}")
                except InvalidTag:
                    print("[-] Recieved data malformed (Invalid GCM Tag).")

if __name__ == "__main__":
    try:
        start_server()
    except OSError as e:
        print(e.strerror, file=stderr)
        exit(e.errno)
