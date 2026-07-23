"""Default seed content for the redesigned GateKeeper.

Ported from the approved React prototype (INFOS-NICHT-UPLOADEN). Provides
default values for AppSettings (branding + questionnaire intro) and the seven
InfoCategory entries (four languages each). All of this is admin-editable at
runtime; these are just sensible starting values for a fresh install.
"""

# --- Questionnaire intro (per language) ------------------------------------
HEALTH_INTRO = {
    "de": "Haben Sie in den letzten 7 Tagen an folgenden Krankheiten gelitten?",
    "en": "In the last 7 days, have you suffered from any of the following illnesses?",
    "fr": "Au cours des 7 derniers jours, avez-vous souffert des maladies suivantes ?",
    "es": "En los últimos 7 días, ¿ha padecido alguna de las siguientes enfermedades?",
}

# --- Default health questions (position, key, de, en, fr, es) --------------
DEFAULT_QUESTIONS = [
    (1, "flu", "Erkältungskrankheiten (Husten, Schnupfen, Fieber)",
     "Flu diseases (cough, runny nose, fever)",
     "Maladies grippales (toux, rhume, fièvre)",
     "Enfermedades gripales (tos, resfriado, fiebre)"),
    (2, "diarrhea", "Durchfall oder Erbrechen",
     "Diarrhoea or vomiting",
     "Diarrhée ou vomissements",
     "Diarrea o vómitos"),
    (3, "food_poisoning",
     "Salmonellen-, Campylobacter-, Shigellen- oder E. Coli-Lebensmittelvergiftung",
     "Salmonella, Campylobacter, Shigella or E. Coli food poisoning",
     "Intoxication alimentaire à Salmonella, Campylobacter, Shigella ou E. Coli",
     "Intoxicación alimentaria por Salmonella, Campylobacter, Shigella o E. Coli"),
    (4, "parasites", "Parasitäre Infektionen",
     "Any parasitic infection",
     "Infections parasitaires",
     "Infecciones parasitarias"),
    (5, "ent", "Hals-Nasen-Ohren-Infektionen",
     "Ear, nose or throat infections",
     "Infections ORL (oreilles, nez, gorge)",
     "Infecciones de oídos, nariz o garganta"),
    (6, "skin", "Hauterkrankungen oder offene, eitrige Wunden",
     "Skin rashes or open, festering wounds",
     "Maladies cutanées ou plaies ouvertes et purulentes",
     "Enfermedades cutáneas o heridas abiertas y purulentas"),
]

# FR/ES backfill for existing installs whose questions predate FR/ES columns.
HQ_FR_ES_BACKFILL = {
    "flu": ("Maladies grippales (toux, rhume, fièvre)",
            "Enfermedades gripales (tos, resfriado, fiebre)"),
    "diarrhea": ("Diarrhée ou vomissements", "Diarrea o vómitos"),
    "food_poisoning": ("Intoxication alimentaire à Salmonella, Campylobacter, Shigella ou E. Coli",
                       "Intoxicación alimentaria por Salmonella, Campylobacter, Shigella o E. Coli"),
    "parasites": ("Infections parasitaires", "Infecciones parasitarias"),
    "ent": ("Infections ORL (oreilles, nez, gorge)", "Infecciones de oídos, nariz o garganta"),
    "skin": ("Maladies cutanées ou plaies ouvertes et purulentes",
             "Enfermedades cutáneas o heridas abiertas y purulentas"),
}

# --- App-wide branding / kiosk defaults ------------------------------------
DEFAULT_SETTINGS = {
    "company_name": "GateKeeper",
    "accent": "blau",
    "retention_days": 90,
    "kiosk_backdrop": "hell",
    "collect_plate": True,
    "auto_return_seconds": 20,
    "idle_timeout_seconds": 120,
}

# --- Accent palettes (mirror of the frontend theme.mjs) --------------------
ACCENTS = ("blau", "gruen", "violett", "anthrazit", "bernstein")
BACKDROPS = ("hell", "anthrazit", "schlicht")


def _L(de, en, fr, es):
    return {"de": de, "en": en, "fr": fr, "es": es}


