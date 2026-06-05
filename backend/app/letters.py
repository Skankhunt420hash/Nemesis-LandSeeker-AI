DISCLAIMER = "This is not legal advice. Verify with the responsible Grundbuchamt."

def letter_de(candidate, contact_placeholder="[Ihr Name, Adresse, E-Mail, Telefon]"):
    return f"""Betreff: Anfrage zu Grundstück {candidate.parcel_number} in {candidate.municipality} ({candidate.canton})

Sehr geehrte Damen und Herren

Ich bitte höflich um Auskunft, ob das Grundstück Nr. {candidate.parcel_number} in der Gemeinde {candidate.municipality} im Grundbuch als herrenlos eingetragen ist.

Zusätzlich bitte ich um Mitteilung, ob eine Aneignung nach Art. 658 ZGB grundsätzlich möglich wäre und ob kantonale/kommunale Vorkaufs- oder Genehmigungsrechte bestehen.

Objektdaten:
- Koordinaten: {candidate.latitude}, {candidate.longitude}
- Quelle: {candidate.source_url}
- Letzte Prüfung: {candidate.date_checked}

Kontakt:
{contact_placeholder}

Freundliche Grüsse

{DISCLAIMER}
"""

def letter_fr(candidate, contact_placeholder="[Nom, adresse, e-mail, téléphone]"):
    return f"""Objet: Demande concernant la parcelle {candidate.parcel_number} à {candidate.municipality} ({candidate.canton})

Madame, Monsieur,

Je vous prie de bien vouloir confirmer si la parcelle n° {candidate.parcel_number} dans la commune de {candidate.municipality} est inscrite comme sans maître au registre foncier.

Je vous prie également d’indiquer si une appropriation selon l’art. 658 CC est en principe possible, et s’il existe des droits de préemption ou d’autorisation cantonaux/communaux.

Données:
- Coordonnées: {candidate.latitude}, {candidate.longitude}
- Source: {candidate.source_url}
- Vérifié le: {candidate.date_checked}

Contact:
{contact_placeholder}

Cordialement,

{DISCLAIMER}
"""

def letter_it(candidate, contact_placeholder="[Nome, indirizzo, e-mail, telefono]"):
    return f"""Oggetto: Richiesta sulla particella {candidate.parcel_number} a {candidate.municipality} ({candidate.canton})

Gentili Signore e Signori,

Vi chiedo cortesemente di confermare se la particella n. {candidate.parcel_number} nel Comune di {candidate.municipality} risulta registrata come senza padrone nel registro fondiario.

Chiedo inoltre se un’appropriazione ai sensi dell’art. 658 CC sia in linea di principio possibile, e se esistano diritti di prelazione o autorizzazioni cantonali/comunali.

Dati:
- Coordinate: {candidate.latitude}, {candidate.longitude}
- Fonte: {candidate.source_url}
- Verificato il: {candidate.date_checked}

Contatto:
{contact_placeholder}

Cordiali saluti,

{DISCLAIMER}
"""

