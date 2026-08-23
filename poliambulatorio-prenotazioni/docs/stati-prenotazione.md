# Ciclo di vita della prenotazione

Stati ammessi per un `Appuntamento` e transizioni consentite.

```mermaid
stateDiagram-v2
    direction LR
    [*] --> prenotata : creazione<br/>(paziente o segreteria)

    prenotata --> annullata : annullamento<br/>(paziente o segreteria)
    prenotata --> completata : visita erogata<br/>(segreteria)
    prenotata --> prenotata : riprogrammazione<br/>(nuovo slot)

    annullata --> [*]
    completata --> [*]

    note left of prenotata
        Unico stato attivo.
        Lo slot collegato risulta occupato.
    end note

    note right of annullata
        Stato terminale.
        Lo slot torna disponibile.
    end note

    note right of completata
        Stato terminale.
        Lo slot resta occupato.
    end note
```

## Regole applicate

Annullamento, completamento e riprogrammazione richiedono lo stato `prenotata`:
da uno stato terminale il service risponde `409`. Il vincolo non è formale ma
sostanziale, perché solo una prenotazione attiva "possiede" il proprio slot.
Agire su una prenotazione già terminata libererebbe uno slot che nel frattempo
può essere stato assegnato a un'altra, producendo due appuntamenti sullo stesso
orario.

Copertura di test: `backend/tests/test_stati_prenotazione.py`.
