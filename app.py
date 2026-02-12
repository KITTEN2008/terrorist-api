from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from datetime import datetime
import os
import json
import threading
import time
import requests
from functools import wraps

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Конфигурация
PING_INTERVAL = 600  # 10 минут (Render усыпляет через 15 минут бездействия)
RENDER_EXTERNAL_URL = os.environ.get('RENDER_EXTERNAL_URL', None)
IS_RENDER = os.environ.get('RENDER', False)

# База данных подозреваемых
suspects_db = [
    {
        "id": 1,
        "full_name": "Мокшанкин Дмитрий Алексеевич",
        "alias": ["Мокшан", "DM", "CyberMok"],
        "date_of_birth": "2005-01-28",
        "birth_place": "Челябинск",
        "nationality": "РФ",
        "crime_type": "кибер-терроризм",
        "crime_details": "Создание и распространение вредоносного ПО, взлом государственных систем, DDoS атаки на правительственные сайты",
        "status": "в розыске",
        "last_seen": "2026-02-10",
        "last_seen_location": "Челябинск, ул. Ленина, 54",
        "danger_level": "высокий",
        "added_date": "2026-01-15",
        "case_number": "2026-001",
        "investigator": "Сидоров А.А.",
        "notes": "Имеет техническое образование, действует в составе группы. Предположительно находится в Челябинске."
    },
    {
        "id": 2,
        "full_name": "Балин Дмитрий Александрович",
        "alias": ["Бал", "Bal1n", "CyberGhost", "Ghost"],
        "date_of_birth": "2007-06-09",
        "birth_place": "Челябинск",
        "nationality": "РФ",
        "crime_type": "кибер-экстремизм",
        "crime_details": "Распространение экстремистских материалов в сети, DDoS атаки, взлом социальных сетей",
        "status": "в розыске",
        "last_seen": "2026-02-11",
        "last_seen_location": "Челябинск, Комсомольский пр., 83",
        "danger_level": "средний",
        "added_date": "2026-01-20",
        "case_number": "2026-002",
        "investigator": "Петров И.И.",
        "notes": "Несовершеннолетний, возможен контакт с родителями. Ранее не судим."
    }
]

next_id = 3