# --- Info categories (7) ---------------------------------------------------
# type 'dir' -> uses `entries`; type 'art' -> uses `body` (Markdown, "## head")
INFO_CATEGORIES = [
    {
        "key": "notruf",
        "type": "dir",
        "icon": "phone",
        "accent": "#d64545",
        "position": 1,
        "title": _L("Notrufnummern", "Emergency numbers", "Numéros d’urgence", "Números de emergencia"),
        "entries": [
            {"label": _L("Notruf (Feuerwehr / Rettung)", "Emergency (fire / ambulance)",
                         "Urgences (pompiers / SAMU)", "Emergencias (bomberos / ambulancia)"), "value": "112"},
            {"label": _L("Polizei", "Police", "Police", "Policía"), "value": "110"},
            {"label": _L("Werkschutz / Sicherheit", "Site security", "Sécurité du site", "Seguridad del centro"),
             "value": "+49 30 555 0 110"},
            {"label": _L("Betrieblicher Ersthelfer", "Company first aider", "Secouriste interne", "Primeros auxilios"),
             "value": "Intern 4747"},
        ],
    },
    {
        "key": "kontakte",
        "type": "dir",
        "icon": "user",
        "accent": "#2f6fed",
        "position": 2,
        "title": _L("Kontakte", "Contacts", "Contacts", "Contactos"),
        "entries": [
            {"label": _L("Empfang", "Reception", "Accueil", "Recepción"), "value": "+49 30 555 0 100"},
            {"label": _L("Facility Management", "Facility management", "Services généraux", "Mantenimiento"),
             "value": "+49 30 555 0 200"},
            {"label": _L("Datenschutzbeauftragter", "Data Protection Officer",
                         "Délégué à la protection des données", "Delegado de protección de datos"),
             "value": "datenschutz@example.com"},
            {"label": _L("IT-Support", "IT support", "Support informatique", "Soporte TI"),
             "value": "+49 30 555 0 300"},
        ],
    },
    {
        "key": "notfall",
        "type": "art",
        "icon": "exit",
        "accent": "#e08a1e",
        "position": 3,
        "title": _L("Notfallpläne", "Emergency plans", "Plans d’urgence", "Planes de emergencia"),
        "body": _L(
            "Im Brandfall: Ruhe bewahren und den nächstgelegenen Notausgang nutzen.\n"
            "Keinen Aufzug benutzen.\nSammelplatz: Parkplatz P2 vor dem Haupteingang.\n"
            "Anweisungen der Evakuierungshelfer (gelbe Warnweste) befolgen.",
            "In case of fire: stay calm and use the nearest emergency exit.\n"
            "Do not use the lift.\nAssembly point: car park P2 in front of the main entrance.\n"
            "Follow the instructions of the evacuation marshals (yellow vests).",
            "En cas d’incendie : gardez votre calme et utilisez la sortie de secours la plus proche.\n"
            "N’utilisez pas l’ascenseur.\nPoint de rassemblement : parking P2 devant l’entrée principale.\n"
            "Suivez les instructions des guides d’évacuation (gilets jaunes).",
            "En caso de incendio: mantenga la calma y use la salida de emergencia más cercana.\n"
            "No use el ascensor.\nPunto de encuentro: aparcamiento P2 frente a la entrada principal.\n"
            "Siga las instrucciones de los responsables de evacuación (chalecos amarillos).",
        ),
    },
    {
        "key": "hygiene",
        "type": "art",
        "icon": "drop",
        "accent": "#1f9d6b",
        "position": 4,
        "title": _L("Hygieneregeln", "Hygiene rules", "Règles d’hygiène", "Normas de higiene"),
        "body": _L(
            "Sollten Sie eine oder mehrere der Gesundheitsfragen mit „Ja“ beantwortet haben, dürfen Sie den "
            "Produktionsbereich nur in Begleitung bzw. nach Rücksprache mit der besuchten Person betreten.\n"
            "Unabhängig davon bitten wir Sie, folgende Hygieneregeln zu befolgen:\n"
            "## Hygieneregeln\n"
            "Für die Dauer Ihres Aufenthaltes in den Produktionsräumen ist der bereitgestellte Kittel zu tragen.\n"
            "Vor Betreten der Produktionsräume bitte die Hände waschen und desinfizieren sowie die vorgesehene "
            "Kopfbedeckung (Haarnetz) anlegen.\n"
            "Bitte legen Sie Uhren und jeglichen Schmuck ab.\n"
            "Bitte rauchen Sie nur in den gekennzeichneten Bereichen.\n"
            "Bitte essen oder trinken Sie nicht in den Produktionsräumen (einschließlich Kaugummi).\n"
            "Bitte tragen Sie keinen Nagellack bzw. keine Kunstnägel.\n"
            "Schnittverletzungen bitte mit einem Spezial-Pflaster versorgen (bei Bedarf an der Rezeption erfragen).",
            "If you answered “Yes” to one or more of the health questions, you may only enter the production area "
            "when accompanied or after consulting the person you are visiting.\n"
            "Regardless, please observe the following hygiene rules:\n"
            "## Hygiene rules\n"
            "Wear the provided coat for the duration of your stay in the production rooms.\n"
            "Before entering the production rooms, wash and disinfect your hands and put on the designated head "
            "covering (hairnet).\n"
            "Please remove watches and all jewellery.\n"
            "Please smoke only in the marked areas.\n"
            "Please do not eat or drink in the production rooms (including chewing gum).\n"
            "Please do not wear nail polish or artificial nails.\n"
            "Please cover any cuts with a special plaster (ask at reception if needed).",
            "Si vous avez répondu « Oui » à une ou plusieurs questions de santé, vous ne pouvez accéder à la zone "
            "de production qu’accompagné(e) ou après accord de la personne visitée.\n"
            "Indépendamment de cela, merci de respecter les règles d’hygiène suivantes :\n"
            "## Règles d’hygiène\n"
            "Pendant toute la durée de votre présence dans les salles de production, portez la blouse fournie.\n"
            "Avant d’entrer, lavez et désinfectez-vous les mains et mettez la coiffe prévue (charlotte).\n"
            "Veuillez retirer montres et bijoux.\n"
            "Ne fumez que dans les zones signalées.\n"
            "Ne mangez et ne buvez pas dans les salles de production (chewing-gum compris).\n"
            "Ne portez pas de vernis ni de faux ongles.\n"
            "Couvrez toute coupure avec un pansement spécial (à demander à l’accueil si besoin).",
            "Si ha respondido «Sí» a una o varias preguntas de salud, solo podrá acceder a la zona de producción "
            "acompañado/a o tras consultarlo con la persona visitada.\n"
            "Al margen de ello, le rogamos que cumpla las siguientes normas de higiene:\n"
            "## Normas de higiene\n"
            "Durante su estancia en las salas de producción debe llevar la bata facilitada.\n"
            "Antes de entrar, lávese y desinféctese las manos y póngase el gorro previsto (redecilla).\n"
            "Quítese relojes y cualquier joya.\n"
            "Fume únicamente en las zonas señalizadas.\n"
            "No coma ni beba en las salas de producción (incluido chicle).\n"
            "No lleve esmalte de uñas ni uñas postizas.\n"
            "Cubra cualquier corte con un apósito especial (solicítelo en recepción si lo necesita).",
        ),
    },
    {
        "key": "sicherheit",
        "type": "art",
        "icon": "shield",
        "accent": "#5b6b85",
        "position": 5,
        "title": _L("Sicherheits- & Verhaltenshinweise", "Safety & conduct",
                    "Sécurité & comportement", "Seguridad y conducta"),
        "body": _L(
            "Wir heißen Sie herzlich willkommen. Im Sinne der Werksicherheit, Hygiene und des Umweltschutzes bitten "
            "wir Sie, während Ihres Aufenthaltes folgende Punkte streng zu beachten:\n"
            "## Rauchen\nAuf dem gesamten Werksgelände gilt ein absolutes Rauchverbot (auch E-Zigaretten). Rauchen "
            "ist nur in den ausgewiesenen Raucherzonen erlaubt (siehe Hinweisschilder).\n"
            "## Handys\nHandys dürfen nur auf dem Freigelände sowie in Büro- und Verwaltungsgebäuden eingeschaltet "
            "sein. Fotohandys sind im Werk untersagt.\n"
            "## Fotografieren\nDas Fotografieren innerhalb der Betriebsgebäude ist nur nach Genehmigung durch die "
            "Begleitperson / den Abteilungsleiter zulässig.\n"
            "## Schmuck\nDas Tragen von Uhren, Halsketten, Ohrringen und Armbändern ist im gesamten "
            "Produktionsbereich nicht gestattet.\n"
            "## Produktionsräume\nIn den Produktionsräumen darf weder gegessen noch getrunken werden. Türen und Tore "
            "sind stets geschlossen zu halten. Bitte gehen Sie nur auf direktem Weg zum vereinbarten Einsatzort. Im "
            "gesamten Produktionsbereich (Hygienezone) ist eine Kopfbedeckung (Haarnetz) vorgeschrieben; Spender "
            "finden Sie an den Eingängen.\n"
            "## Feueralarm\nBei Feueralarm (Sirene) die Gebäude sofort verlassen und die Sammelstellen aufsuchen "
            "(siehe Flucht- und Rettungspläne).\n"
            "## Krankheiten\nBesucher mit meldepflichtigen Krankheiten gem. IfSG §42 dürfen das Produktionsgebäude "
            "nicht betreten.\nVielen Dank – Die Betriebsleitung",
            "A warm welcome. For the sake of plant safety, hygiene and environmental protection, please strictly "
            "observe the following points during your visit:\n"
            "## Smoking\nSmoking is strictly prohibited across the entire site (including e-cigarettes). Smoking is "
            "only allowed in the designated smoking zones (see signs).\n"
            "## Mobile phones\nMobile phones may only be switched on outdoors and in office/administration buildings. "
            "Camera phones are prohibited in the plant.\n"
            "## Photography\nPhotography inside the operating buildings is only permitted with approval from your "
            "escort / the department manager.\n"
            "## Jewellery\nWearing watches, necklaces, earrings and bracelets is not permitted anywhere in the "
            "production area.\n"
            "## Production rooms\nEating and drinking are not allowed in the production rooms. Keep doors and gates "
            "closed at all times. Please go directly to your agreed work location. A head covering (hairnet) is "
            "mandatory throughout the production area (hygiene zone); dispensers are located at the entrances.\n"
            "## Fire alarm\nIn the event of a fire alarm (siren), leave the buildings immediately and go to the "
            "assembly points (see posted escape and rescue plans).\n"
            "## Illnesses\nVisitors with notifiable illnesses under the German Infection Protection Act (IfSG) §42 "
            "may not enter the production building.\nThank you – Plant Management",
            "Bienvenue. Pour la sécurité du site, l’hygiène et la protection de l’environnement, merci de respecter "
            "strictement les points suivants pendant votre visite :\n"
            "## Tabac\nIl est strictement interdit de fumer sur l’ensemble du site (cigarettes électroniques "
            "comprises). Le tabac n’est autorisé que dans les zones fumeurs signalées.\n"
            "## Téléphones portables\nLes téléphones ne peuvent être allumés qu’à l’extérieur et dans les bâtiments "
            "administratifs. Les téléphones avec appareil photo sont interdits dans l’usine.\n"
            "## Photographie\nLa photographie à l’intérieur des bâtiments n’est autorisée qu’avec l’accord de "
            "l’accompagnateur / du chef de service.\n"
            "## Bijoux\nLe port de montres, colliers, boucles d’oreilles et bracelets est interdit dans toute la "
            "zone de production.\n"
            "## Salles de production\nIl est interdit de manger et de boire dans les salles de production. Gardez "
            "les portes fermées en permanence. Rendez-vous directement au lieu convenu. Une coiffe (charlotte) est "
            "obligatoire dans toute la zone de production ; des distributeurs sont aux entrées.\n"
            "## Alarme incendie\nEn cas d’alarme (sirène), quittez immédiatement les bâtiments et rejoignez les "
            "points de rassemblement (voir plans d’évacuation).\n"
            "## Maladies\nLes visiteurs atteints de maladies à déclaration obligatoire (IfSG §42) ne peuvent entrer "
            "dans le bâtiment de production.\nMerci – La Direction",
            "Le damos la bienvenida. Por la seguridad del centro, la higiene y la protección del medio ambiente, le "
            "rogamos que respete estrictamente los siguientes puntos durante su visita:\n"
            "## Tabaco\nEstá totalmente prohibido fumar en todo el recinto (incluidos cigarrillos electrónicos). "
            "Solo se permite fumar en las zonas señalizadas.\n"
            "## Teléfonos móviles\nLos móviles solo pueden estar encendidos al aire libre y en edificios de "
            "oficinas/administración. Los móviles con cámara están prohibidos en la planta.\n"
            "## Fotografía\nFotografiar dentro de los edificios solo se permite con autorización del acompañante / "
            "jefe de departamento.\n"
            "## Joyas\nNo se permite llevar relojes, collares, pendientes ni pulseras en toda la zona de producción.\n"
            "## Salas de producción\nNo se puede comer ni beber en las salas de producción. Mantenga puertas y "
            "portones siempre cerrados. Diríjase directamente al lugar acordado. En toda la zona de producción "
            "(zona de higiene) es obligatorio un gorro (redecilla); hay dispensadores en las entradas.\n"
            "## Alarma de incendio\nEn caso de alarma (sirena), abandone los edificios de inmediato y diríjase a los "
            "puntos de encuentro (véanse los planos de evacuación).\n"
            "## Enfermedades\nLos visitantes con enfermedades de declaración obligatoria (IfSG §42) no pueden entrar "
            "en el edificio de producción.\nGracias – La Dirección",
        ),
    },
    {
        "key": "besucher",
        "type": "art",
        "icon": "info",
        "accent": "#2f6fed",
        "position": 6,
        "title": _L("Besucherinformationen", "Visitor information",
                    "Informations visiteurs", "Información para visitantes"),
        "body": _L(
            "WLAN: „Guest“, Passwort am Empfang.\nBesucherparkplätze: P1 (beschildert).\n"
            "Öffnungszeiten Empfang: Mo–Fr 7:30–18:00 Uhr.\nGetränke stehen im Wartebereich bereit.",
            "Wi-Fi: “Guest”, password at reception.\nVisitor parking: P1 (signposted).\n"
            "Reception hours: Mon–Fri 7:30–18:00.\nRefreshments are available in the waiting area.",
            "Wi-Fi : « Guest », mot de passe à l’accueil.\nParking visiteurs : P1 (signalé).\n"
            "Horaires de l’accueil : lun–ven 7h30–18h00.\nDes boissons sont à disposition dans l’espace d’attente.",
            "Wi-Fi: «Guest», contraseña en recepción.\nAparcamiento de visitantes: P1 (señalizado).\n"
            "Horario de recepción: lun–vie 7:30–18:00.\nHay bebidas disponibles en la sala de espera.",
        ),
    },
    {
        "key": "datenschutz",
        "type": "art",
        "icon": "lock",
        "accent": "#7c5cd6",
        "position": 7,
        "title": _L("Datenschutzerklärung", "Privacy policy",
                    "Politique de confidentialité", "Política de privacidad"),
        "body": _L(
            "Ihre personenbezogenen Daten (Name, Firma, Ansprechpartner, Besuchszeiten) werden ausschließlich zum "
            "Zweck der Besucherdokumentation und Gebäudesicherheit erfasst und verarbeitet.\n"
            "Die Daten werden nach Ablauf der gesetzlichen Aufbewahrungsfrist automatisch gelöscht.\n"
            "Sie haben das Recht auf Auskunft, Berichtigung und Löschung Ihrer Daten gemäß DSGVO Art. 15–17.",
            "Your personal data (name, company, host, visit times) is collected and processed solely for the "
            "purpose of visitor documentation and building security.\n"
            "The data is automatically deleted after the statutory retention period.\n"
            "You have the right to access, rectification and erasure of your data in accordance with GDPR Art. 15–17.",
            "Vos données personnelles (nom, société, personne visitée, heures de visite) sont collectées et traitées "
            "uniquement à des fins de documentation des visiteurs et de sécurité du bâtiment.\n"
            "Les données sont automatiquement supprimées à l’expiration du délai légal de conservation.\n"
            "Vous disposez d’un droit d’accès, de rectification et d’effacement de vos données conformément aux "
            "art. 15-17 du RGPD.",
            "Sus datos personales (nombre, empresa, persona de contacto, horas de visita) se recopilan y tratan "
            "únicamente con fines de documentación de visitantes y seguridad del edificio.\n"
            "Los datos se eliminan automáticamente una vez transcurrido el plazo legal de conservación.\n"
            "Tiene derecho de acceso, rectificación y supresión de sus datos conforme a los art. 15-17 del RGPD.",
        ),
    },
]

# Map old StaticPage slugs -> new InfoCategory keys (for content migration).
STATICPAGE_SLUG_TO_KEY = {
    "emergency_numbers": "notruf",
    "emergency_contacts": "kontakte",
    "emergency_plans": "notfall",
    "hygiene_rules": "hygiene",
    "safety_conduct": "sicherheit",
    "visitor_info": "besucher",
}
