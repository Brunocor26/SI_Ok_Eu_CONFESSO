from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes
#
# O sistema tem de gerar uma assinatura digital do recibo de leitura.
#

# Gerar o par de chaves RSA
chave_privada = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
)
chave_publica = chave_privada.public_key()

recibo_leitura = b"O utilizador Vasco leu a mensagem no dia 28 de Marco."

# Assinar o recibo (usa a chave PRIVADA)
assinatura = chave_privada.sign(
    recibo_leitura,
    padding.PSS(
        mgf=padding.MGF1(hashes.SHA256()),
        salt_length=padding.PSS.MAX_LENGTH
    ),
    hashes.SHA256() # SHA256 with RSA
)

# Verificar a assinatura (usa a chave PUBLICA)
try:
    chave_publica.verify(
        assinatura,
        recibo_leitura,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    print("Assinatura verificada com SUCESSO! O recibo é autêntico.")
except Exception as e:
    print("A verificação FALHOU. O recibo foi alterado ou a chave está errada.")