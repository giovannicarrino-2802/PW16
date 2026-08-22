/* =========================================================================
   Poliambulatorio - logica front-end (vanilla JS)

   I controlli fatti qui sono agevolazioni d'uso, non controlli di sicurezza:
   la validazione effettiva risiede interamente nel back-end.
   ========================================================================= */

const $ = (id) => document.getElementById(id);

let currentUser = null;
let mediciCache = {};        // id -> medico
let prestazioniCache = {};   // id -> prestazione
let bookingSlots = [];       // slot liberi del medico selezionato
let weekStart = null;        // lunedi della settimana mostrata nel calendario
let selectedSlot = null;     // slot selezionato per la prenotazione

/* ---------- utilita ---------- */
function pad(n) { return String(n).padStart(2, "0"); }
function dateKey(d) { return d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate()); }
function startOfWeek(d) {
  const x = new Date(d); const off = (x.getDay() + 6) % 7;
  x.setHours(0, 0, 0, 0); x.setDate(x.getDate() - off); return x;
}
function addDays(d, n) { const x = new Date(d); x.setDate(x.getDate() + n); return x; }
function fmtTime(d) { return pad(d.getHours()) + ":" + pad(d.getMinutes()); }
function fmtDayHeader(d) {
  const gg = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"];
  return gg[(d.getDay() + 6) % 7] + " " + pad(d.getDate()) + "/" + pad(d.getMonth() + 1);
}
function fmtDateTime(iso) {
  return new Date(iso).toLocaleString("it-IT", { dateStyle: "short", timeStyle: "short" });
}
function toast(msg, ok = true) {
  const t = $("toast");
  t.textContent = msg;
  t.className = "toast " + (ok ? "ok" : "err");
  setTimeout(() => { t.className = "toast hidden"; }, 3200);
}

/* ============================ AUTENTICAZIONE ============================ */
$("login-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    await apiLogin($("email").value, $("password").value);
    await boot();
  } catch (err) { toast(err.message, false); }
});

$("logout").addEventListener("click", () => {
  localStorage.removeItem("token");
  currentUser = null;
  render();
});

async function boot() {
  try {
    currentUser = await apiMe();
  } catch (e) {
    localStorage.removeItem("token");
    currentUser = null;
  }
  render();
  // Dopo il login si parte sempre dalla scheda "Prenota" (evita di restare su
  // un pannello della sessione precedente, es. Amministrazione).
  if (currentUser) showTab("prenota");
}

function isStaff() { return currentUser && (currentUser.ruolo === "operatore" || currentUser.ruolo === "admin"); }

function render() {
  const logged = !!currentUser;
  $("login-view").classList.toggle("hidden", logged);
  $("app-view").classList.toggle("hidden", !logged);
  $("user-box").classList.toggle("hidden", !logged);
  if (logged) {
    $("user-info").textContent = currentUser.email + " (" + currentUser.ruolo + ")";
    const paziente = currentUser.ruolo === "paziente";
    // Le mie prenotazioni: solo paziente. Agenda: segreteria/admin. Amministrazione: admin.
    $("tab-btn-mie").classList.toggle("hidden", !paziente);
    $("tab-btn-agenda").classList.toggle("hidden", !isStaff());
    $("tab-btn-admin").classList.toggle("hidden", currentUser.ruolo !== "admin");
    // Selettore paziente in prenotazione (prenotazione per conto di - segreteria)
    $("operatore-paziente").classList.toggle("hidden", !isStaff());
  }
}

/* ============================ NAVIGAZIONE TAB ============================ */
// Mostra la scheda indicata (aggiorna pulsanti + pannelli) e ne avvia il caricamento.
function showTab(tab) {
  document.querySelectorAll(".tab").forEach((b) => b.classList.toggle("active", b.dataset.tab === tab));
  $("panel-prenota").classList.toggle("hidden", tab !== "prenota");
  $("panel-mie").classList.toggle("hidden", tab !== "mie");
  $("panel-agenda").classList.toggle("hidden", tab !== "agenda");
  $("panel-admin").classList.toggle("hidden", tab !== "admin");
  if (tab === "prenota") onEnterBooking();
  if (tab === "mie") loadMie();
  if (tab === "agenda") loadAgenda();
  if (tab === "admin") loadAdmin();
}

