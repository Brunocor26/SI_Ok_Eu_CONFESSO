const nodemailer = require('nodemailer');

async function enviarEmailCifrado(destinatario, assunto, codigoAcesso, corpoCifrado) {
    // 1. Configurar a ligação ao Mailpit
    const transporter = nodemailer.createTransport({
        host: 'localhost',
        port: 1025,
        secure: false, // O Mailpit local não usa SSL/TLS
        ignoreTLS: true
    });

    // 2. Formatar a mensagem conforme o enunciado
    const textoEmail = `Se quiser ler este e-mail, aceda ao sistema https://OK-Eu-CONFESSO.xxx
e confirme a receção com o código ${codigoAcesso}. Ser-lhe-á decifrada e
mostrada a mensagem.

--- CORPO DA MENSAGEM CIFRADO ---
${corpoCifrado}
---------------------------------`;

    // 3. Opções do Email
    const opcoesEmail = {
        from: '"Sistema OK-Eu-CONFESSO" <sistema@ok-eu-confesso.xxx>',
        to: destinatario,
        subject: assunto,
        text: textoEmail, // Enviamos como texto simples para evitar que HTML interfira com o criptograma
    };

    // 4. Enviar
    try {
        const info = await transporter.sendMail(opcoesEmail);
        console.log(`[OK] Email enviado com sucesso para ${destinatario}!`);
        console.log(`-> Vai a http://localhost:8025 para veres o email.`);
    } catch (erro) {
        console.error(`[ERRO] Falha ao enviar. O Docker do Mailpit está a correr? Detalhes:`, erro);
    }
}

// --- Teste da Função ---
const testeDestinatario = "professor@universidade.pt";
const testeAssunto = "Relatório Secreto";
const testeCodigo = "A1B2C3D4E5F678901234567890ABCDEF"; // 32 caracteres Hex
const testeCifrado = "U2FsdGVkX1+vxyz... (simulação do criptograma AES)";

enviarEmailCifrado(testeDestinatario, testeAssunto, testeCodigo, testeCifrado);