const API_URL = "/api";

const request = async (endpoint, options = {}) => {
  const config = {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    // Allows sending and receiving cookies (for Flask session)
  };

  const response = await fetch(`${API_URL}${endpoint}`, config);
  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error || "Algo correu mal no servidor.");
  }

  return data;
};

export const api = {
  auth: {
    register: (key_cipher_algo, rsa_key_size) =>
      request("/auth/register", {
        method: "POST",
        body: JSON.stringify({ key_cipher_algo, rsa_key_size }),
      }),
    login: (user_id, password) =>
      request("/auth/login", {
        method: "POST",
        body: JSON.stringify({ user_id, password }),
      }),
    logout: () =>       //?????
      request("/auth/logout", {
        method: "POST",
      }),
    me: () => request("/auth/me"),
  },
  messages: {
    send: (recipient_email, subject, body, notification_email, password) =>
      request("/messages/send", {
        method: "POST",
        body: JSON.stringify({ recipient_email, subject, body, notification_email: notification_email || null, password }),
      }),
    decrypt: (code, password, encrypted_body, private_key, hmac) =>
      request("/messages/decrypt", {
        method: "POST",
        body: JSON.stringify({ code, password, encrypted_body, private_key, hmac: hmac || null }),
      })
  },
  receipts: {
    verify: (code) =>
      request("/receipts/verify", {
        method: "POST",
        body: JSON.stringify({ code }),
      }),
    check: (code) =>
      request("/receipts/check", {
        method: "POST",
        body: JSON.stringify({ code }),
      }),
    confirmRead: (code, signature) =>
      request("/receipts/confirm-read", {
        method: "POST",
        body: JSON.stringify({ code, signature }),
      }),
  }
};
