import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
#
#o sistema vai usar o PBKDF2 para derivar uma chave de cifra de 256 bits a partir de um código aleatório.
#

# 1. Definir a palavra-passe (neste caso, simula o vosso código aleatório)
codigo_aleatorio = b"meu_codigo_secreto_123"

# 2. Gerar um salt aleatório (deve ser guardado para derivar a mesma chave mais tarde)
salt = os.urandom(16)

# 3. Configurar o PBKDF2 para gerar uma chave de 256 bits (32 bytes)
kdf = PBKDF2HMAC(
    algorithm=hashes.SHA256(),
    length=32,
    salt=salt,
    iterations=390000, # Um número alto de iterações torna mais seguro
)

# 4. Derivar a chave
chave_derivada = kdf.derive(codigo_aleatorio)

print(f"Código Original: {codigo_aleatorio.decode()}")
print(f"Chave Derivada (Hex): {chave_derivada.hex()}")
print(f"Tamanho da Chave: {len(chave_derivada) * 8} bits")