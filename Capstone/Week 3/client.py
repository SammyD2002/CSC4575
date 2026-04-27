import socket
import os
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

def load_keys():
	"""Loads Alice's private identity key and Bob's public identity key."""
	with open("alice_private.pem", "rb") as f:
		alice_priv = serialization.load_pem_private_key(f.read(), password=None)
	with open("bob_public.pem", "rb") as f:
		bob_pub = serialization.load_pem_public_key(f.read())
	return alice_priv, bob_pub

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

# Week 2 AES Key derivation
def derive_aes_key(shared_secret: bytes) -> bytes:
	"""
	TODO: Implement HKDF to derive a 32-byte AES key.
	Must match the Server's HKDF parameters exactly.
	"""
	return HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b'handshake data').derive(shared_secret)



def start_client():
	host, port = 'bob_node', 65432
	message = b"CLASSIFIED: The Eagle flies at midnight."
	alice_identity_priv, bob_identity_pub = load_keys()
	
	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
		try:
			s.connect((host, port))
			print(f"[*] Connected to Bob at {host}:{port}")
			
			# --- PHASE 1: AUTHENTICATED ECDH HANDSHAKE ---
			# TODO: 1. Generate Alice's ephemeral X25519PrivateKey
			akey = x25519.X25519PrivateKey.generate()			
			# TODO: 2. Extract Alice's X25519 public bytes
			apub = akey.public_key()
			apbytes = apub.public_bytes_raw()
			# TODO: 3. Use alice_identity_priv to SIGN the X25519 public bytes using padding.PSS and hashes.SHA256()
			asig = alice_identity_priv.sign(apbytes, padding.PSS(
					mgf=padding.MGF1(hashes.SHA256()),
					salt_length=padding.PSS.MAX_LENGTH
				),
				hashes.SHA256()
			)
			# TODO: 4. Send Alice's signature (256 bytes) and Alice's X25519 public key (32 bytes) to Bob.
			s.sendall(asig + apbytes)
			# TODO: 5. Receive Bob's data (Format: 256-byte signature + 32-byte X25519 public key)
			bsig = s.recv(256)
			bpbytes = s.recv(32)
			# TODO: 6. Use bob_identity_pub to VERIFY Bob's signature against his X25519 public bytes.
			bob_identity_pub.verify(
				bsig, bpbytes,
				padding.PSS(
					mgf=padding.MGF1(hashes.SHA256()),
					salt_length=padding.PSS.MAX_LENGTH
				),
				hashes.SHA256()
			)
			# Signature is known valid here, so reconstruct.
			bpub = x25519.X25519PublicKey.from_public_bytes(bpbytes)
			# TODO: 7. Compute the shared_secret using the verified X25519 points.
			skbytes = akey.exchange(bpub)
			# --- PHASE 2: KEY DERIVATION ---
			# TODO: Derive the AES key using HKDF (Same as Week 2)
			aes = derive_aes_key(skbytes)
			# --- PHASE 3: SECURE PAYLOAD ---
			# TODO: Encrypt and send the AES-GCM payload (Same as Week 1 & 2)
			nonce, ciphertext, tag = encrypt_payload(message, aes)
			# TODO: Send the nonce, tag, and ciphertext to Bob.
			s.sendall(nonce + tag + ciphertext)
			print("[*] Handshake complete. Encrypted payload sent.")			

		except ConnectionRefusedError:
			print("[-] Connection refused. Is Bob's server running?")

if __name__ == "__main__":
	start_client()