document.querySelectorAll(".tab").forEach((btn) => {
  btn.addEventListener("click", () => {
    // Ignora eventuali pulsanti nascosti per il ruolo corrente
    if (btn.classList.contains("hidden")) return;
    showTab(btn.dataset.tab);
  });
});

document.querySelectorAll(".subtab").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".subtab").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    const sub = btn.dataset.sub;
    $("sub-medici").classList.toggle("hidden", sub !== "medici");
    $("sub-prestazioni").classList.toggle("hidden", sub !== "prestazioni");
    $("sub-assoc").classList.toggle("hidden", sub !== "assoc");
    $("sub-disp").classList.toggle("hidden", sub !== "disp");
    $("sub-utenti").classList.toggle("hidden", sub !== "utenti");
  });
});

/* ============================ CARICAMENTO BASE ============================ */
// Ricarica medici e prestazioni ogni volta che si entra nella scheda "Prenota":
// cosi' i medici/prestazioni creati dall'admin compaiono senza rifare il login.
async function onEnterBooking() {
  const medici = await apiGet("/medici");
  mediciCache = {};
  medici.forEach((m) => { mediciCache[m.id] = m; });
  const sel = $("medico");
  const prev = sel.value;
  sel.innerHTML = "";
  medici.forEach((m) => {
    const o = document.createElement("option");
    o.value = m.id;
    o.textContent = m.nome + " " + m.cognome + " - " + m.specializzazione;
    sel.appendChild(o);
  });
  if (prev && mediciCache[prev]) sel.value = prev;   // mantiene la selezione

  const prest = await apiGet("/prestazioni");
  prestazioniCache = {};
  prest.forEach((p) => { prestazioniCache[p.id] = p; });

  if (isStaff()) await loadPazientiSelect();

  sel.onchange = onMedicoChange;
  await onMedicoChange();   // popola prestazioni e calendario del medico selezionato
}

// Popola il selettore paziente usato dalla segreteria per prenotare per conto altrui
async function loadPazientiSelect() {
  try {
    const pazienti = await apiGet("/pazienti");
    const sel = $("op-paziente");
    const prev = sel.value;
    sel.innerHTML = "";
    if (!pazienti.length) {
      const o = document.createElement("option");
      o.value = ""; o.textContent = "Nessun paziente registrato";
      sel.appendChild(o);
    } else {
      pazienti.forEach((p) => {
        const o = document.createElement("option");
        o.value = p.id;
        o.textContent = p.cognome + " " + p.nome + " (" + p.codice_fiscale + ")";
        sel.appendChild(o);
      });
      if (prev) sel.value = prev;
    }
  } catch (e) { toast(e.message, false); }
}

/* ============================ PRENOTAZIONE ============================ */
// Al cambio medico ricarica prestazioni associate e calendario
async function onMedicoChange() {
  const mid = $("medico").value;
  selectedSlot = null;
  $("booking-bar").classList.add("hidden");

  // Svuota e ricarica la tendina con le sole prestazioni del medico
  const ps = $("prestazione");
  ps.innerHTML = "";
  $("prestazione-info").textContent = "";
  if (!mid) { renderCalendar([]); return; }

  const prestazioni = await apiGet("/medici/" + mid + "/prestazioni");
  if (prestazioni.length === 0) {
    const o = document.createElement("option");
    o.value = ""; o.textContent = "Nessuna prestazione disponibile";
    ps.appendChild(o);
  } else {
    prestazioni.forEach((p) => {
      const o = document.createElement("option");
      o.value = p.id; o.textContent = p.nome;
      ps.appendChild(o);
    });
  }
  ps.onchange = updatePrestazioneInfo;
  updatePrestazioneInfo();

  await loadSlots(mid);
}

function updatePrestazioneInfo() {
  const pid = $("prestazione").value;
  const p = prestazioniCache[pid];
  $("prestazione-info").textContent = p
    ? "Durata: " + p.durata_min + " min  -  Prezzo: " + p.prezzo + " EUR"
    : "";
}

async function loadSlots(mid) {
  bookingSlots = await apiGet("/medici/" + mid + "/disponibilita");
  // Posiziona il calendario sulla settimana del primo slot disponibile
  if (bookingSlots.length) {
    weekStart = startOfWeek(new Date(bookingSlots[0].inizio));
  } else {
    weekStart = startOfWeek(new Date());
  }
  renderCalendar(bookingSlots);
}

