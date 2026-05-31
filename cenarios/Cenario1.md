USER                                                    SISTEMA

---------------------- REGISTO -----------------------
[frontend: pages/Register.jsx | backend: routes/auth.py, services/auth.py, services/crypto.py]

registo() ------------------------------------------>
                                                        pass = gerarPassword(tam=16)
                                                        id   = SHA256(pass)    ==lookup key, deriva da password==
                                                        hash = PBKDF2(pass, salt_pw)  -> guarda (id, hash, salt_pw)
                                                        (pub, priv) = gerarParRSA(bits=2048)
                                                        priv_cifrada = AES-256-CBC(priv, PBKDF2(pass, salt_k))
                                                        guarda apenas pub  ==priv NUNCA é guardada no servidor==

pass, pub, priv_cifrada  <---------------------------------  pass, pub, priv_cifrada

[utilizador guarda pass + chave_publica.pem + chave_privada.json]
[chave_privada.json contém: cipher, salt, iv, ciphertext  (AES-256-CBC + PBKDF2)]

Nota: o backend NUNCA GUARDA A CHAVE PRIVADA!
      A chave privada é devolvida já cifrada e apenas o utilizador a pode decifrar com a sua password.
      Não existe login separado — a autenticação é feita inline em cada operação (envio/decifração).


----------------------- ENVIO DE MENSAGEM -----------------------
[frontend: pages/SendMessage.jsx | backend: routes/messages.py, services/crypto.py, services/email.py]

enviar(pass, dest, assunto, corpo, [email_notif]) --->
                                                        id = SHA256(pass)    ==encontrar o emissor==
                                                        verificar PBKDF2(pass, salt_pw) == hash_guardada

                                                        code   = token_hex(16)          [32 chars hex]
                                                        salt_m = random(16 bytes)
                                                        key    = PBKDF2(code, salt_m, it=600000)  -> 256 bits
                                                        (cifrado, nonce) = AES-256-CTR(corpo, key)
                                                        mac    = HMAC-SHA256(cifrado, key)
                                                        guarda (dest, assunto, cifrado, code, salt_m, nonce, mac, email_notif)
                                                        guarda recibo (confirmado_recebido=false, lido=false)
                                                        envia email para dest:

                                                          |--------------------------------------|
                                                          │ Para ler este email, aceda ao sistema│
                                                          │ e confirme a receção com o código:   │
                                                          │ <code>                               │
                                                          │ HMAC: <mac>                          │
                                                          │ --- CORPO CIFRADO ---                │
                                                          │ <cifrado>                            │
                                                          |--------------------------------------|

code (rastreio)  <-----------------------------------------  code
