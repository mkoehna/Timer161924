# Architektura aplikacji
Aplikacja jest zbudowana w architekturze klient-serwer:

## Backend: Python Flask
## Frontend: HTML, CSS, JavaScript z biblioteką Bootstrap5

Komunikacja między frontendem a backendem odbywa się za pomocą API RESTowego.

## Endpointy

| Endpoint | Metoda | opis |
|---|---|---|
| / | GET | Główna strona aplikacji |
| /api/start | POST | Uruchamia timer |
| /api/pause | POST | Pauzuje/wznawia timer |
| /api/stop | POST | Zatrzymuje timer |
| /api/status | GET | Zwraca aktualny stan timera |
| /api/update-settings | POST | Aktualizuje ustawienia timera bez uruchamiania |
| /api/focus/toggle | POST | Przełącza tryb skupienia |
| /api/focus/settings | POST | Aktualizuje ustawienia trybu skupienia |
| /api/focus/acknowledge-exit | POST | Potwierdza wyjście z trybu skupienia |


## Backend przechowuje stan aplikacji w słowniku timer_state
timer_state = {  <br>
    'is_running': False,    &emsp;  &emsp; &emsp;   # Czy timer jest uruchomiony  <br>
    'current_session': 0,    &emsp;&emsp; &emsp;    # Aktualna sesja  <br>
    'current_cycle': 0,     &emsp; &emsp; &emsp;    # Aktualny cykl  <br>
    'time_left': 0,       &emsp;  &emsp; &emsp;&emsp;     # Pozostały czas w sekundach  <br>
    'is_break': False,     &emsp; &emsp; &emsp;     # Czy trwa przerwa  <br>
    'total_sessions': 0,  &emsp;  &emsp; &emsp;     # Całkowita liczba sesji  <br>
    'work_duration': 25,  &emsp;  &emsp; &emsp;     # Domyślny czas pracy w minutach  <br>
    'break_duration': 5,  &emsp;  &emsp; &emsp;     # Domyślny czas przerwy w minutach  <br>
    'cycles': 1,          &emsp; &emsp; &emsp;&emsp; &emsp;&emsp;     # Domyślna liczba cykli  <br>
    'end_with_break': True,&emsp;&emsp; &emsp;     # Czy kończyć przerwą  <br>
    'warmup_enabled': False,&emsp; &emsp; &emsp;    # Czy włączyć rozgrzewkę  <br>
    'in_warmup': False,     &emsp; &emsp; &emsp;    # Czy aktualnie jest rozgrzewka  <br>
    'focus_mode': { ... }  &emsp; &emsp;  &emsp;    # Ustawienia trybu skupienia  <br>
}<br>

# Uruchomienie aplikacji
## Wymagania:
Python 3.6+
Flask

## Instalacja zależności
pip install flask

## Uruchomienie aplikacji
python app.py <br>
Przegladarka: 
http://localhost:5000