function renderCalendar(slots) {
  const cal = $("calendar");
  cal.innerHTML = "";
  if (!weekStart) weekStart = startOfWeek(new Date());

  // Raggruppa slot per giorno
  const byDay = {};
  slots.forEach((s) => {
    const k = dateKey(new Date(s.inizio));
    (byDay[k] = byDay[k] || []).push(s);
  });

  const end = addDays(weekStart, 6);
  $("cal-range").textContent =
    pad(weekStart.getDate()) + "/" + pad(weekStart.getMonth() + 1) + " - " +
    pad(end.getDate()) + "/" + pad(end.getMonth() + 1) + "/" + end.getFullYear();

  let totalWeek = 0;
  for (let i = 0; i < 7; i++) {
    const day = addDays(weekStart, i);
    const col = document.createElement("div");
    col.className = "cal-col";
    const head = document.createElement("div");
    head.className = "cal-col-head";
    head.textContent = fmtDayHeader(day);
    col.appendChild(head);

    const daySlots = (byDay[dateKey(day)] || []).sort(
      (a, b) => new Date(a.inizio) - new Date(b.inizio));
    totalWeek += daySlots.length;

    if (daySlots.length === 0) {
      const none = document.createElement("div");
      none.className = "cal-none";
      none.textContent = "-";
      col.appendChild(none);
    } else {
      daySlots.forEach((s) => {
        const b = document.createElement("button");
        b.type = "button";
        b.className = "cal-slot" + (selectedSlot && selectedSlot.id === s.id ? " selected" : "");
        b.textContent = fmtTime(new Date(s.inizio));
        b.onclick = () => selectSlot(s);
        col.appendChild(b);
      });
    }
    cal.appendChild(col);
  }
  $("cal-empty").classList.toggle("hidden", slots.length !== 0 || totalWeek !== 0);
}

function selectSlot(s) {
  selectedSlot = s;
  renderCalendar(bookingSlots);
  const pSel = $("prestazione");
  const p = prestazioniCache[pSel.value];
  const med = mediciCache[s.medico_id];
  const bar = $("booking-bar");
  if (!pSel.value) {
    $("booking-summary").textContent =
      "Seleziona una prestazione per confermare (" + fmtDateTime(s.inizio) + ")";
  } else {
    $("booking-summary").textContent =
      (p ? p.nome : "Prestazione") + " con " +
      (med ? med.nome + " " + med.cognome : "il medico") +
      " - " + fmtDateTime(s.inizio);
  }
  bar.classList.remove("hidden");
}

$("cal-prev").addEventListener("click", () => { weekStart = addDays(weekStart, -7); renderCalendar(bookingSlots); });
$("cal-next").addEventListener("click", () => { weekStart = addDays(weekStart, 7); renderCalendar(bookingSlots); });
$("booking-cancel").addEventListener("click", () => {
  selectedSlot = null;
  $("booking-bar").classList.add("hidden");
  renderCalendar(bookingSlots);
});

$("booking-confirm").addEventListener("click", async () => {
  const pid = $("prestazione").value;
  if (!selectedSlot) { toast("Seleziona uno slot dal calendario", false); return; }
  if (!pid) { toast("Seleziona una prestazione", false); return; }
  try {
    if (isStaff()) {
      // La segreteria prenota per conto del paziente selezionato
      const paz = $("op-paziente").value;
      if (!paz) { toast("Seleziona il paziente per cui prenotare", false); return; }
      await apiPost("/appuntamenti/operatore", {
        paziente_id: Number(paz),
        disponibilita_id: selectedSlot.id,
        prestazione_id: Number(pid),
      });
      toast("Prenotazione registrata per il paziente");
    } else {
      await apiPost("/appuntamenti", {
        disponibilita_id: selectedSlot.id,
        prestazione_id: Number(pid),
      });
      toast("Prenotazione confermata");
      await loadMie();
    }
    selectedSlot = null;
    $("booking-bar").classList.add("hidden");
    await loadSlots($("medico").value);
  } catch (e) { toast(e.message, false); }
});

