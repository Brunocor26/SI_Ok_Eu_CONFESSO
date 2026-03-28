import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
#
#O enunciado pede que o corpo do e-mail seja cifrado com AES-256-CTR.
#

# 1. Gerar uma chave de 256 bits (32 bytes) e um Nonce (16 bytes)
chave = os.urandom(32)
nonce = os.urandom(16) # No modo CTR usamos um Nonce em vez de um IV tradicional

texto_limpo = b"Esta e a mensagem secreta do e-mail."

# 2. Configurar a cifra e cifrar
cipher = Cipher(algorithms.AES(chave), modes.CTR(nonce))
encryptor = cipher.encryptor()
criptograma = encryptor.update(texto_limpo) + encryptor.finalize()

# 3. Configurar a decifra (precisa da mesma chave e do mesmo nonce)
decryptor = cipher.decryptor()
texto_decifrado = decryptor.update(criptograma) + decryptor.finalize()

print("--- AES-256-CTR ---")
print(f"Original:   {texto_limpo}")
print(f"Cifrado:    {criptograma}")
print(f"Decifrado:  {texto_decifrado}")