# Декоратор для логирования запросов
def log_request(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Запрос: {request.method} {request.path}")
        return f(*args, **kwargs)
    return decorated_function

# Middleware для поддержания активности
@app.before_request
def before_request():
    """Логирование всех запросов"""
    pass

# Функция для само-пингования
def self_ping():
    """Периодически пингует собственный URL чтобы Render не усыплял"""
    if IS_RENDER and RENDER_EXTERNAL_URL:
        while True:
            try:
                time.sleep(PING_INTERVAL)
                response = requests.get(f"{RENDER_EXTERNAL_URL}/api/ping", timeout=10)
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Пинг: статус {response.status_code}")
            except Exception as e:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Ошибка пинга: {e}")

# Эндпоинт для пинга
@app.route('/api/ping', methods=['GET'])
@log_request
def ping():
    """Простой эндпоинт для проверки активности"""
    return jsonify({
        'status': 'active',
        'timestamp': datetime.now().isoformat(),
        'environment': 'render' if IS_RENDER else 'development',
        'suspects_count': len(suspects_db)
    })

# Эндпоинт для проверки здоровья
@app.route('/api/health', methods=['GET'])
@log_request
def health_check():
    """Проверка здоровья сервиса"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'uptime': time.time() - start_time if 'start_time' in globals() else 0
    })

@app.route('/')
@log_request
def index():
    """Главная страница"""
    return render_template('index.html')

@app.route('/api/suspects', methods=['GET'])
@log_request
def get_all_suspects():
    """Получить всех подозреваемых"""
    return jsonify({
        'status': 'success',
        'count': len(suspects_db),
        'data': suspects_db,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/suspects/<int:suspect_id>', methods=['GET'])
@log_request
def get_suspect(suspect_id):
    """Получить подозреваемого по ID"""
    suspect = next((s for s in suspects_db if s['id'] == suspect_id), None)
    if suspect:
        return jsonify({
            'status': 'success',
            'data': suspect
        })
    return jsonify({
        'status': 'error',
        'message': 'Подозреваемый не найден'
    }), 404

@app.route('/api/suspects', methods=['POST'])
@log_request
def add_suspect():
    """Добавить нового подозреваемого"""
    global next_id
    data = request.json
    
    # Валидация обязательных полей
    if not data.get('full_name'):
        return jsonify({
            'status': 'error',
            'message': 'Поле full_name обязательно'
        }), 400
    
    if not data.get('date_of_birth'):
        return jsonify({
            'status': 'error',
            'message': 'Поле date_of_birth обязательно'
        }), 400
    
    if not data.get('crime_type'):
        return jsonify({
            'status': 'error',
            'message': 'Поле crime_type обязательно'
        }), 400
    
    new_suspect = {
        'id': next_id,
        'full_name': data.get('full_name'),
        'alias': data.get('alias', []),
        'date_of_birth': data.get('date_of_birth'),
        'birth_place': data.get('birth_place', ''),
        'nationality': data.get('nationality', 'РФ'),
        'crime_type': data.get('crime_type'),
        'crime_details': data.get('crime_details', ''),
        'status': data.get('status', 'в розыске'),
        'last_seen': data.get('last_seen', datetime.now().strftime('%Y-%m-%d')),
        'last_seen_location': data.get('last_seen_location', ''),
        'danger_level': data.get('danger_level', 'средний'),
        'added_date': datetime.now().strftime('%Y-%m-%d'),
        'case_number': data.get('case_number', f"2026-{next_id:03d}"),
        'investigator': data.get('investigator', ''),
        'notes': data.get('notes', '')
    }
    
    suspects_db.append(new_suspect)
    next_id += 1
    
    return jsonify({
        'status': 'success',
        'message': 'Подозреваемый добавлен',
        'data': new_suspect
    }), 201

@app.route('/api/suspects/<int:suspect_id>', methods=['PUT'])
@log_request
def update_suspect(suspect_id):
    """Обновить данные подозреваемого"""
    data = request.json
    suspect = next((s for s in suspects_db if s['id'] == suspect_id), None)
    
    if not suspect:
        return jsonify({
            'status': 'error',
            'message': 'Подозреваемый не найден'
        }), 404
    
    # Обновляем поля
    suspect.update({
        'full_name': data.get('full_name', suspect['full_name']),
        'alias': data.get('alias', suspect['alias']),
        'date_of_birth': data.get('date_of_birth', suspect['date_of_birth']),
        'birth_place': data.get('birth_place', suspect['birth_place']),
        'nationality': data.get('nationality', suspect['nationality']),
        'crime_type': data.get('crime_type', suspect['crime_type']),
        'crime_details': data.get('crime_details', suspect['crime_details']),
        'status': data.get('status', suspect['status']),
        'last_seen': data.get('last_seen', suspect['last_seen']),
        'last_seen_location': data.get('last_seen_location', suspect['last_seen_location']),
        'danger_level': data.get('danger_level', suspect['danger_level']),
        'investigator': data.get('investigator', suspect['investigator']),
        'notes': data.get('notes', suspect['notes'])
    })
    
    return jsonify({
        'status': 'success',
        'message': 'Данные обновлены',
        'data': suspect
    })

@app.route('/api/suspects/<int:suspect_id>', methods=['DELETE'])
@log_request
def delete_suspect(suspect_id):
    """Удалить подозреваемого"""
    global suspects_db
    suspect = next((s for s in suspects_db if s['id'] == suspect_id), None)
    
    if not suspect:
        return jsonify({
            'status': 'error',
            'message': 'Подозреваемый не найден'
        }), 404
    
    suspects_db = [s for s in suspects_db if s['id'] != suspect_id]
    
    return jsonify({
        'status': 'success',
        'message': 'Подозреваемый удален'
    })

@app.route('/api/search', methods=['GET'])
@log_request
def search_suspects():
    """Поиск с фильтрацией"""
    query = request.args.get('q', '').lower()
    crime_type = request.args.get('crime_type', '')
    danger_level = request.args.get('danger_level', '')
    status = request.args.get('status', '')
    
    results = []
    
    for suspect in suspects_db:
        match = True
        
        # Поиск по тексту
        if query:
            match = False
            if query in suspect['full_name'].lower():
                match = True
            for alias in suspect['alias']:
                if query in alias.lower():
                    match = True
            if query in suspect['crime_details'].lower():
                match = True
            if query in suspect['birth_place'].lower():
                match = True
            if query in suspect['notes'].lower():
                match = True
        
        # Фильтры
        if crime_type and crime_type != suspect['crime_type']:
            match = False
        if danger_level and danger_level != suspect['danger_level']:
            match = False
        if status and status != suspect['status']:
            match = False
        
        if match:
            results.append(suspect)
    
    return jsonify({
        'status': 'success',
        'count': len(results),
        'data': results,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/stats', methods=['GET'])
@log_request
def get_stats():
    """Статистика"""
    stats = {
        'total': len(suspects_db),
        'by_crime_type': {},
        'by_danger_level': {},
        'by_status': {},
        'by_city': {},
        'by_age_group': {
            'до 18': 0,
            '18-25': 0,
            '26-35': 0,
            '36+': 0
        }
    }
    
    current_year = datetime.now().year
    
    for suspect in suspects_db:
        # По типу преступления
        crime_type = suspect['crime_type']
        stats['by_crime_type'][crime_type] = stats['by_crime_type'].get(crime_type, 0) + 1
        
        # По уровню опасности
        danger = suspect['danger_level']
        stats['by_danger_level'][danger] = stats['by_danger_level'].get(danger, 0) + 1
        
        # По статусу
        status = suspect['status']
        stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
        
        # По городу
        city = suspect['birth_place']
        if city:
            stats['by_city'][city] = stats['by_city'].get(city, 0) + 1
        
        # По возрасту
        if suspect['date_of_birth']:
            try:
                birth_year = int(suspect['date_of_birth'].split('-')[0])
                age = current_year - birth_year
                if age < 18:
                    stats['by_age_group']['до 18'] += 1
                elif age < 26:
                    stats['by_age_group']['18-25'] += 1
                elif age < 36:
                    stats['by_age_group']['26-35'] += 1
                else:
                    stats['by_age_group']['36+'] += 1
            except:
                pass
    
    return jsonify(stats)

# Запись времени запуска
start_time = time.time()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    
    # Запускаем поток для само-пингования если на Render
    if IS_RENDER and RENDER_EXTERNAL_URL:
        ping_thread = threading.Thread(target=self_ping, daemon=True)
        ping_thread.start()
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Запущен поток само-пингования для {RENDER_EXTERNAL_URL}")
    
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Запуск сервера на порту {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