/* ============================ LE MIE PRENOTAZIONI ============================ */
async function loadMie() {
  const ul = $("mie");
  // Solo i pazienti hanno prenotazioni: per operatore/admin evitiamo il 403.
  if (!currentUser || currentUser.ruolo !== "paziente") {
    ul.innerHTML = "<li class='muted'>Sezione disponibile solo per gli account paziente.</li>";
    return;
  }
  let mie;
  try { mie = await apiGet("/appuntamenti"); }
  catch (e) { ul.innerHTML = "<li class='muted'>" + e.message + "</li>"; return; }
  ul.innerHTML = "";
  if (!mie.length) { ul.innerHTML = "<li class='muted'>Nessuna prenotazione.</li>"; return; }
  mie.forEach((a) => {
    const li = document.createElement("li");
    const p = prestazioniCache[a.prestazione_id];
    const med = mediciCache[a.medico_id];
    const info = document.createElement("span");
    info.textContent = fmtDateTime(a.inizio) + " - " +
      (p ? p.nome : "Prestazione #" + a.prestazione_id) +
      (med ? " con " + med.nome + " " + med.cognome : "") +
      "  [" + a.stato + "]";
    li.appendChild(info);
    if (a.stato !== "annullata" && a.stato !== "completata") {
      const b = document.createElement("button");
      b.className = "btn-danger";
      b.textContent = "Annulla";
      b.onclick = async () => {
        try {
          await apiPatch("/appuntamenti/" + a.id, { stato: "annullata" });
          toast("Prenotazione annullata");
          await loadMie();
          if ($("medico").value) await loadSlots($("medico").value);
        } catch (e) { toast(e.message, false); }
      };
      li.appendChild(b);
    }
    ul.appendChild(li);
  });
}

/* ============================ AGENDA (segreteria / admin) ============================ */
let agendaCache = [];

async function loadAgenda() {
  if (!isStaff()) return;
  try { agendaCache = await apiGet("/appuntamenti/tutti"); }
  catch (e) { toast(e.message, false); return; }
  renderAgenda();
}

