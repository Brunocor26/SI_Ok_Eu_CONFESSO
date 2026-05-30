USER                                                    SISTEMA
                                                        
---------------------- REGISTO -----------------------
[frontend: pages/Register.jsx | backend: routes/auth.py, services/auth.py, services/crypto.py]
                                                        
registo() ------------------------------------------>
                                                        pass = gerarPassword(tam=16)
                                                        id   = SHA256(pass)    ==lookup key, deriva da password==
                                                        hash = PBKDF2(pass, salt_pw)  -> guarda (id, hash, salt_pw)
                                                        (pub, priv) = gerarParRSA(bits=2048)
                                                        guarda apenas pub  ==priv NUNCA é guardada no servidor==

pass, pub, priv  <-----------------------------------------  pass, pub, priv

[utilizador guarda pass + chave_publica.pem + chave_privada.pem]

Nota: o backend NUNCA GUARDA A PASSWORD! 2 entidades a saberem a password nao pode acontecer, so o proprio dono

                                                        
----------------------- LOGIN ------------------------
[frontend: pages/Login.jsx | backend: routes/auth.py, services/auth.py]
                                                        
login(pass) ----------------------------------------->
                                                        id     = SHA256(pass)       ==lookup: encontrar o registo==
                                                        hash'  = PBKDF2(pass, salt_pw guardado)
                                                        verificar hash' == hash  -> cria sessão

autenticado  <---------------------------------------------  ok


Nota: SHA256(pass) serve apenas para ENCONTRAR o utilizador na BD (é rápido, usado como índice).
      PBKDF2(pass, salt) serve para VERIFICAR a password (é lento por design, 600k iterações).
      O servidor nunca guarda a password em claro.

----------------------- ENVIO DE MENSAGEM -----------------------
[frontend: pages/SendMessage.jsx | backend: routes/messages.py, services/crypto.py, services/email.py]

enviar(dest, assunto, corpo) ------------------------->
                                                        code   = token_hex(16)          [32 chars hex]
                                                        salt_m = random(16 bytes)
                                                        key    = PBKDF2(code, salt_m, it=600000)  -> 256 bits
                                                        (cifrado, nonce) = AES-256-CTR(corpo, key)
                                                        mac    = HMAC-SHA256(cifrado, key)
                                                        guarda (dest, assunto, cifrado, code, salt_m, nonce, mac)
                                                        guarda recibo (confirmado=false, lido=false)
                                                        envia email para dest:
                                                        
                                                          |--------------------------------------|
                                                          │ Para ler este email, aceda ao sistema│
                                                          │ e confirme a receção com o código:   │
                                                          │ <code>                               │
                                                          │ --- CORPO CIFRADO ---                │
                                                          │ <cifrado>                            │
                                                          |--------------------------------------|

code (rastreio)  <-----------------------------------------  code
