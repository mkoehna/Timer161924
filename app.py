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
    'paused_time': 0,
    'end_with_break': True,  # Nowe pole - czy kończymy przerwą
    'warmup_enabled': False,  # Nowe pole - czy włączyć rozgrzewkę
    'in_warmup': False,  # Nowe pole - czy aktualnie jest rozgrzewka
    'warmup_duration': 10,  # Czas rozgrzewki w sekundach
    # Focus Mode state
    'focus_mode': {
        'active': False,
        'auto_enable_on_start': False,
        'auto_disable_on_completion': True,
        'auto_disable_on_stop': True,
        'exit_requested': False,  # Sygnał dla frontendu do wyjścia z focus mode
        'theme': {
            'work_color': '#28a745',
            'break_color': '#ffc107',
            'warmup_color': '#adb5bd'  # Dodajemy kolor dla rozgrzewki
        }
    }
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
                f"DEBUG: Time finished. Current session: {timer_state['current_session']}, is_break: {timer_state['is_break']}, in_warmup: {timer_state['in_warmup']}")

            # Jeśli była rozgrzewka, przełącz na pierwszy timer pracy
            if timer_state['in_warmup']:
                timer_state['in_warmup'] = False
                timer_state['time_left'] = round(timer_state['work_duration'] * 60)
                print(f"DEBUG: Warmup ended. Switching to first work session.")
                continue

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

                    # Auto-wyłącz focus mode po zakończeniu
                    if timer_state['focus_mode']['auto_disable_on_completion'] and timer_state['focus_mode']['active']:
                        timer_state['focus_mode']['exit_requested'] = True
                        print("DEBUG: Requesting focus mode exit after completion")

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

                    # Auto-wyłącz focus mode po zakończeniu
                    if timer_state['focus_mode']['auto_disable_on_completion'] and timer_state['focus_mode']['active']:
                        timer_state['focus_mode']['exit_requested'] = True
                        print("DEBUG: Requesting focus mode exit after completion")

                    break

                # Przełącz na przerwę
                timer_state['is_break'] = True
                timer_state['time_left'] = round(timer_state['break_duration'] * 60)
                print(f"DEBUG: Switched to break. Time: {timer_state['time_left']}s")

            if not timer_state['is_running']:
                break


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
        end_with_break = bool(data.get('end_with_break', True))
        warmup_enabled = bool(data.get('warmup_enabled', False))

        # Walidacja zakresów (w minutach)
        if work_duration_decimal < 0.016 or work_duration_decimal > 120:  # min 1 sekunda
            return jsonify({'error': 'Czas pracy musi być między 0.016 a 120 minutami'}), 400

        if break_duration_decimal < 0.016 or break_duration_decimal > 60:  # min 1 sekunda
            return jsonify({'error': 'Czas przerwy musi być między 0.016 a 60 minutami'}), 400

        if cycles < 1 or cycles > 20:
            return jsonify({'error': 'Liczba cykli musi być między 1 a 20'}), 400

        # Konwersja na sekundy (zaokrąglone do pełnych sekund)
        work_duration_seconds = round(work_duration_decimal * 60)
        break_duration_seconds = round(break_duration_decimal * 60)

        # Obliczenie całkowitej liczby sesji
        total_sessions = cycles * 2
        if not end_with_break:
            total_sessions -= 1  # Odejmujemy ostatnią przerwę jeśli nie kończymy przerwą

        # Ustawienia timera
        timer_state.update({
            'work_duration': work_duration_decimal,  # Zachowaj ułamek dla frontend
            'break_duration': break_duration_decimal,  # Zachowaj ułamek dla frontend
            'cycles': cycles,
            'is_running': True,
            'current_session': 0,
            'current_cycle': 0,
            'is_break': False,
            'end_with_break': end_with_break,
            'warmup_enabled': warmup_enabled,
            'in_warmup': warmup_enabled,  # Zaczynamy od rozgrzewki jeśli włączona
            'time_left': 10 if warmup_enabled else work_duration_seconds,
            # Jeśli rozgrzewka to 10s, inaczej normalny czas pracy
            'total_sessions': total_sessions,
            'start_time': datetime.now(),
            'paused_time': 0
        })

        # Auto-włącz focus mode jeśli ustawione
        if timer_state['focus_mode']['auto_enable_on_start']:
            timer_state['focus_mode']['active'] = True
            print("DEBUG: Auto-enabled focus mode on timer start")

        # Reset flag wyjścia z focus mode
        timer_state['focus_mode']['exit_requested'] = False

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
        # Reset flag wyjścia z focus mode przy wznowieniu
        timer_state['focus_mode']['exit_requested'] = False

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

    # Auto-wyłącz focus mode przy zatrzymaniu jeśli ustawione
    if timer_state['focus_mode']['auto_disable_on_stop'] and timer_state['focus_mode']['active']:
        timer_state['focus_mode']['exit_requested'] = True
        print("DEBUG: Requesting focus mode exit after stop")

    timer_state.update({
        'is_running': False,
        'current_session': 0,
        'current_cycle': 0,
        'time_left': 0,
        'is_break': False,
        'in_warmup': False,  # Reset stanu rozgrzewki
        'start_time': None,
        'paused_time': 0
        # Nie resetujemy end_with_break i warmup_enabled, żeby zachować ustawienia użytkownika
    })

    return jsonify({'status': 'stopped', 'timer_state': timer_state})