function renderAgenda() {
  const filtro = $("agenda-stato").value;
  const tb = $("tbody-agenda");
  tb.innerHTML = "";
  const righe = agendaCache.filter((a) => {
    if (filtro === "tutte") return true;
    if (filtro === "attive") return a.stato === "prenotata";
    return a.stato === filtro;
  });
  if (!righe.length) {
    tb.innerHTML = "<tr><td colspan='7' class='muted'>Nessuna prenotazione.</td></tr>";
    return;
  }
  righe.forEach((a) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${a.id}</td><td>${fmtDateTime(a.inizio)}</td>` +
      `<td>${a.paziente_nome}</td><td>${a.medico_nome}</td>` +
      `<td>${a.prestazione_nome}</td>` +
      `<td><span class="stato stato-${a.stato}">${a.stato}</span></td>`;
    const td = document.createElement("td");
    td.className = "actions";
    if (a.stato !== "annullata" && a.stato !== "completata") {
      const resched = document.createElement("button");
      resched.className = "btn-ghost"; resched.textContent = "Riprogramma";
      resched.onclick = () => openReschedule(a, td);
      const done = document.createElement("button");
      done.className = "btn-ghost"; done.textContent = "Completa";
      done.onclick = () => agendaAction(a.id, { stato: "completata" }, "Visita completata");
      const canc = document.createElement("button");
      canc.className = "btn-danger"; canc.textContent = "Annulla";
      canc.onclick = () => {
        if (confirm("Annullare la prenotazione #" + a.id + "?"))
          agendaAction(a.id, { stato: "annullata" }, "Prenotazione annullata");
      };
      td.appendChild(resched); td.appendChild(done); td.appendChild(canc);
    } else {
      td.innerHTML = "<span class='muted'>-</span>";
    }
    tr.appendChild(td);
    tb.appendChild(tr);
  });
}

async function agendaAction(id, body, okMsg) {
  try {
    await apiPatch("/appuntamenti/tutti/" + id, body);
    toast(okMsg);
    await loadAgenda();
  } catch (e) { toast(e.message, false); }
}

// Riprogrammazione inline: mostra gli slot liberi del medico e sposta la prenotazione
async function openReschedule(a, td) {
  td.innerHTML = "<span class='muted'>Carico slot...</span>";
  let slots;
  try { slots = await apiGet("/medici/" + a.medico_id + "/disponibilita"); }
  catch (e) { toast(e.message, false); renderAgenda(); return; }
  td.innerHTML = "";
  const sel = document.createElement("select");
  if (!slots.length) {
    const o = document.createElement("option");
    o.value = ""; o.textContent = "Nessuno slot libero";
    sel.appendChild(o);
  }
  slots.forEach((s) => {
    const o = document.createElement("option");
    o.value = s.id; o.textContent = fmtDateTime(s.inizio);
    sel.appendChild(o);
  });
  const ok = document.createElement("button");
  ok.textContent = "Sposta";
  ok.onclick = () => {
    if (!sel.value) { toast("Nessuno slot disponibile", false); return; }
    agendaAction(a.id, { disponibilita_id: Number(sel.value) }, "Prenotazione riprogrammata");
  };
  const no = document.createElement("button");
  no.className = "btn-ghost"; no.textContent = "Annulla";
  no.onclick = renderAgenda;
  td.appendChild(sel); td.appendChild(ok); td.appendChild(no);
}

$("agenda-stato").addEventListener("change", renderAgenda);
$("agenda-refresh").addEventListener("click", loadAgenda);

/* ============================ AMMINISTRAZIONE ============================ */
async function loadAdmin() {
  if (!currentUser || currentUser.ruolo !== "admin") return;
  // Ogni sezione e' indipendente: un errore in una non deve bloccare le altre.
  for (const step of [loadAdminMedici, loadAdminPrestazioni, refreshAssocSelects,
                      refreshDispSelects, loadAdminUtenti]) {
    try { await step(); }
    catch (e) { toast(e.message, false); }
  }
}

/* ----- Medici ----- */
async function loadAdminMedici() {
  const medici = await apiGet("/admin/medici");
  mediciCache = {};
  medici.forEach((m) => { mediciCache[m.id] = m; });
  const tb = $("tbody-medici");
  tb.innerHTML = "";
  medici.forEach((m) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${m.id}</td><td>${m.nome}</td><td>${m.cognome}</td><td>${m.specializzazione}</td>`;
    const td = document.createElement("td");
    td.className = "actions";
    const edit = document.createElement("button");
    edit.className = "btn-ghost"; edit.textContent = "Modifica";
    edit.onclick = () => {
      $("medico-id").value = m.id;
      $("medico-nome").value = m.nome;
      $("medico-cognome").value = m.cognome;
      $("medico-spec").value = m.specializzazione;
    };
    const del = document.createElement("button");
    del.className = "btn-danger"; del.textContent = "Elimina";
    del.onclick = async () => {
      if (!confirm("Eliminare il medico " + m.nome + " " + m.cognome + "?")) return;
      try { await apiDelete("/admin/medici/" + m.id); toast("Medico eliminato"); await loadAdmin(); }
      catch (e) { toast(e.message, false); }
    };
    td.appendChild(edit); td.appendChild(del);
    tr.appendChild(td);
    tb.appendChild(tr);
  });
}

$("form-medico").addEventListener("submit", async (e) => {
  e.preventDefault();
  const id = $("medico-id").value;
  const body = {
    nome: $("medico-nome").value,
    cognome: $("medico-cognome").value,
    specializzazione: $("medico-spec").value,
  };
  try {
    if (id) await apiPut("/admin/medici/" + id, body);
    else await apiPost("/admin/medici", body);
    toast("Medico salvato");
    resetMedicoForm();
    await loadAdmin();
  } catch (err) { toast(err.message, false); }
});
$("medico-reset").addEventListener("click", resetMedicoForm);
function resetMedicoForm() {
  $("medico-id").value = ""; $("medico-nome").value = "";
  $("medico-cognome").value = ""; $("medico-spec").value = "";
}

