################################################
# Programmeerimine I
# 2024/2025 sügissemester
#
# Projekt: SafeSend - Turvaline sõnumivahetus
# Teema: Krüpteeritud vestlusrakendus
#
# Autorid:
# Richard Mihhels
# Oskar Pukk
#
# Eeskuju: Signal sõnumirakenduse Double Ratchet meetod
#
# Käivitusjuhend:
# 1. Installige vajalikud paketid: pip install -r requirements.txt
# 2. Käivitage server: python server.py
################################################

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def generate_keypair():
    """Genereerib uue võtmepaari"""
    private_key = x25519.X25519PrivateKey.generate()
    public_key = private_key.public_key()
    return private_key, public_key


def derive_shared_secret(private_key, peer_public_key):
    """Tuletab jagatud saladuse kahe osapoole vahel"""
    shared_key = private_key.exchange(peer_public_key)
    return shared_key


def encrypt_message(message, shared_secret):
    """Krüpteerib sõnumi kasutades jagatud saladust"""
    derived_key = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b'handshake data'
    ).derive(shared_secret)
    
    aesgcm = AESGCM(derived_key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, message.encode(), None)
    return nonce + ciphertext


def decrypt_message(encrypted_message, shared_secret):
    """Dekrüpteerib sõnumi kasutades jagatud saladust"""
    nonce = encrypted_message[:12]
    ciphertext = encrypted_message[12:]
    
    derived_key = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b'handshake data'
    ).derive(shared_secret)
    
    aesgcm = AESGCM(derived_key)
    return aesgcm.decrypt(nonce, ciphertext, None).decode()