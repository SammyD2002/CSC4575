import socket
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.exceptions import InvalidTag, InvalidSignature

def load_keys():
	"""Loads Bob's private identity key and Alice's public identity key."""
	with open("bob_private.pem", "rb") as f:
		bob_priv = serialization.load_pem_private_key(f.read(), password=None)
	with open("alice_public.pem", "rb") as f:
		alice_pub = serialization.load_pem_public_key(f.read())
	return bob_priv, alice_pub

#Week 1 AES-256-GCM decryption.
def decrypt_payload(nonce: bytes, ciphertext: bytes, tag: bytes, key: bytes) -> bytes:
	#1. Construct the Cipher object using algorithms.AES(key) and modes.GCM(nonce, tag).
	sypher = Cipher(algorithms.AES(key), modes.GCM(nonce, tag))
	#2. Create a decryptor object.
	deekripter = sypher.decryptor()
	#3. Decrypt the ciphertext and return the plaintext.
	return deekripter.update(ciphertext) + deekripter.finalize()

# Week 2 Key Derivation
def derive_aes_key(shared_secret: bytes) -> bytes:
	"""
	TODO: Implement HKDF to derive a 32-byte AES key.
	Use SHA256 as the algorithm, length=32, salt=None, info=b'handshake data'.
	"""
	return HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b'handshake data').derive(shared_secret)


def start_server():
	host, port = '0.0.0.0', 65432
	bob_identity_priv, alice_identity_pub = load_keys()
	
	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
		s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		s.bind((host, port))
		s.listen()
		print(f"[*] Bob (Server) listening on {host}:{port}...")
		
		conn, addr = s.accept()
		with conn:
			# --- PHASE 1: AUTHENTICATED ECDH HANDSHAKE ---
			# TODO: 1. Generate Bob's ephemeral X25519PrivateKey
			bkey = x25519.X25519PrivateKey.generate()			
			# TODO: 2. Extract Bob's X25519 public bytes
			bpbytes = bkey.public_key().public_bytes_raw()
			# TODO: 3. Use bob_identity_priv to SIGN the X25519 public bytes using padding.PSS and hashes.SHA256()
			bsig = bob_identity_priv.sign(bpbytes, padding.PSS(
				mgf=padding.MGF1(hashes.SHA256()),
				salt_length=padding.PSS.MAX_LENGTH
			),
			hashes.SHA256()
			)
			# TODO: 4. Receive Alice's data (Format: 256-byte signature + 32-byte X25519 public key)
			asig = conn.recv(256)
			apbytes = conn.recv(32)
			# TODO: 5. Use alice_identity_pub to VERIFY Alice's signature against her X25519 public bytes.
			#		  (If verification fails, cryptography will raise an InvalidSignature exception. Let it crash the connection.)
			alice_identity_pub.verify(
				asig, apbytes,
				padding.PSS(
					mgf=padding.MGF1(hashes.SHA256()),
					salt_length=padding.PSS.MAX_LENGTH
				),
				hashes.SHA256()
			)
			apub = x25519.X25519PublicKey.from_public_bytes(apbytes)
			# TODO: 6. Send Bob's signature and Bob's X25519 public bytes to Alice.
			conn.sendall(bsig + bpbytes)
			# TODO: 7. Compute the shared_secret using the verified X25519 points.
			skbytes = bkey.exchange(apub)
			# --- PHASE 2: KEY DERIVATION ---
			# TODO: Derive the AES key using HKDF (Same as Week 2)
			aes = derive_aes_key(skbytes)
			# --- PHASE 3: RECEIVE PAYLOAD ---
			# TODO: Receive and decrypt the AES-GCM payload (Same as Week 1 & 2)
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
	start_server()
