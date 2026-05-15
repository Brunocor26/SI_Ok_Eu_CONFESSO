const API_URL = "/api";

const request = async (endpoint, options = {}) => {
  const config = {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    // Allows sending and receiving cookies (for Flask session)
    // Note: If running on different ports without proxy, CORS needs to be handled on Backend.
    // For local dev, Vite proxy is recommended.
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
    register: (username, password) => 
      request("/auth/register", {
        method: "POST",
        body: JSON.stringify({ username, password }),
      }),
    login: (username, password) =>
      request("/auth/login", {
        method: "POST",
        body: JSON.stringify({ username, password }),
      }),
    logout: () =>
      request("/auth/logout", {
        method: "POST",
      }),
    me: () => request("/auth/me"),
  },
  messages: {
    send: (recipient_email, subject, body) =>
      request("/messages/send", {
        method: "POST",
        body: JSON.stringify({ recipient_email, subject, body }),
      }),
    decrypt: (code) =>
      request("/messages/decrypt", {
        method: "POST",
        body: JSON.stringify({ code }),
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
  }
};
