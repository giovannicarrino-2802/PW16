const API = "http://localhost:8000/api/v1";

function token() { return localStorage.getItem("token"); }

async function _detail(r) {
  try {
    const d = await r.json();
    if (d && d.detail) {
      return typeof d.detail === "string" ? d.detail : JSON.stringify(d.detail);
    }
  } catch (e) { /* corpo non JSON */ }
  return "Errore " + r.status;
}

async function apiLogin(email, password) {
  const body = new URLSearchParams({ username: email, password });
  const r = await fetch(API + "/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body
  });
  if (!r.ok) throw new Error("Login fallito: email o password errate");
  const d = await r.json();
  localStorage.setItem("token", d.access_token);
  return d;
}

async function apiMe() {
  return apiGet("/auth/me");
}

async function apiGet(path) {
  const r = await fetch(API + path, { headers: { Authorization: "Bearer " + token() } });
  if (!r.ok) throw new Error(await _detail(r));
  return r.json();
}

async function apiSend(method, path, data) {
  const opts = { method, headers: { Authorization: "Bearer " + token() } };
  if (data !== undefined) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(data);
  }
  const r = await fetch(API + path, opts);
  if (!r.ok) throw new Error(await _detail(r));
  if (r.status === 204) return null;
  const txt = await r.text();
  return txt ? JSON.parse(txt) : null;
}

function apiPost(path, data) { return apiSend("POST", path, data); }
function apiPut(path, data) { return apiSend("PUT", path, data); }
function apiPatch(path, data) { return apiSend("PATCH", path, data); }
function apiDelete(path) { return apiSend("DELETE", path); }
