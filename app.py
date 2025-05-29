from flask import Flask, render_template, jsonify, request
from datetime import datetime, timedelta
import threading
import time

app = Flask(__name__)

timer_state = {              #słownik przechowujący stan timera
    'is_running': False,
    'current_session': 0,
    'current_cycle': 0,
    'time_left': 0,
    'is_break': False,
    'total_sessions': 0,
    'work_duration': 25,
    'break_duration': 5,
    'cycles': 1,
    'start_time': None,
    'paused_time': 0
}

timer_thread = None
stop_timer = threading.Event()


def timer_worker():
    """Funkcja działająca w osobnym wątku do obsługi timera"""
    global timer_state, stop_timer

    while not stop_timer.is_set() and timer_state['is_running']:
        if timer_state['time_left'] > 0:
            time.sleep(1)  # Czekaj 1 sekundę
            timer_state['time_left'] -= 1  # Odejmij sekundę
        else:
            # Czas się skończył - przełącz fazę
            if timer_state['is_break']:
                # Koniec przerwy → przejdź do pracy
                timer_state['is_break'] = False
                timer_state['current_session'] += 1

                if timer_state['current_session'] >= timer_state['total_sessions']:
                    # Wszystkie sesje skończone
                    timer_state['is_running'] = False
                    timer_state['current_cycle'] += 1
                    # Sprawdź czy wszystkie cykle skończone
                    if timer_state['current_cycle'] >= timer_state['cycles']:
                        timer_state['current_cycle'] = 0
                        timer_state['current_session'] = 0
                else:
                    # Rozpocznij następną sesję pracy
                    timer_state['time_left'] = timer_state['work_duration'] * 60
            else:
                # Koniec pracy → przejdź do przerwy
                timer_state['is_break'] = True
                timer_state['time_left'] = timer_state['break_duration'] * 60

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/start', methods=['POST'])
def start_timer():
    global timer_state, timer_thread, stop_timer

    if timer_state['is_running']:
        return jsonify({'error': 'Timer już działa'}), 400

    data = request.json  # Pobierz dane JSON z przeglądarki

    # Ustawienia timera z formularza
    timer_state.update({
        'work_duration': int(data.get('work_duration', 25)),
        'break_duration': int(data.get('break_duration', 5)),
        'cycles': int(data.get('cycles', 1)),
        'is_running': True,
        'current_session': 0,
        'current_cycle': 0,
        'is_break': False,
        'time_left': int(data.get('work_duration', 25)) * 60,  # Minuty → sekundy
        'total_sessions': int(data.get('cycles', 1)),
        'start_time': datetime.now(),
        'paused_time': 0
    })

    # Uruchom timer w osobnym wątku
    stop_timer.clear()  # Resetuj sygnał stop
    timer_thread = threading.Thread(target=timer_worker)  # Utwórz wątek
    timer_thread.daemon = True  # Zamknij z aplikacją
    timer_thread.start()  # Uruchom wątek

    return jsonify({'status': 'started', 'timer_state': timer_state})


@app.route('/api/pause', methods=['POST'])
def pause_timer():
    global timer_state

    if timer_state['is_running']:
        # Zatrzymaj timer
        timer_state['is_running'] = False
        return jsonify({'status': 'paused', 'timer_state': timer_state})
    else:
        # Wznów timer
        timer_state['is_running'] = True
        # Uruchom nowy wątek
        global timer_thread, stop_timer
        stop_timer.clear()
        timer_thread = threading.Thread(target=timer_worker)
        timer_thread.daemon = True
        timer_thread.start()
        return jsonify({'status': 'resumed', 'timer_state': timer_state})


@app.route('/api/stop', methods=['POST'])
def stop_timer_endpoint():
    global timer_state, stop_timer

    stop_timer.set()  # Wyślij sygnał do wątku żeby się zatrzymał

    # Zresetuj cały stan
    timer_state.update({
        'is_running': False,
        'current_session': 0,
        'current_cycle': 0,
        'time_left': 0,
        'is_break': False,
        'start_time': None,
        'paused_time': 0
    })

    return jsonify({'status': 'stopped', 'timer_state': timer_state})

@app.route('/api/status')
def get_status():
    return jsonify(timer_state)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)