import os
from cryptography.hazmat.primitives import hashes, serialization, padding as sym_padding
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
#Este ficheiro contem: 
# Confirmação Dupla: verificar confirmacao_rececao e confirmacao_leitura antes de avançar cumpre o requisito do Cenário 2. 
# Algoritmo de Cifra: AES em modo CTR para a decifragem do corpo da mensagem. 
# Assinatura Digital: A função gerar_recibo_digital utiliza SHA256 com RSA, o que corresponde ao requisito SHA256withRSA mencionado no enunciado. 
# Verificação: A função de verificação permite ao emissor validar a prova de leitura, fechando o ciclo de Não-Repúdio. 


#   Usada no registo: Transforma a chave RSA em bytes, cifra com AES-256-CBC 
#   e devolve os bytes para serem gravados no ficheiro .pem.
def cifrar_chave_privada(chave_privada_obj, password_16):

    # 1. Transformar o objeto da chave em bytes PEM (sem password interna)
    pem_original = chave_privada_obj.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    # 2. Preparar a cifra AES-256-CBC
    chave_aes = derivar_chave_pbkdf2(password_16)
    iv = os.urandom(16) # Gerar um IV aleatório (vital para CBC)
    
    # 3. Adicionar Padding (PKCS7) porque o CBC exige blocos de 16 bytes
    padder = sym_padding.PKCS7(128).padder()
    dados_padded = padder.update(pem_original) + padder.finalize()

    # 4. Cifrar
    cipher = Cipher(algorithms.AES(chave_aes), modes.CBC(iv))
    encryptor = cipher.encryptor()
    conteudo_cifrado = encryptor.update(dados_padded) + encryptor.finalize()

    # 5. O ficheiro final será: IV (16 bytes) + Conteúdo Cifrado
    return iv + conteudo_cifrado


#     Transforma a password ou o código de 32 chars numa chave de 32 bytes (256 bits).
def derivar_chave_pbkdf2(texto_secreto, salt=b'salt_projeto_si_2026'):

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000, # Quanto mais iterações, mais seguro contra ataques
    )
    # Se o texto for string, converte para bytes
    if isinstance(texto_secreto, str):
        texto_secreto = texto_secreto.encode()
        
    return kdf.derive(texto_secreto)


#recuperar chave privada que está trancada dentro de um ficheiro, cifrada com AES-256-CBC
def recuperar_chave_privada(ficheiro_pem_cifrado, password_16):

    try:
        # 1. Derivar a chave de 256 bits a partir da password
        chave_aes_cbc = derivar_chave_pbkdf2(password_16) 

        # 2. Ler os dados do ficheiro
        with open(ficheiro_pem_cifrado, "rb") as f:
            conteudo = f.read()
        
        # O IV (16 bytes) costuma estar no início do ficheiro cifrado
        iv = conteudo[:16]
        dados_cifrados = conteudo[16:]

        # 3. Configurar AES-256-CBC e executar a decifragem AES-256-CBC,
        cipher = Cipher(algorithms.AES(chave_aes_cbc), modes.CBC(iv))
        decryptor = cipher.decryptor()
        
        # Decifrar os dados
        dados_com_padding = decryptor.update(dados_cifrados) + decryptor.finalize()

        # 4. Remover o Padding (PKCS7)
        # O modo CBC exige blocos fixos, por isso temos de tirar o preenchimento
        unpadder = sym_padding.PKCS7(128).unpadder()
        dados_pem_limpos = unpadder.update(dados_com_padding) + unpadder.finalize()

        # 5. Converter os bytes PEM de volta para um objeto de Chave Privada RSA
        chave_privada = serialization.load_pem_private_key(
            dados_pem_limpos,
            password=None  # Aqui é None porque já a decifrámos nós manualmente
        )

        return chave_privada

    except Exception as e:
        raise Exception(f"Erro ao recuperar chave: Password incorreta ou ficheiro corrompido. ({str(e)})")


# Permite ao emissor verificar se o recibo assinado pelo destinatário é válido.
def verificar_recibo_leitura(texto_recibo, assinatura_bin, chave_publica_rsa):
    try:
        chave_publica_rsa.verify(
            assinatura_bin,
            texto_recibo.encode() if isinstance(texto_recibo, str) else texto_recibo,
            asym_padding.PSS(
                mgf=asym_padding.MGF1(hashes.SHA256()),
                salt_length=asym_padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True # Assinatura legítima!
    except Exception:
        return False # Assinatura inválida ou recibo alterado!


# --- DECIFRAGEM + CONFIRMAÇÃO DUPLA ---
def processar_fluxo_leitura(dados):
    # Verificação de Segurança (Cenário 2 do enunciado)
    # Só decifra se houver confirmação explícita de receção e leitura [cite: 114, 115]
    if not (dados['confirmacao_rececao'] and dados['confirmacao_leitura']):
        return None, "Acesso Negado: Confirmacões obrigatórias em falta."

    try:
        # O Passo Crítico: Recuperar a Chave Privada RSA
        # A chave privada está cifrada com AES-256-CBC usando a password de 16 chars 
        chave_privada_rsa = recuperar_chave_privada(
            dados['ficheiro_chave_priv'], 
            dados['password_16_chars']
        )

        # Decifrar o Corpo da Mensagem (AES-256-CTR) 
        # Deriva a chave de 256 bits a partir do código de 32 caracteres 
        chave_aes_msg = derivar_chave_pbkdf2(dados['codigo_32_hex'])
        
        corpo_cifrado = bytes.fromhex(dados['corpo_cifrado_hex'])
        # Nota: O nonce deve ser recuperado do envio, não ser fixo!
        cipher = Cipher(algorithms.AES(chave_aes_msg), modes.CTR(dados['nonce_msg']))
        decryptor = cipher.decryptor()
        mensagem_limpa = decryptor.update(corpo_cifrado) + decryptor.finalize()

        # --- TAREFA 1: RECIBO SHA256withRSA --- 
        # O sistema gera a assinatura digital como prova de leitura [cite: 117]
        texto_recibo, assinatura = gerar_recibo_digital(
            mensagem_limpa, 
            chave_privada_rsa, 
            dados['codigo_32_hex']
        )

        return {
            "mensagem": mensagem_limpa.decode('utf-8'),
            "recibo_texto": texto_recibo.decode(),
            "assinatura_hex": assinatura.hex()
        }, "Sucesso"

    except Exception as e:
        return None, f"Erro na operação: {str(e)}"


# --- FUNÇÃO AUXILIAR DE ASSINATURA ---
def gerar_recibo_digital(msg_limpa, chave_privada, codigo):
    # Texto do recibo conforme pedido no enunciado [cite: 117]
    texto_recibo = f"Recibo de leitura: Mensagem {codigo} lida com sucesso.".encode()
    
    assinatura = chave_privada.sign(
        texto_recibo,
        asym_padding.PSS(
            mgf=asym_padding.MGF1(hashes.SHA256()),
            salt_length=asym_padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return texto_recibo, assinatura