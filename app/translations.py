"""UI string translations for GateKeeper (DE/EN/FR/ES)."""

# All translatable UI strings keyed by identifier.
# Each key maps to {lang_code: translated_string}.
# German (de) is the primary/fallback language.

TRANSLATIONS = {
    # --- Common ---
    "app_name": {"de": "GateKeeper", "en": "GateKeeper", "fr": "GateKeeper", "es": "GateKeeper"},
    "visitor_mgmt": {"de": "Besuchermanagement", "en": "Visitor Management", "fr": "Gestion des visiteurs", "es": "Gestión de visitantes"},

    # --- Navigation / Sidebar ---
    "information": {"de": "Informationen", "en": "Information", "fr": "Informations", "es": "Información"},
    "check_in": {"de": "Einchecken", "en": "Check In", "fr": "Enregistrement", "es": "Registro de entrada"},
    "check_out": {"de": "Auschecken", "en": "Check Out", "fr": "Départ", "es": "Registro de salida"},
    "contacts": {"de": "Kontakte", "en": "Contacts", "fr": "Contacts", "es": "Contactos"},
    "emergency_plans": {"de": "Notfallpläne", "en": "Emergency Plans", "fr": "Plans d'urgence", "es": "Planes de emergencia"},
    "emergency_numbers": {"de": "Notrufnummern", "en": "Emergency Numbers", "fr": "Numéros d'urgence", "es": "Números de emergencia"},
    "visitor_info": {"de": "Besucherinformationen", "en": "Visitor Information", "fr": "Informations visiteurs", "es": "Información para visitantes"},
    "hygiene_rules": {"de": "Hygieneregeln", "en": "Hygiene Rules", "fr": "Règles d'hygiène", "es": "Normas de higiene"},
    "safety_conduct": {"de": "Sicherheits-/Verhaltenshinweise", "en": "Rules of safety / conduct", "fr": "Règles de sécurité / conduite", "es": "Normas de seguridad / conducta"},

    # --- Home page ---
    "welcome": {"de": "Willkommen", "en": "Welcome", "fr": "Bienvenue", "es": "Bienvenido"},
    "please_checkin_checkout": {"de": "Bitte melden Sie sich an oder ab", "en": "Please check in or check out", "fr": "Veuillez vous enregistrer ou partir", "es": "Por favor, regístrese o salga"},
    "i_am_arriving": {"de": "Ich komme an", "en": "I'm arriving", "fr": "J'arrive", "es": "Estoy llegando"},
    "i_am_leaving": {"de": "Ich gehe", "en": "I'm leaving", "fr": "Je pars", "es": "Me voy"},

    # --- Check-in form ---
    "fill_form": {"de": "Bitte füllen Sie das Formular aus", "en": "Please fill in the form", "fr": "Veuillez remplir le formulaire", "es": "Por favor complete el formulario"},
    "first_name": {"de": "Vorname", "en": "First Name", "fr": "Prénom", "es": "Nombre"},
    "last_name": {"de": "Nachname", "en": "Last Name", "fr": "Nom", "es": "Apellido"},
    "company": {"de": "Firma", "en": "Company", "fr": "Entreprise", "es": "Empresa"},
    "contact_person": {"de": "Ansprechpartner", "en": "Contact Person", "fr": "Personne de contact", "es": "Persona de contacto"},
    "who_visiting": {"de": "Wen besuchen Sie?", "en": "Who are you visiting?", "fr": "Qui visitez-vous ?", "es": "¿A quién visita?"},
    "license_plate": {"de": "KFZ-Kennzeichen", "en": "License Plate", "fr": "Plaque d'immatriculation", "es": "Matrícula"},
    "license_plate_example": {"de": "z.B. M-AB 1234", "en": "e.g. M-AB 1234", "fr": "ex. M-AB 1234", "es": "ej. M-AB 1234"},
    "health_questionnaire": {"de": "Gesundheitsfragebogen", "en": "Health Questionnaire", "fr": "Questionnaire de santé", "es": "Cuestionario de salud"},
    "health_question_intro": {"de": "Haben Sie in den letzten 7 Tagen an folgenden Krankheiten gelitten?", "en": "In the last 7 days have you suffered from any of the following conditions?", "fr": "Au cours des 7 derniers jours, avez-vous souffert de l'une des affections suivantes ?", "es": "¿En los últimos 7 días ha padecido alguna de las siguientes enfermedades?"},
    "yes": {"de": "Ja", "en": "Yes", "fr": "Oui", "es": "Sí"},
    "no": {"de": "Nein", "en": "No", "fr": "Non", "es": "No"},
    "answer_all_questions": {"de": "Bitte beantworten Sie alle Fragen.", "en": "Please answer all questions.", "fr": "Veuillez répondre à toutes les questions.", "es": "Por favor responda todas las preguntas."},

    # --- DSGVO / Privacy ---
    "privacy_agree_de": "Ich stimme der <a href=\"#\" onclick=\"event.preventDefault(); document.getElementById('dsgvoModal').showModal();\">Datenschutzerklärung</a> zu und bin mit der Erfassung meiner Daten einverstanden. *",
    "privacy_agree_en": "I agree to the <a href=\"#\" onclick=\"event.preventDefault(); document.getElementById('dsgvoModal').showModal();\">privacy policy</a> and consent to the processing of my data. *",
    "privacy_agree_fr": "J'accepte la <a href=\"#\" onclick=\"event.preventDefault(); document.getElementById('dsgvoModal').showModal();\">politique de confidentialité</a> et consens au traitement de mes données. *",
    "privacy_agree_es": "Acepto la <a href=\"#\" onclick=\"event.preventDefault(); document.getElementById('dsgvoModal').showModal();\">política de privacidad</a> y consiento el tratamiento de mis datos. *",

    "privacy_policy": {"de": "Datenschutzerklärung", "en": "Privacy Policy", "fr": "Politique de confidentialité", "es": "Política de privacidad"},
    "privacy_text_de": "Ihre personenbezogenen Daten (Name, Firma, Ansprechpartner, Besuchszeiten) werden ausschließlich zum Zweck der Besucherdokumentation und Gebäudesicherheit erfasst und verarbeitet. Die Daten werden nach Ablauf der gesetzlichen Aufbewahrungsfrist automatisch gelöscht. Sie haben das Recht auf Auskunft, Berichtigung und Löschung Ihrer Daten gemäß DSGVO Art. 15-17.",
    "privacy_text_en": "Your personal data (name, company, contact person, visit times) is collected and processed solely for visitor documentation and building security purposes. Data will be automatically deleted after the statutory retention period. You have the right to access, rectify, and delete your data according to GDPR Articles 15-17.",
    "privacy_text_fr": "Vos données personnelles (nom, entreprise, personne de contact, horaires de visite) sont collectées et traitées exclusivement à des fins de documentation des visiteurs et de sécurité du bâtiment. Les données seront automatiquement supprimées après la période de conservation légale. Vous avez le droit d'accéder, de rectifier et de supprimer vos données conformément aux articles 15 à 17 du RGPD.",
    "privacy_text_es": "Sus datos personales (nombre, empresa, persona de contacto, horarios de visita) se recopilan y procesan exclusivamente con fines de documentación de visitantes y seguridad del edificio. Los datos se eliminarán automáticamente una vez transcurrido el plazo legal de conservación. Tiene derecho a acceder, rectificar y suprimir sus datos conforme a los artículos 15 a 17 del RGPD.",

    # --- Hygiene consent ---
    "hygiene_confirm_de": "Hiermit bestätige ich, dass ich die <a href=\"{url}\" target=\"_blank\">Hygieneregeln</a> gelesen und verstanden habe und die Fragen korrekt beantwortet wurden. *",
    "hygiene_confirm_en": "I confirm that the information I have given is correct and I have read and understood the <a href=\"{url}\" target=\"_blank\">hygiene rules</a>. *",
    "hygiene_confirm_fr": "Je confirme que les informations fournies sont correctes et que j'ai lu et compris les <a href=\"{url}\" target=\"_blank\">règles d'hygiène</a>. *",
    "hygiene_confirm_es": "Confirmo que la información proporcionada es correcta y que he leído y comprendido las <a href=\"{url}\" target=\"_blank\">normas de higiene</a>. *",

    # --- Safety consent ---
    "safety_confirm_de": "Ich habe die <a href=\"{url}\" target=\"_blank\">Sicherheits-/Verhaltenshinweise</a> gelesen und bestätige deren Einhaltung. *",
    "safety_confirm_en": "I have read the <a href=\"{url}\" target=\"_blank\">rules of safety / conduct</a> and confirm that I will comply with them. *",
    "safety_confirm_fr": "J'ai lu les <a href=\"{url}\" target=\"_blank\">règles de sécurité / conduite</a> et confirme que je les respecterai. *",
    "safety_confirm_es": "He leído las <a href=\"{url}\" target=\"_blank\">normas de seguridad / conducta</a> y confirmo que las cumpliré. *",

    # --- Signature ---
    "signature": {"de": "Unterschrift", "en": "Signature", "fr": "Signature", "es": "Firma"},
    "clear": {"de": "Löschen", "en": "Clear", "fr": "Effacer", "es": "Borrar"},
    "sign_hint": {"de": "Bitte unterschreiben Sie mit dem Finger oder Stift", "en": "Please sign with your finger or stylus", "fr": "Veuillez signer avec le doigt ou un stylet", "es": "Por favor firme con el dedo o un lápiz"},
    "sign_required": {"de": "Bitte unterschreiben Sie das Formular.", "en": "Please sign the form.", "fr": "Veuillez signer le formulaire.", "es": "Por favor firme el formulario."},

    # --- Buttons ---
    "cancel": {"de": "Abbrechen", "en": "Cancel", "fr": "Annuler", "es": "Cancelar"},
    "close": {"de": "Schließen", "en": "Close", "fr": "Fermer", "es": "Cerrar"},
    "back_to_home": {"de": "Zur Startseite", "en": "Back to Home", "fr": "Retour à l'accueil", "es": "Volver al inicio"},
    "back_to_checkin": {"de": "Zurück zum Einchecken", "en": "Back to Check In", "fr": "Retour à l'enregistrement", "es": "Volver al registro"},

    # --- Check-in success ---
    "checkin_success": {"de": "Erfolgreich eingecheckt!", "en": "Successfully Checked In!", "fr": "Enregistrement réussi !", "es": "¡Registro exitoso!"},
    "checkin_success_title": {"de": "Erfolgreich eingecheckt", "en": "Checked In", "fr": "Enregistré", "es": "Registrado"},
    "your_pin": {"de": "Ihr persönlicher PIN für das Auschecken:", "en": "Your personal PIN for checking out:", "fr": "Votre code PIN personnel pour le départ :", "es": "Su PIN personal para el registro de salida:"},
    "remember_pin": {"de": "Bitte merken Sie sich diesen PIN oder fotografieren Sie ihn ab.", "en": "Please remember this PIN or take a photo.", "fr": "Veuillez mémoriser ce code PIN ou le photographier.", "es": "Por favor recuerde este PIN o tome una foto."},
    "auto_redirect_in": {"de": "Automatische Weiterleitung in", "en": "Auto-redirect in", "fr": "Redirection automatique dans", "es": "Redirección automática en"},
    "seconds": {"de": "Sekunden", "en": "seconds", "fr": "secondes", "es": "segundos"},

    # --- Check-out ---
    "enter_pin": {"de": "Bitte geben Sie Ihren 4-stelligen PIN ein", "en": "Please enter your 4-digit PIN", "fr": "Veuillez entrer votre code PIN à 4 chiffres", "es": "Por favor ingrese su PIN de 4 dígitos"},
    "checkout_title": {"de": "Ausgecheckt", "en": "Checked Out", "fr": "Départ effectué", "es": "Salida registrada"},
    "too_many_attempts": {"de": "Zu viele Versuche. Bitte warten Sie 2 Minuten.", "en": "Too many attempts. Please wait 2 minutes.", "fr": "Trop de tentatives. Veuillez patienter 2 minutes.", "es": "Demasiados intentos. Por favor espere 2 minutos."},
    "invalid_pin": {"de": "Ungültiger PIN. Bitte versuchen Sie es erneut.", "en": "Invalid PIN. Please try again.", "fr": "Code PIN invalide. Veuillez réessayer.", "es": "PIN inválido. Por favor intente de nuevo."},

    # --- Check-out success ---
    "goodbye": {"de": "Auf Wiedersehen!", "en": "Goodbye!", "fr": "Au revoir !", "es": "¡Adiós!"},
    "checkout_success_msg": {"de": "Sie wurden erfolgreich ausgecheckt. Haben Sie einen guten Tag!", "en": "You have been successfully checked out. Have a great day!", "fr": "Vous avez été enregistré(e) avec succès. Bonne journée !", "es": "Se ha registrado su salida exitosamente. ¡Que tenga un buen día!"},

    # --- Health warning modal ---
    "access_denied": {"de": "Zugang nicht möglich", "en": "Access not permitted", "fr": "Accès non autorisé", "es": "Acceso no permitido"},
    "health_blocked_de": "Aufgrund Ihrer Angaben im Gesundheitsfragebogen kann der Zutritt zum Betrieb leider nicht gestattet werden.<br><br><strong>Bitte wenden Sie sich an einen Mitarbeiter.</strong>",
    "health_blocked_en": "Based on your answers in the health questionnaire, access to the premises cannot be granted at this time.<br><br><strong>Please contact a member of staff.</strong>",
    "health_blocked_fr": "En raison de vos réponses au questionnaire de santé, l'accès aux locaux ne peut malheureusement pas être autorisé pour le moment.<br><br><strong>Veuillez contacter un membre du personnel.</strong>",
    "health_blocked_es": "Según sus respuestas en el cuestionario de salud, no se puede conceder el acceso a las instalaciones en este momento.<br><br><strong>Por favor contacte a un miembro del personal.</strong>",
    # --- Admin: Dashboard ---
    "admin_dashboard": {"de": "Besucher-Dashboard", "en": "Visitor Dashboard", "fr": "Tableau de bord visiteurs", "es": "Panel de visitantes"},
    "currently_on_site": {"de": "Aktuell vor Ort", "en": "Currently on site", "fr": "Actuellement sur place", "es": "Actualmente en el sitio"},
    "emergency_send": {"de": "Notfall-Liste senden", "en": "Send emergency list", "fr": "Envoyer liste d'urgence", "es": "Enviar lista de emergencia"},
    "emergency_confirm": {"de": "Notfall-Evakuierungsliste jetzt an alle Notfall-Kontakte senden?", "en": "Send emergency evacuation list to all emergency contacts now?", "fr": "Envoyer la liste d'évacuation d'urgence à tous les contacts maintenant ?", "es": "¿Enviar la lista de evacuación de emergencia a todos los contactos ahora?"},
    "health_questions": {"de": "Gesundheitsfragen", "en": "Health Questions", "fr": "Questions de santé", "es": "Preguntas de salud"},
    "manage_pages": {"de": "Seiten verwalten", "en": "Manage Pages", "fr": "Gérer les pages", "es": "Gestionar páginas"},
    "email_smtp": {"de": "E-Mail / SMTP", "en": "Email / SMTP", "fr": "E-mail / SMTP", "es": "Correo / SMTP"},
    "logout": {"de": "Abmelden", "en": "Logout", "fr": "Déconnexion", "es": "Cerrar sesión"},
    "filter_from": {"de": "Von", "en": "From", "fr": "Du", "es": "Desde"},
    "filter_to": {"de": "Bis", "en": "To", "fr": "Au", "es": "Hasta"},
    "filter_status": {"de": "Status", "en": "Status", "fr": "Statut", "es": "Estado"},
    "filter_search": {"de": "Suche", "en": "Search", "fr": "Recherche", "es": "Búsqueda"},
    "filter_btn": {"de": "Filtern", "en": "Filter", "fr": "Filtrer", "es": "Filtrar"},
    "filter_reset": {"de": "Zurücksetzen", "en": "Reset", "fr": "Réinitialiser", "es": "Restablecer"},
    "results": {"de": "Ergebnis(se)", "en": "result(s)", "fr": "résultat(s)", "es": "resultado(s)"},
    "csv_export": {"de": "CSV Export", "en": "CSV Export", "fr": "Export CSV", "es": "Exportar CSV"},
    "search_placeholder": {"de": "Name, Firma...", "en": "Name, company...", "fr": "Nom, entreprise...", "es": "Nombre, empresa..."},
    "th_name": {"de": "Name", "en": "Name", "fr": "Nom", "es": "Nombre"},
    "th_company": {"de": "Firma", "en": "Company", "fr": "Entreprise", "es": "Empresa"},
    "th_contact": {"de": "Ansprechpartner", "en": "Contact", "fr": "Contact", "es": "Contacto"},
    "th_plate": {"de": "KFZ", "en": "Plate", "fr": "Plaque", "es": "Matrícula"},
    "th_arrival": {"de": "Ankunft", "en": "Arrival", "fr": "Arrivée", "es": "Llegada"},
    "th_departure": {"de": "Abfahrt", "en": "Departure", "fr": "Départ", "es": "Salida"},
    "th_pin": {"de": "PIN", "en": "PIN", "fr": "PIN", "es": "PIN"},
    "th_signature": {"de": "Signatur", "en": "Signature", "fr": "Signature", "es": "Firma"},
    "th_questionnaire": {"de": "Fragebogen", "en": "Questionnaire", "fr": "Questionnaire", "es": "Cuestionario"},
    "on_site": {"de": "Vor Ort", "en": "On site", "fr": "Sur place", "es": "En el sitio"},
    "departed": {"de": "Abgereist", "en": "Departed", "fr": "Parti", "es": "Salió"},
    "missed_checkout": {"de": "Kein Checkout", "en": "No checkout", "fr": "Pas de départ", "es": "Sin salida"},
    "no_visitors_found": {"de": "Keine Besucher gefunden.", "en": "No visitors found.", "fr": "Aucun visiteur trouvé.", "es": "No se encontraron visitantes."},
    "show_signature": {"de": "Anzeigen", "en": "Show", "fr": "Afficher", "es": "Mostrar"},
    "sig_label": {"de": "Unterschrift", "en": "Signature", "fr": "Signature", "es": "Firma"},
    "no_sig": {"de": "Keine", "en": "None", "fr": "Aucune", "es": "Ninguna"},
    "conspicuous": {"de": "Auffällig", "en": "Conspicuous", "fr": "Suspect", "es": "Sospechoso"},
    "ok": {"de": "OK", "en": "OK", "fr": "OK", "es": "OK"},
    "questionnaire_label": {"de": "Fragebogen", "en": "Questionnaire", "fr": "Questionnaire", "es": "Cuestionario"},
    "show_pin": {"de": "PIN anzeigen", "en": "Show PIN", "fr": "Afficher PIN", "es": "Mostrar PIN"},

    # --- Admin: Filter status choices ---
    "status_all": {"de": "Alle", "en": "All", "fr": "Tous", "es": "Todos"},
    "status_on_site": {"de": "Vor Ort", "en": "On site", "fr": "Sur place", "es": "En el sitio"},
    "status_departed": {"de": "Abgereist", "en": "Departed", "fr": "Parti(e)s", "es": "Salidos"},
    "status_missed": {"de": "Kein Checkout", "en": "No checkout", "fr": "Pas de départ", "es": "Sin salida"},

    # --- Admin: Login ---
    "admin_login": {"de": "Admin Login", "en": "Admin Login", "fr": "Connexion admin", "es": "Inicio de sesión admin"},
    "username": {"de": "Benutzername", "en": "Username", "fr": "Nom d'utilisateur", "es": "Nombre de usuario"},
    "password": {"de": "Passwort", "en": "Password", "fr": "Mot de passe", "es": "Contraseña"},
    "login_btn": {"de": "Anmelden", "en": "Login", "fr": "Se connecter", "es": "Iniciar sesión"},

    # --- Admin: Pages ---
    "manage_static_pages": {"de": "Statische Seiten verwalten", "en": "Manage Static Pages", "fr": "Gérer les pages statiques", "es": "Gestionar páginas estáticas"},
    "back_to_dashboard": {"de": "Zurück zum Dashboard", "en": "Back to Dashboard", "fr": "Retour au tableau de bord", "es": "Volver al panel"},
    "last_edited": {"de": "Zuletzt bearbeitet", "en": "Last edited", "fr": "Dernière modification", "es": "Última edición"},
    "edit": {"de": "Bearbeiten", "en": "Edit", "fr": "Modifier", "es": "Editar"},
    "save": {"de": "Speichern", "en": "Save", "fr": "Enregistrer", "es": "Guardar"},
    "back": {"de": "Zurück", "en": "Back", "fr": "Retour", "es": "Volver"},
    "edit_page_title": {"de": "Seite bearbeiten", "en": "Edit Page", "fr": "Modifier la page", "es": "Editar página"},
    "delete": {"de": "Löschen", "en": "Delete", "fr": "Supprimer", "es": "Eliminar"},

    # --- Admin: Health Questions ---
    "manage_health_questions": {"de": "Gesundheitsfragen verwalten", "en": "Manage Health Questions", "fr": "Gérer les questions de santé", "es": "Gestionar preguntas de salud"},
    "new_question": {"de": "Neue Frage", "en": "New Question", "fr": "Nouvelle question", "es": "Nueva pregunta"},
    "new_question_create": {"de": "Neue Frage erstellen", "en": "Create New Question", "fr": "Créer une nouvelle question", "es": "Crear nueva pregunta"},
    "edit_question": {"de": "Frage bearbeiten", "en": "Edit Question", "fr": "Modifier la question", "es": "Editar pregunta"},
    "question_hint": {"de": "Gesundheitsfragen werden im Check-in-Formular als Ja/Nein-Fragen angezeigt.", "en": "Health questions are displayed as Yes/No questions in the check-in form.", "fr": "Les questions de santé sont affichées comme questions Oui/Non dans le formulaire d'enregistrement.", "es": "Las preguntas de salud se muestran como preguntas Sí/No en el formulario de registro."},
    "position": {"de": "Pos.", "en": "Pos.", "fr": "Pos.", "es": "Pos."},
    "question_de": {"de": "Frage (DE)", "en": "Question (DE)", "fr": "Question (DE)", "es": "Pregunta (DE)"},
    "question_en": {"de": "Frage (EN)", "en": "Question (EN)", "fr": "Question (EN)", "es": "Pregunta (EN)"},
    "key": {"de": "Schlüssel", "en": "Key", "fr": "Clé", "es": "Clave"},
    "active": {"de": "Aktiv", "en": "Active", "fr": "Actif", "es": "Activo"},
    "inactive": {"de": "Inaktiv", "en": "Inactive", "fr": "Inactif", "es": "Inactivo"},
    "actions": {"de": "Aktionen", "en": "Actions", "fr": "Actions", "es": "Acciones"},
    "confirm_delete_question": {"de": "Frage wirklich löschen? Antworten bestehender Besucher gehen verloren.", "en": "Really delete this question? Existing visitor answers will be lost.", "fr": "Vraiment supprimer cette question ? Les réponses des visiteurs existants seront perdues.", "es": "¿Realmente eliminar esta pregunta? Las respuestas de los visitantes existentes se perderán."},
    "no_questions": {"de": "Keine Fragen definiert. Klicken Sie \"Neue Frage\" um zu beginnen.", "en": "No questions defined. Click \"New Question\" to start.", "fr": "Aucune question définie. Cliquez sur \"Nouvelle question\" pour commencer.", "es": "No hay preguntas definidas. Haga clic en \"Nueva pregunta\" para comenzar."},
    "question_note": {"de": "Änderungen an Fragen wirken sich nur auf neue Check-ins aus. Bestehende Besucher-Antworten bleiben unverändert. Inaktive Fragen werden nicht im Check-in-Formular angezeigt.", "en": "Changes to questions only affect new check-ins. Existing visitor answers remain unchanged. Inactive questions are not shown in the check-in form.", "fr": "Les modifications des questions n'affectent que les nouveaux enregistrements. Les réponses existantes restent inchangées. Les questions inactives ne sont pas affichées dans le formulaire.", "es": "Los cambios en las preguntas solo afectan los nuevos registros. Las respuestas existentes permanecen sin cambios. Las preguntas inactivas no se muestran en el formulario."},

    # --- Admin: SMTP ---
    "email_settings": {"de": "E-Mail Einstellungen (SMTP)", "en": "Email Settings (SMTP)", "fr": "Paramètres e-mail (SMTP)", "es": "Configuración de correo (SMTP)"},
}


def t(key, lang="de"):
    """Look up a translation. Returns the string for the given language.

    If the key maps to a dict, return the value for lang (fallback: de, then key itself).
    If the key maps to a string (language-suffixed keys like 'privacy_agree_de'),
    this is handled by the caller via t('privacy_agree_' + lang).
    """
    val = TRANSLATIONS.get(key)
    if val is None:
        return key  # missing key -> return key as-is for debugging
    if isinstance(val, dict):
        return val.get(lang, val.get("de", key))
    return val  # direct string (for lang-suffixed keys)
