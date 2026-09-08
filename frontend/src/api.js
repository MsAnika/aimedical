function normalizeErrorMessage(value) {
  if (value == null) return "Something went wrong.";
  if (typeof value === "string") return value;
  if (Array.isArray(value)) {
    return value
      .map((item) => normalizeErrorMessage(item))
      .filter(Boolean)
      .join("; ");
  }
  if (typeof value === "object") {
    if ("detail" in value) return normalizeErrorMessage(value.detail);
    if ("message" in value) return normalizeErrorMessage(value.message);
    return JSON.stringify(value);
  }
  return String(value);
}

export const API = {
  async request(path, { method = "GET", body, token, form } = {}) {
    const headers = {};
    if (token) headers.Authorization = `Bearer ${token}`;
    let payload;
    if (form) {
      payload = form;
    } else if (body) {
      headers["Content-Type"] = "application/json";
      payload = JSON.stringify(body);
    }
    const res = await fetch(path, { method, headers, body: payload });
    if (!res.ok) {
      let detail = res.statusText || "Request failed.";
      try {
        const data = await res.json();
        detail = normalizeErrorMessage(data);
      } catch (_) {}
      throw new Error(detail);
    }
    return res.json();
  },

  login(email, password) {
    return this.request("/api/auth/login", {
      method: "POST",
      body: { email, password },
    });
  },

  register(payload) {
    return this.request("/api/auth/register", {
      method: "POST",
      body: payload,
    });
  },

  me(token) {
    return this.request("/api/auth/me", { token });
  },

  diseases(token) {
    return this.request("/api/diseases", { token });
  },

  predictImage(token, disease, file) {
    const form = new FormData();
    form.append("disease", disease);
    form.append("file", file);
    return this.request("/api/predictions/image", { method: "POST", form, token });
  },

  predictTabular(token, disease, features) {
    return this.request("/api/predictions/tabular", {
      method: "POST",
      body: { disease, features },
      token,
    });
  },

  history(token) {
    return this.request("/api/history", { token });
  },

  prediction(token, id) {
    return this.request(`/api/predictions/${id}`, { token });
  },

  createReport(token, id) {
    return this.request(`/api/predictions/${id}/report`, { method: "POST", token });
  },

  adminStats(token) {
    return this.request("/api/admin/stats", { token });
  },
};

export function downloadUrl(url) {
  const a = document.createElement("a");
  a.href = url;
  a.download = "";
  document.body.appendChild(a);
  a.click();
  a.remove();
}