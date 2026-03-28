import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
#
#A chave privada gerada no registo deve ser guardada de forma segura, cifrada com AES-256-CBC.
#O modo CBC exige que o tamanho do texto seja múltiplo do tamanho do bloco (16 bytes), por isso
# precisamos de usar padding.
#
chave = os.urandom(32) # Chave de 256 bits
iv = os.urandom(16)    # Initialization Vector (obrigatório no CBC)

# Simular a chave privada em formato de texto
chave_privada_simulada = b"---BEGIN PRIVATE KEY---...---END PRIVATE KEY---"

# 1. Adicionar Padding (Preenchimento)
padder = padding.PKCS7(algorithms.AES.block_size).padder()
dados_com_padding = padder.update(chave_privada_simulada) + padder.finalize()

# 2. Cifrar
cipher = Cipher(algorithms.AES(chave), modes.CBC(iv))
encryptor = cipher.encryptor()
criptograma = encryptor.update(dados_com_padding) + encryptor.finalize()

# 3. Decifrar
decryptor = cipher.decryptor()
dados_decifrados_com_padding = decryptor.update(criptograma) + decryptor.finalize()

# 4. Remover Padding
unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
dados_originais = unpadder.update(dados_decifrados_com_padding) + unpadder.finalize()

print("--- AES-256-CBC ---")
print(f"Tamanho original: {len(chave_privada_simulada)} bytes")
print(f"Tamanho com padding: {len(dados_com_padding)} bytes")
print(f"Recuperado com sucesso? {chave_privada_simulada == dados_originais}")