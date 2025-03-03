// static/js/timer.js
document.addEventListener('DOMContentLoaded', function() {
    // Timer-Element finden
    const timerElement = document.getElementById('timer');
    const activeTimerElement = document.getElementById('active-timer');
    
    // Zeiten berechnen und anzeigen
    function updateTimer(startTime) {
        if (!timerElement) return;
        
        const now = new Date();
        const start = new Date(startTime);
        let diffMs = now - start;
        
        // Formatieren (Stunden:Minuten:Sekunden)
        const hours = Math.floor(diffMs / 3600000);
        diffMs %= 3600000;
        const minutes = Math.floor(diffMs / 60000);
        diffMs %= 60000;
        const seconds = Math.floor(diffMs / 1000);
        
        // Zeiten mit führender Null anzeigen
        timerElement.textContent = 
            String(hours).padStart(2, '0') + ':' + 
            String(minutes).padStart(2, '0') + ':' + 
            String(seconds).padStart(2, '0');
    }
    
    // Timer initialisieren, wenn vorhanden
    if (activeTimerElement && timerElement) {
        const startTime = activeTimerElement.getAttribute('data-start-time');
        
        if (startTime) {
            console.log('Timer initialisiert mit Startzeit:', startTime);
            
            // Initiale Anzeige
            updateTimer(startTime);
            
            // Timer alle Sekunde aktualisieren
            setInterval(function() {
                updateTimer(startTime);
            }, 1000);
        }
    }
    
    // Aktuelle Zeit für manuelle Eingaben setzen
    function setCurrentDateTime() {
        const startTimeInput = document.getElementById('id_start_time');
        const endTimeInput = document.getElementById('id_end_time');
        
        if (startTimeInput && endTimeInput) {
            const now = new Date();
            
            // ISO-String erzeugen und für HTML5 datetime-local formatieren (YYYY-MM-DDThh:mm)
            const isoNow = now.toISOString().slice(0, 16);
            startTimeInput.value = isoNow;
            
            // End-Zeit = jetzt + 1 Stunde
            const oneHourLater = new Date(now.getTime() + 60 * 60 * 1000);
            const isoLater = oneHourLater.toISOString().slice(0, 16);
            endTimeInput.value = isoLater;
        }
    }
    
    // Zeit-Inputs initialisieren, wenn auf der Zeiterfassungsseite
    const timeEntryForm = document.getElementById('id_start_time');
    if (timeEntryForm) {
        setCurrentDateTime();
    }
});