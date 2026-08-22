# Casi d'uso

Attori del sistema e funzionalita accessibili a ciascuno. I ruoli sono
cumulativi: l'**Operatore** dispone delle funzioni di segreteria, l'**Admin**
di quelle di segreteria piu' la configurazione del poliambulatorio.

```mermaid
flowchart LR
    PAZ(["Paziente"])
    OPE(["Operatore<br/>(segreteria)"])
    ADM(["Admin"])

    subgraph AREA_PAZ["Area paziente"]
        UC1(["Registrarsi"])
        UC2(["Autenticarsi"])
        UC3(["Consultare medici<br/>e prestazioni"])
        UC4(["Consultare slot liberi"])
        UC5(["Prenotare una visita"])
        UC6(["Consultare le proprie<br/>prenotazioni"])
        UC7(["Annullare una propria<br/>prenotazione"])
    end

    subgraph AREA_OPE["Area segreteria"]
        UC8(["Consultare l'agenda<br/>completa"])
        UC9(["Prenotare per conto<br/>di un paziente"])
        UC10(["Riprogrammare una<br/>prenotazione"])
        UC11(["Completare una<br/>prenotazione"])
        UC12(["Annullare qualsiasi<br/>prenotazione"])
    end

    subgraph AREA_ADM["Area amministrativa"]
        UC13(["Gestire i medici"])
        UC14(["Gestire le prestazioni"])
        UC15(["Associare prestazioni<br/>ai medici"])
        UC16(["Gestire le disponibilita"])
        UC17(["Generare slot ricorrenti"])
        UC18(["Gestire gli utenti"])
    end

    UC1 --- PAZ
    UC2 --- PAZ
    UC3 --- PAZ
    UC4 --- PAZ
    UC5 --- PAZ
    UC6 --- PAZ
    UC7 --- PAZ

    UC2 --- OPE
    UC3 --- OPE
    UC4 --- OPE

    OPE --- UC8
    OPE --- UC9
    OPE --- UC10
    OPE --- UC11
    OPE --- UC12

    AREA_OPE --- ADM
    
    ADM --- UC13
    ADM --- UC14
    ADM --- UC15
    ADM --- UC16
    ADM --- UC17
    ADM --- UC18
```

## Note sui casi d'uso

- **Prenotare una visita** e **Consultare le proprie prenotazioni** sono
  riservati al ruolo `paziente`: un account di segreteria non ha un profilo
  paziente collegato e riceve `403`. La segreteria opera invece tramite
  *Prenotare per conto di un paziente*.
- **Prenotare una visita** include sempre la verifica che la prestazione scelta
  sia associata al medico dello slot: se l'associazione non esiste la richiesta
  viene respinta con `400`.
- **Riprogrammare**, **Completare** e **Annullare qualsiasi prenotazione** sono
  ammessi solo su prenotazioni attive (vedi
  [`stati-prenotazione.md`](stati-prenotazione.md)).
- **Generare slot ricorrenti** e' una specializzazione di *Gestire le
  disponibilita*: crea in blocco gli slot di un periodo saltando quelli che si
  sovrapporrebbero a slot gia esistenti.
