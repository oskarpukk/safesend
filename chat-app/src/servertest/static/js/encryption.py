################################################
# Programmeerimine I
# 2024/2025 sügissemester
#
# Projekt
# Teema: Krüpteerimine
#
# Autorid:
# Oskar Pukk
# Richard Mihhels
#
# Lisakommentaar: Krüpteerimise teostamine Pythonis
##################################################

import random

class DiffieHellmanAlg:
    def __init__(self, P=23, G=9):
        """Initsialiseerib Diffie-Hellmani parameetrid"""
        self.P = 23  # Algarvuline moodul
        self.G = 9   # Generaator
        
    def generate_private_key(self):
        """Genereerib juhusliku privaatvõtme vahemikus 1 kuni P-1"""
        return random.randint(1, self.P-1)
    
    def generate_public_key(self, private_key):
        """Genereerib avaliku võtme kasutades G^private_key mod P"""
        return pow(self.G, private_key, self.P)
    
    def generate_shared_secret(self, private_key, other_public_key):
        """Genereerib jagatud saladuse teise osapoole avaliku võtme abil"""
        return pow(other_public_key, private_key, self.P)

class MessageEncryption:
    def __init__(self, shared_secret):
        """Initsialiseerib krüpteerimise jagatud saladusega"""
        self.shared_secret = shared_secret
        self.pool = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 !@#$%^&*()_+-=[]{}|;:,.<>?"

    def encrypt(self, message):
        """Krüpteerib sõnumi kasutades nihkešifrit"""
        shift = self.shared_secret % len(self.pool)
        result = ""
        for char in message:
            if char in self.pool:
                current_pos = self.pool.index(char)
                new_pos = (current_pos + shift) % len(self.pool)
                result += self.pool[new_pos]
            else:
                result += char
        return result

    def decrypt(self, message):
        """Dekrüpteerib sõnumi kasutades nihkešifrit"""
        shift = self.shared_secret % len(self.pool)
        result = ""
        for char in message:
            if char in self.pool:
                current_pos = self.pool.index(char)
                new_pos = (current_pos - shift) % len(self.pool)
                result += self.pool[new_pos]
            else:
                result += char
        return result

    def test_encryption(self, message):
        encrypted = self.encrypt(message)
        decrypted = self.decrypt(encrypted)
        return {
            'original': message,
            'encrypted': encrypted,
            'decrypted': decrypted
        }