/* ----- Prestazioni ----- */
async function loadAdminPrestazioni() {
  const prest = await apiGet("/admin/prestazioni");
  prestazioniCache = {};
  prest.forEach((p) => { prestazioniCache[p.id] = p; });
  const tb = $("tbody-prestazioni");
  tb.innerHTML = "";
  prest.forEach((p) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${p.id}</td><td>${p.nome}</td><td>${p.durata_min} min</td><td>${p.prezzo} EUR</td>`;
    const td = document.createElement("td");
    td.className = "actions";
    const edit = document.createElement("button");
    edit.className = "btn-ghost"; edit.textContent = "Modifica";
    edit.onclick = () => {
      $("prest-id").value = p.id;
      $("prest-nome").value = p.nome;
      $("prest-durata").value = p.durata_min;
      $("prest-prezzo").value = p.prezzo;
    };
    const del = document.createElement("button");
    del.className = "btn-danger"; del.textContent = "Elimina";
    del.onclick = async () => {
      if (!confirm("Eliminare la prestazione " + p.nome + "?")) return;
      try { await apiDelete("/admin/prestazioni/" + p.id); toast("Prestazione eliminata"); await loadAdmin(); }
      catch (e) { toast(e.message, false); }
    };
    td.appendChild(edit); td.appendChild(del);
    tr.appendChild(td);
    tb.appendChild(tr);
  });
}

$("form-prestazione").addEventListener("submit", async (e) => {
  e.preventDefault();
  const id = $("prest-id").value;
  const body = {
    nome: $("prest-nome").value,
    durata_min: Number($("prest-durata").value),
    prezzo: Number($("prest-prezzo").value),
  };
  try {
    if (id) await apiPut("/admin/prestazioni/" + id, body);
    else await apiPost("/admin/prestazioni", body);
    toast("Prestazione salvata");
    resetPrestForm();
    await loadAdmin();
  } catch (err) { toast(err.message, false); }
});
$("prest-reset").addEventListener("click", resetPrestForm);
function resetPrestForm() {
  $("prest-id").value = ""; $("prest-nome").value = "";
  $("prest-durata").value = ""; $("prest-prezzo").value = "";
}

/* ----- Associazioni ----- */
function fillMedicoSelect(sel) {
  sel.innerHTML = "";
  Object.values(mediciCache).forEach((m) => {
    const o = document.createElement("option");
    o.value = m.id; o.textContent = m.nome + " " + m.cognome + " - " + m.specializzazione;
    sel.appendChild(o);
  });
}
function fillPrestSelect(sel) {
  sel.innerHTML = "";
  Object.values(prestazioniCache).forEach((p) => {
    const o = document.createElement("option");
    o.value = p.id; o.textContent = p.nome;
    sel.appendChild(o);
  });
}
async function refreshAssocSelects() {
  fillMedicoSelect($("assoc-medico"));
  fillPrestSelect($("assoc-prestazione"));
  $("assoc-medico").onchange = loadAssocList;
  await loadAssocList();
}
async function loadAssocList() {
  const mid = $("assoc-medico").value;
  const ul = $("assoc-list");
  ul.innerHTML = "";
  if (!mid) return;
  const prest = await apiGet("/admin/medici/" + mid + "/prestazioni");
  if (!prest.length) { ul.innerHTML = "<li class='muted'>Nessuna prestazione associata.</li>"; return; }
  prest.forEach((p) => {
    const li = document.createElement("li");
    const span = document.createElement("span");
    span.textContent = p.nome + " (" + p.durata_min + " min, " + p.prezzo + " EUR)";
    li.appendChild(span);
    const del = document.createElement("button");
    del.className = "btn-danger"; del.textContent = "Rimuovi";
    del.onclick = async () => {
      try { await apiDelete("/admin/medici/" + mid + "/prestazioni/" + p.id); toast("Associazione rimossa"); await loadAssocList(); }
      catch (e) { toast(e.message, false); }
    };
    li.appendChild(del);
    ul.appendChild(li);
  });
}
$("assoc-add").addEventListener("click", async () => {
  const mid = $("assoc-medico").value;
  const pid = $("assoc-prestazione").value;
  if (!mid || !pid) return;
  try {
    await apiPost("/admin/medici/" + mid + "/prestazioni", { prestazione_id: Number(pid) });
    toast("Prestazione associata");
    await loadAssocList();
  } catch (e) { toast(e.message, false); }
});

/* ----- Disponibilita (generatore ricorrente + calendario) ----- */
let dispSlots = [];
let dispWeekStart = null;
const GIORNI = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]; // indice = weekday Python 0..6

function buildWeekdayChips() {
  const wrap = $("gen-giorni");
  if (!wrap) return;
  wrap.innerHTML = "";
  GIORNI.forEach((g, i) => {
    const lab = document.createElement("label");
    lab.className = "wd-chip";
    const cb = document.createElement("input");
    cb.type = "checkbox"; cb.value = i;
    if (i === 0 || i === 3) cb.checked = true; // default: lunedi e giovedi
    lab.appendChild(cb);
    lab.appendChild(document.createTextNode(" " + g));
    wrap.appendChild(lab);
  });
}

function initDispDefaults() {
  buildWeekdayChips();
  const oggi = new Date();
  const tra30 = addDays(oggi, 30);
  if ($("gen-da")) $("gen-da").value = dateKey(oggi);
  if ($("gen-a")) $("gen-a").value = dateKey(tra30);
}

// Popola la select del medico (Step 1) e carica i suoi slot
function refreshDispSelects() {
  const sel = $("disp-medico");
  const prev = sel.value;
  sel.innerHTML = "";
  Object.values(mediciCache).forEach((m) => {
    const o = document.createElement("option");
    o.value = m.id; o.textContent = m.nome + " " + m.cognome + " - " + m.specializzazione;
    sel.appendChild(o);
  });
  if (prev && mediciCache[prev]) sel.value = prev;
  sel.onchange = loadDispSlots;
  return loadDispSlots();
}

async function loadDispSlots() {
  const mid = $("disp-medico").value;
  if (!mid) { dispSlots = []; renderDispCalendar(); return; }
  dispSlots = await apiGet("/admin/disponibilita?medico_id=" + mid);
  dispWeekStart = dispSlots.length ? startOfWeek(new Date(dispSlots[0].inizio)) : startOfWeek(new Date());
  renderDispCalendar();
}

function renderDispCalendar() {
  const cal = $("disp-calendar");
  cal.innerHTML = "";
  if (!dispWeekStart) dispWeekStart = startOfWeek(new Date());

  const byDay = {};
  dispSlots.forEach((s) => {
    const k = dateKey(new Date(s.inizio));
    (byDay[k] = byDay[k] || []).push(s);
  });

  const end = addDays(dispWeekStart, 6);
  $("disp-range").textContent =
    pad(dispWeekStart.getDate()) + "/" + pad(dispWeekStart.getMonth() + 1) + " - " +
    pad(end.getDate()) + "/" + pad(end.getMonth() + 1) + "/" + end.getFullYear();

  let weekTotal = 0;
  for (let i = 0; i < 7; i++) {
    const day = addDays(dispWeekStart, i);
    const col = document.createElement("div");
    col.className = "cal-col";
    const head = document.createElement("div");
    head.className = "cal-col-head";
    head.textContent = fmtDayHeader(day);
    col.appendChild(head);

    const daySlots = (byDay[dateKey(day)] || []).sort(
      (a, b) => new Date(a.inizio) - new Date(b.inizio));
    weekTotal += daySlots.length;

    if (daySlots.length === 0) {
      const none = document.createElement("div");
      none.className = "cal-none";
      none.textContent = "-";
      col.appendChild(none);
    } else {
      daySlots.forEach((s) => {
        const chip = document.createElement("div");
        chip.className = "disp-chip" + (s.occupato ? " occ" : "");
        const t = document.createElement("span");
        t.textContent = fmtTime(new Date(s.inizio));
        chip.appendChild(t);
        const x = document.createElement("button");
        x.type = "button"; x.className = "disp-x"; x.textContent = "\u00d7";
        x.title = s.occupato ? "Slot prenotato (non eliminabile)" : "Elimina slot";
        x.onclick = async () => {
          if (s.occupato) { toast("Slot gia prenotato: non eliminabile", false); return; }
          if (!confirm("Eliminare lo slot delle " + fmtTime(new Date(s.inizio)) +
                       " del " + fmtDayHeader(new Date(s.inizio)) + "?")) return;
          try { await apiDelete("/admin/disponibilita/" + s.id); toast("Slot eliminato"); await loadDispSlots(); }
          catch (e) { toast(e.message, false); }
        };
        chip.appendChild(x);
        col.appendChild(chip);
      });
    }
    cal.appendChild(col);
  }
  $("disp-empty").classList.toggle("hidden", weekTotal !== 0);
}

$("disp-prev").addEventListener("click", () => { dispWeekStart = addDays(dispWeekStart, -7); renderDispCalendar(); });
$("disp-next").addEventListener("click", () => { dispWeekStart = addDays(dispWeekStart, 7); renderDispCalendar(); });

$("gen-btn").addEventListener("click", async () => {
  const mid = $("disp-medico").value;
  if (!mid) { toast("Seleziona un medico", false); return; }
  const giorni = Array.from($("gen-giorni").querySelectorAll("input:checked")).map((c) => Number(c.value));
  if (!giorni.length) { toast("Seleziona almeno un giorno della settimana", false); return; }
  if (!$("gen-da").value || !$("gen-a").value) { toast("Imposta il periodo (dal / al)", false); return; }
  const body = {
    medico_id: Number(mid),
    data_inizio: $("gen-da").value,
    data_fine: $("gen-a").value,
    giorni,
    ora_inizio: $("gen-ora-da").value,
    ora_fine: $("gen-ora-a").value,
    durata_min: Number($("gen-durata").value),
  };
  try {
    const res = await apiPost("/admin/disponibilita/genera", body);
    const msg = res.creati_count + " slot creati" +
      (res.saltati ? (", " + res.saltati + " saltati (gia presenti)") : "");
    $("gen-result").textContent = msg;
    toast(msg);
    await loadDispSlots();
  } catch (e) { toast(e.message, false); }
});

/* ----- Utenti (admin) ----- */
function toggleUtentePazFields() {
  const isPaz = $("utente-ruolo").value === "paziente";
  const editing = !!$("utente-id").value;
  // I campi anagrafici servono solo alla creazione di nuovi pazienti
  $("utente-paziente-fields").style.display = (isPaz && !editing) ? "flex" : "none";
}
$("utente-ruolo").addEventListener("change", toggleUtentePazFields);

async function loadAdminUtenti() {
  const utenti = await apiGet("/admin/utenti");
  const tb = $("tbody-utenti");
  tb.innerHTML = "";
  utenti.forEach((u) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${u.id}</td><td>${u.email}</td><td><span class="stato stato-${u.ruolo}">${u.ruolo}</span></td>`;
    const td = document.createElement("td");
    td.className = "actions";
    const edit = document.createElement("button");
    edit.className = "btn-ghost"; edit.textContent = "Modifica";
    edit.onclick = () => {
      $("utente-id").value = u.id;
      $("utente-email").value = u.email;
      $("utente-ruolo").value = u.ruolo;
      $("utente-password").value = "";
      $("utente-password").placeholder = "Nuova password (lascia vuoto)";
      toggleUtentePazFields();
    };
    const del = document.createElement("button");
    del.className = "btn-danger"; del.textContent = "Elimina";
    del.onclick = async () => {
      if (currentUser && u.id === currentUser.id) { toast("Non puoi eliminare il tuo account", false); return; }
      if (!confirm("Eliminare l'utente " + u.email + "? Verranno rimosse anche le sue prenotazioni.")) return;
      try { await apiDelete("/admin/utenti/" + u.id); toast("Utente eliminato"); await loadAdminUtenti(); }
      catch (e) { toast(e.message, false); }
    };
    td.appendChild(edit); td.appendChild(del);
    tr.appendChild(td);
    tb.appendChild(tr);
  });
}

