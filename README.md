Architektura aplikacji
Aplikacja jest zbudowana w architekturze klient-serwer:

Backend: Flask (Python)
Frontend: HTML, CSS, JavaScript z biblioteką Bootstrap

Komunikacja między frontendem a backendem odbywa się za pomocą API RESTowego.

 Endpointy
/                              GET      Główna strona aplikacji
/api/start                     POST     Uruchamia timer
/api/pause                     POST     Pauzuje/wznawia timer
/api/stop                      POST     Zatrzymuje timer
/api/status                    GET      Zwraca aktualny stan timera
/api/update-settings           POST     Aktualizuje ustawienia timera bez uruchamiania
/api/focus/toggle              POST     Przełącza tryb skupienia
/api/focus/settings            POST     Aktualizuje ustawienia trybu skupienia
/api/focus/acknowledge-exit    POST     Potwierdza wyjście z trybu skupienia

Backend przechowuje stan aplikacji w słowniku timer_state
timer_state = {
    'is_running': False,          # Czy timer jest uruchomiony
    'current_session': 0,         # Aktualna sesja
    'current_cycle': 0,           # Aktualny cykl
    'time_left': 0,               # Pozostały czas w sekundach
    'is_break': False,            # Czy trwa przerwa
    'total_sessions': 0,          # Całkowita liczba sesji
    'work_duration': 25,          # Domyślny czas pracy w minutach
    'break_duration': 5,          # Domyślny czas przerwy w minutach
    'cycles': 1,                  # Domyślna liczba cykli
    'end_with_break': True,       # Czy kończyć przerwą
    'warmup_enabled': False,      # Czy włączyć rozgrzewkę
    'in_warmup': False,           # Czy aktualnie jest rozgrzewka
    'focus_mode': { ... }         # Ustawienia trybu skupienia
}

Uruchomienie aplikacji
Wymagania:
Python 3.6+
Flask

Instalacja zależności
pip install flask

Uruchomienie aplikacji
python app.py
Przegladarka:
http://localhost:5000
