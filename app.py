from flask import Flask, render_template, jsonify, request
from datetime import datetime, timedelta
import threading
import time

app = Flask(__name__)

# Globalne zmienne do zarządzania timerem
timer_state = {
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
            time.sleep(1)
            timer_state['time_left'] -= 1
        else:
            # Czas się skończył
            print(
                f"DEBUG: Time finished. Current session: {timer_state['current_session']}, is_break: {timer_state['is_break']}")

            if timer_state['is_break']:
                # Koniec przerwy
                timer_state['current_session'] += 1  # Nalicz sesję przerwy
                print(
                    f"DEBUG: Break ended. Session incremented to: {timer_state['current_session']}/{timer_state['total_sessions']}")

                # Sprawdź czy to była ostatnia sesja
                if timer_state['current_session'] >= timer_state['total_sessions']:
                    print(
                        f"DEBUG: All sessions completed! Stopping timer. Final: {timer_state['current_session']}/{timer_state['total_sessions']}")
                    timer_state['is_running'] = False
                    break

                # Przełącz na pracę i nalicz cykl
                timer_state['is_break'] = False
                timer_state['time_left'] = round(timer_state['work_duration'] * 60)
                timer_state['current_cycle'] += 1
                print(f"DEBUG: Switched to work. Cycle: {timer_state['current_cycle']}/{timer_state['cycles']}")

            else:
                # Koniec pracy
                timer_state['current_session'] += 1  # Nalicz sesję pracy
                print(
                    f"DEBUG: Work ended. Session incremented to: {timer_state['current_session']}/{timer_state['total_sessions']}")

                # Sprawdź czy to była ostatnia sesja
                if timer_state['current_session'] >= timer_state['total_sessions']:
                    print(
                        f"DEBUG: All sessions completed! Stopping timer. Final: {timer_state['current_session']}/{timer_state['total_sessions']}")
                    timer_state['is_running'] = False
                    break

                # Przełącz na przerwę
                timer_state['is_break'] = True
                timer_state['time_left'] = round(timer_state['break_duration'] * 60)
                print(f"DEBUG: Switched to break. Time: {timer_state['time_left']}s")


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/start', methods=['POST'])
def start_timer():
    global timer_state, timer_thread, stop_timer

    if timer_state['is_running']:
        return jsonify({'error': 'Timer już działa'}), 400

    data = request.json

    try:
        # Parsowanie ułamków dziesiętnych minut
        work_duration_decimal = float(data.get('work_duration', 25))
        break_duration_decimal = float(data.get('break_duration', 5))
        cycles = int(data.get('cycles', 1))

        # Walidacja zakresów (w minutach)
        if work_duration_decimal < 0.017 or work_duration_decimal > 120:  # min 1 sekunda
            return jsonify({'error': 'Czas pracy musi być między 0.017 a 120 minutami'}), 400

        if break_duration_decimal < 0.017 or break_duration_decimal > 60:  # min 1 sekunda
            return jsonify({'error': 'Czas przerwy musi być między 0.017 a 60 minutami'}), 400

        if cycles < 1 or cycles > 20:
            return jsonify({'error': 'Liczba cykli musi być między 1 a 20'}), 400

        # Konwersja na sekundy (zaokrąglone do pełnych sekund)
        work_duration_seconds = round(work_duration_decimal * 60)
        break_duration_seconds = round(break_duration_decimal * 60)

        # Ustawienia timera
        timer_state.update({
            'work_duration': work_duration_decimal,  # Zachowaj ułamek dla frontend
            'break_duration': break_duration_decimal,  # Zachowaj ułamek dla frontend
            'cycles': cycles,
            'is_running': True,
            'current_session': 0,  # Aktualna sesja (0-7 dla 4 cykli)
            'current_cycle': 0,  # Aktualny cykl (0-3 dla 4 cykli)
            'is_break': False,
            'time_left': work_duration_seconds,  # Sekundy dla odliczania
            'total_sessions': cycles * 2,  # Każdy cykl = 2 sesje (praca + przerwa)
            'start_time': datetime.now(),
            'paused_time': 0
        })

        # Uruchom timer w osobnym wątku
        stop_timer.clear()
        timer_thread = threading.Thread(target=timer_worker)
        timer_thread.daemon = True
        timer_thread.start()

        return jsonify({'status': 'started', 'timer_state': timer_state})

    except (ValueError, TypeError) as e:
        return jsonify({'error': 'Nieprawidłowe dane wejściowe'}), 400


@app.route('/api/pause', methods=['POST'])
def pause_timer():
    global timer_state

    if timer_state['is_running']:
        timer_state['is_running'] = False
        return jsonify({'status': 'paused', 'timer_state': timer_state})
    else:
        timer_state['is_running'] = True
        # Wznów timer w nowym wątku
        global timer_thread, stop_timer
        stop_timer.clear()
        timer_thread = threading.Thread(target=timer_worker)
        timer_thread.daemon = True
        timer_thread.start()
        return jsonify({'status': 'resumed', 'timer_state': timer_state})


@app.route('/api/stop', methods=['POST'])
def stop_timer_endpoint():
    global timer_state, stop_timer

    stop_timer.set()
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