$("form-utente").addEventListener("submit", async (e) => {
  e.preventDefault();
  const id = $("utente-id").value;
  try {
    if (id) {
      const body = { email: $("utente-email").value, ruolo: $("utente-ruolo").value };
      const pw = $("utente-password").value;
      if (pw) body.password = pw;
      await apiPut("/admin/utenti/" + id, body);
      toast("Utente aggiornato");
    } else {
      const pw = $("utente-password").value;
      if (!pw) { toast("La password e' obbligatoria per un nuovo utente", false); return; }
      const body = {
        email: $("utente-email").value,
        password: pw,
        ruolo: $("utente-ruolo").value,
      };
      if (body.ruolo === "paziente") {
        body.nome = $("utente-nome").value;
        body.cognome = $("utente-cognome").value;
        body.codice_fiscale = $("utente-cf").value;
        body.telefono = $("utente-tel").value || null;
      }
      await apiPost("/admin/utenti", body);
      toast("Utente creato");
    }
    resetUtenteForm();
    await loadAdminUtenti();
  } catch (err) { toast(err.message, false); }
});
$("utente-reset").addEventListener("click", resetUtenteForm);
function resetUtenteForm() {
  $("utente-id").value = "";
  $("utente-email").value = "";
  $("utente-password").value = "";
  $("utente-password").placeholder = "Password";
  $("utente-ruolo").value = "paziente";
  $("utente-nome").value = ""; $("utente-cognome").value = "";
  $("utente-cf").value = ""; $("utente-tel").value = "";
  toggleUtentePazFields();
}

/* ============================ AVVIO ============================ */
initDispDefaults();
toggleUtentePazFields();
boot();
