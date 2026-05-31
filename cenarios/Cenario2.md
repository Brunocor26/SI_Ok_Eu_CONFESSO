USER / BROWSER                                          SISTEMA

-------------------- RECEÇÃO DO EMAIL --------------------

[utilizador recebe email com código + corpo cifrado + HMAC]
[clica na hiperligação -> abre /decrypt no browser]


-------------- INTRODUÇÃO DOS DADOS (PASSO 1) -------------
[frontend: pages/DecryptMessage.jsx]

introduz(code, pass, cifrado, [hmac], chave_privada.json)
                                                        [apenas validação local no frontend]
                                                        [nenhum pedido ao servidor ainda]
                                                        [chave_privada.json é decifrada localmente
                                                         no browser: AES-256-CBC(PBKDF2(pass)) → priv_pem]


------------- CONFIRMAÇÃO DE RECEÇÃO (PASSO 2) ------------
[frontend: pages/DecryptMessage.jsx | backend: routes/receipts.py]

"Confirmas que recebeste esta mensagem?" [Sim / Não]

  Não --> mensagem não é decifrada, fluxo termina

  Sim: POST /api/receipts/verify  {code} ----------->
                                                        recibo = procurar(code)
                                                        recibo.confirmado_recebido = True
                                                        guarda(recibo)

ok  <------------------------------------------------


-------------- CONFIRMAÇÃO DE LEITURA (PASSO 3) -----------
[frontend: pages/DecryptMessage.jsx | backend: routes/messages.py, routes/receipts.py]

"Confirmas que vais ler esta mensagem?" [Sim / Não]

  Não --> mensagem não é decifrada, fluxo termina

  ==3a. DECIFRAÇÃO==
  Sim: POST /api/messages/decrypt  {code, pass, cifrado, [hmac]} -->
                                                        msg  = procurar(code)
                                                        verificar cifrado == msg.cifrado_guardado

                                                        id   = SHA256(pass)  ==encontrar o destinatário==
                                                        user = procurar(id)
                                                        verificar PBKDF2(pass, salt_pw) == hash_guardada

                                                        key  = PBKDF2(code, salt_m, it=600000)
                                                        verificar HMAC-SHA256(cifrado, key)  ==integridade==
                                                        corpo = AES-256-CTR_dec(cifrado, key, nonce)

                                                        texto_recibo = "Recibo de Leitura - msg:<id> - dest:<email> - data:<now>"
                                                        guarda texto_recibo no recibo (lido ainda = false)

  (assunto, corpo, texto_recibo)  <------------------

  ==3b. ASSINATURA NO BROWSER  (chave privada nunca sai do dispositivo)==

  assinatura = SHA256withRSA(texto_recibo, priv_pem)
  [Web Crypto API: RSASSA-PKCS1-v1_5 + SHA-256, inteiramente no browser]

  ==3c. SUBMISSÃO DA ASSINATURA==
  POST /api/receipts/submit-signature  {code, assinatura} -->
                                                        recibo = procurar(code)
                                                        pub    = userKeys.procurar(recibo.dest_user_id)
                                                        válido = SHA256withRSA_verify(texto_recibo, assinatura, pub)
                                                        se inválido → rejeitar (400)

                                                        recibo.lido       = True
                                                        recibo.assinatura = assinatura
                                                        guarda(recibo)

                                                        se msg.email_notif definido:
                                                            envia email ao emissor: "A sua mensagem foi lida"

ok  <------------------------------------------------


--------------------- RESULTADO (PASSO 4) -----------------
[frontend: pages/DecryptMessage.jsx]

[mensagem decifrada mostrada ao utilizador]


------------- VERIFICAÇÃO DO RECIBO (EMISSOR) -------------
[frontend: pages/VerifyReceipt.jsx | backend: routes/receipts.py]

verificar(code) -------------------------------------->
                                                        recibo = procurar(code)
                                                        pub    = userKeys.procurar(recibo.dest_user_id)
                                                        válido = SHA256withRSA_verify(recibo.texto, recibo.assinatura, pub)

(lido, confirmado_recebido, válido, texto_recibo)  <--

Nota: a assinatura prova que foi o DESTINATÁRIO a confirmar a leitura,
      porque só ele tem a chave privada correspondente à chave pública registada.
      A chave privada nunca é enviada ao servidor — a assinatura é produzida
      inteiramente no browser do destinatário.