@app.route('/api/update-settings', methods=['POST'])
def update_timer_settings():
    """Aktualizuje ustawienia timera bez jego uruchamiania"""
    global timer_state

    data = request.json or {}

    # Aktualizuj tylko te ustawienia, które zostały przekazane
    if 'end_with_break' in data:
        timer_state['end_with_break'] = bool(data['end_with_break'])

    if 'warmup_enabled' in data:
        timer_state['warmup_enabled'] = bool(data['warmup_enabled'])

    print(
        f"DEBUG: Timer settings updated: end_with_break={timer_state['end_with_break']}, warmup_enabled={timer_state['warmup_enabled']}")

    return jsonify({
        'status': 'settings_updated',
        'timer_state': timer_state
    })


@app.route('/api/focus/toggle', methods=['POST'])
def toggle_focus_mode():
    """Przełącza stan focus mode"""
    data = request.json or {}
    force_state = data.get('force_state')  # None, True, False

    if force_state is not None:
        timer_state['focus_mode']['active'] = bool(force_state)
    else:
        timer_state['focus_mode']['active'] = not timer_state['focus_mode']['active']

    # Reset flag wyjścia przy ręcznym przełączeniu
    timer_state['focus_mode']['exit_requested'] = False

    print(f"DEBUG: Focus mode toggled to: {timer_state['focus_mode']['active']}")

    return jsonify({
        'status': 'focus_toggled',
        'focus_mode': timer_state['focus_mode']
    })


@app.route('/api/focus/settings', methods=['POST'])
def update_focus_settings():
    """Aktualizuje ustawienia focus mode"""
    data = request.json or {}

    focus_settings = timer_state['focus_mode']

    # Aktualizuj ustawienia jeśli podane
    if 'auto_enable_on_start' in data:
        focus_settings['auto_enable_on_start'] = bool(data['auto_enable_on_start'])

    if 'auto_disable_on_completion' in data:
        focus_settings['auto_disable_on_completion'] = bool(data['auto_disable_on_completion'])

    if 'auto_disable_on_stop' in data:
        focus_settings['auto_disable_on_stop'] = bool(data['auto_disable_on_stop'])

    if 'theme' in data:
        theme_data = data['theme']
        if 'work_color' in theme_data:
            focus_settings['theme']['work_color'] = theme_data['work_color']
        if 'break_color' in theme_data:
            focus_settings['theme']['break_color'] = theme_data['break_color']
        if 'warmup_color' in theme_data:
            focus_settings['theme']['warmup_color'] = theme_data['warmup_color']

    print(f"DEBUG: Focus settings updated: {focus_settings}")

    return jsonify({
        'status': 'settings_updated',
        'focus_mode': focus_settings
    })


@app.route('/api/focus/acknowledge-exit', methods=['POST'])
def acknowledge_focus_exit():
    """Frontend potwierdza wyjście z focus mode"""
    timer_state['focus_mode']['exit_requested'] = False
    timer_state['focus_mode']['active'] = False

    print("DEBUG: Focus mode exit acknowledged by frontend")

    return jsonify({
        'status': 'exit_acknowledged',
        'focus_mode': timer_state['focus_mode']
    })


@app.route('/api/status')
def get_status():
    return jsonify(timer_state)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)