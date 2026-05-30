USER                                                    SISTEMA

-------------------- RECEÇÃO DO EMAIL --------------------

[utilizador recebe email com código + corpo cifrado]
[clica na hiperligação -> abre /decrypt no browser]


-------------- INTRODUÇÃO DOS DADOS (PASSO 1) -------------
[frontend: pages/DecryptMessage.jsx]

introduz(code, pass, cifrado, chave_privada.pem) ----->
                                                        [apenas validação local no frontend]
                                                        [nenhum pedido ao servidor ainda]


------------- CONFIRMAÇÃO DE RECEÇÃO (PASSO 2) ------------
[frontend: pages/DecryptMessage.jsx | backend: routes/receipts.py]

"Confirmas que recebeste esta mensagem?" [Sim / Não]

  Não --> mensagem não é decifrada, fluxo termina

  Sim -------------------------------------------->
                                                        recibo = procurar(code)
                                                        recibo.confirmado_recebido = True
                                                        guarda(recibo)

ok  <------------------------------------------------


-------------- CONFIRMAÇÃO DE LEITURA (PASSO 3) -----------
[frontend: pages/DecryptMessage.jsx | backend: routes/messages.py, services/crypto.py]

"Confirmas que vais ler esta mensagem?" [Sim / Não]

  Não --> mensagem não é decifrada, fluxo termina

  Sim(code, pass, cifrado, priv_pem) ------------->
                                                        msg = procurar(code)
                                                        verificar cifrado == msg.cifrado_guardado
                                                        
                                                        user = procurar(msg.dest_email)
                                                        verificar PBKDF2(pass, salt_pw) == hash_guardada  ==autentica o destinatário==
                                                        
                                                        pub_derivada = extrairPublica(priv_pem)
                                                        verificar pub_derivada == pub_guardada  ==garante que a chave é do utilizador==
                                                        
                                                        key = PBKDF2(code, salt_m, it=600000)
                                                        verificar HMAC-SHA256(cifrado, key)  ==integridade da mensagem==
                                                        corpo = AES-256-CTR_dec(cifrado, key, nonce)
                                                        
                                                        texto_recibo = "Recibo de Leitura - msg:<id> - dest:<email> - data:<now>"
                                                        assinatura   = SHA256withRSA(texto_recibo, priv_pem)
                                                        
                                                        recibo.lido       = True
                                                        recibo.texto      = texto_recibo
                                                        recibo.assinatura = assinatura
                                                        guarda(recibo)

(assunto, corpo)  <----------------------------------


--------------------- RESULTADO (PASSO 4) -----------------
[frontend: pages/DecryptMessage.jsx]

[mensagem decifrada mostrada ao utilizador]
[emissor é notificado de que a mensagem foi lida]


------------- VERIFICAÇÃO DO RECIBO (EMISSOR) -------------
[frontend: pages/VerifyReceipt.jsx | backend: routes/receipts.py, services/crypto.py]

verificar(code) -------------------------------------->
                                                        recibo = procurar(code)
                                                        pub = userKeys.procurar(recibo.dest_user_id)
                                                        valido = SHA256withRSA_verify(recibo.texto, recibo.assinatura, pub)

(lido, confirmado_recebido, valido, texto_recibo)  <--

Nota: a assinatura prova que foi o DESTINATÁRIO a confirmar a leitura,
      porque só ele tem a chave privada correspondente à chave pública registada
