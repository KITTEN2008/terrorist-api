from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from datetime import datetime
import os
import json
import threading
import time
import requests
import logging
from functools import wraps

app = Flask(__name__)
CORS(app)

# === НАСТРОЙКИ АНТИ-СНА ===
PING_INTERVAL = 300  # Пинг каждые 5 минут (вместо 10)
RENDER_EXTERNAL_URL = os.environ.get('RENDER_EXTERNAL_URL', None)
IS_RENDER = os.environ.get('RENDER', False)
PORT = int(os.environ.get('PORT', 5000))

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === БАЗА ДАННЫХ ===
suspects_db = [
    {
        "id": 1,
        "full_name": "Мокшанкин Дмитрий Алексеевич",
        "alias": ["Мокшан", "DM", "CyberMok"],
        "date_of_birth": "2005-01-28",
        "birth_place": "Челябинск",
        "nationality": "РФ",
        "crime_type": "кибер-терроризм",
        "crime_details": "Создание и распространение вредоносного ПО, взлом государственных систем",
        "status": "в розыске",
        "last_seen": "2026-02-10",
        "last_seen_location": "Челябинск, ул. Ленина, 54",
        "danger_level": "высокий",
        "added_date": "2026-01-15",
        "case_number": "2026-001",
        "investigator": "Сидоров А.А.",
        "notes": "Имеет техническое образование, действует в составе группы"
    },
    {
        "id": 2,
        "full_name": "Балин Дмитрий Александрович",
        "alias": ["Бал", "Bal1n", "CyberGhost"],
        "date_of_birth": "2007-06-09",
        "birth_place": "Челябинск",
        "nationality": "РФ",
        "crime_type": "кибер-экстремизм",
        "crime_details": "Распространение экстремистских материалов в сети, DDoS атаки",
        "status": "в розыске",
        "last_seen": "2026-02-11",
        "last_seen_location": "Челябинск, Комсомольский пр., 83",
        "danger_level": "средний",
        "added_date": "2026-01-20",
        "case_number": "2026-002",
        "investigator": "Петров И.И.",
        "notes": "Несовершеннолетний, возможен контакт с родителями"
    }
]

next_id = 3

# === СИСТЕМА АНТИ-СНА ===

def self_ping_worker():
    """Агрессивный пинг каждые 5 минут"""
    if not IS_RENDER or not RENDER_EXTERNAL_URL:
        logger.info("Анти-сон: режим разработки, пинг не требуется")
        return
    
    logger.info(f"🚀 Анти-сон активирован! URL: {RENDER_EXTERNAL_URL}")
    
    while True:
        try:
            # Основной пинг
            response = requests.get(
                f"{RENDER_EXTERNAL_URL}/api/ping",
                timeout=15,
                headers={'User-Agent': 'Render-AntiSleep/1.0'}
            )
            logger.info(f"✅ Пинг успешен: {response.status_code}")
            
            # Дополнительный пинг к health check
            requests.get(
                f"{RENDER_EXTERNAL_URL}/api/health",
                timeout=15,
                headers={'User-Agent': 'Render-AntiSleep/1.0'}
            )
            
            # Получаем статистику для активности
            requests.get(
                f"{RENDER_EXTERNAL_URL}/api/stats",
                timeout=15,
                headers={'User-Agent': 'Render-AntiSleep/1.0'}
            )
            
        except requests.exceptions.Timeout:
            logger.warning("⚠️ Таймаут пинга - сервер просыпается")
        except requests.exceptions.ConnectionError:
            logger.warning("🔴 Ошибка соединения - сервер спит")
        except Exception as e:
            logger.error(f"❌ Ошибка пинга: {e}")
        
        # Ждем 5 минут
        time.sleep(PING_INTERVAL)

def start_anti_sleep():
    """Запуск системы анти-сна в отдельном потоке"""
    if IS_RENDER:
        thread = threading.Thread(target=self_ping_worker, daemon=True)
        thread.start()
        logger.info("🛡️ Защита от сна запущена (интервал: 5 минут)")

# === ДЕКОРАТОР ДЛЯ ЛОГИРОВАНИЯ ===
def log_request(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        logger.info(f"📨 {request.method} {request.path}")
        return f(*args, **kwargs)
    return decorated_function

# === ВСТРОЕННЫЙ HTML ===
INDEX_HTML = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ФСБ - База данных подозреваемых</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', sans-serif; }
        body { background: linear-gradient(135deg, #1a1e2c 0%, #2d3748 100%); min-height: 100vh; padding: 20px; }
        .container { max-width: 1400px; margin: 0 auto; background: white; border-radius: 20px; padding: 30px; box-shadow: 0 25px 50px rgba(0,0,0,0.5); }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 2px solid #e2e8f0; }
        .header h1 { color: #2d3748; font-size: 2em; display: flex; align-items: center; gap: 10px; }
        .header h1:before { content: "⚖️"; font-size: 1.2em; }
        .btn { padding: 12px 24px; border: none; border-radius: 10px; font-size: 14px; font-weight: 600; cursor: pointer; transition: all 0.3s; display: inline-flex; align-items: center; gap: 8px; }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 7px 14px rgba(0,0,0,0.1); }
        .btn-primary { background: #4299e1; color: white; }
        .btn-success { background: #48bb78; color: white; }
        .btn-warning { background: #ecc94b; color: #744210; }
        .btn-danger { background: #f56565; color: white; }
        .btn-outline { background: transparent; border: 2px solid #4299e1; color: #4299e1; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%); color: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .stat-card h3 { font-size: 0.9em; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px; opacity: 0.9; }
        .stat-number { font-size: 2.2em; font-weight: bold; }
        .search-section { background: #f7fafc; padding: 25px; border-radius: 15px; margin-bottom: 30px; }
        .search-box { display: flex; gap: 10px; margin-bottom: 15px; }
        .search-box input { flex: 1; padding: 12px 15px; border: 2px solid #e2e8f0; border-radius: 10px; font-size: 16px; }
        .filters { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; }
        .filter-select { padding: 10px; border: 2px solid #e2e8f0; border-radius: 8px; background: white; font-size: 14px; }
        .suspects-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(400px, 1fr)); gap: 25px; margin-top: 20px; }
        .suspect-card { background: white; border: 1px solid #e2e8f0; border-radius: 15px; padding: 20px; position: relative; transition: all 0.3s; }
        .suspect-card:hover { transform: translateY(-5px); box-shadow: 0 12px 20px rgba(0,0,0,0.1); border-color: #4299e1; }
        .danger-high { border-left: 8px solid #f56565; }
        .danger-medium { border-left: 8px solid #ecc94b; }
        .danger-low { border-left: 8px solid #48bb78; }
        .card-header { display: flex; justify-content: space-between; align-items: start; margin-bottom: 15px; }
        .suspect-name { font-size: 1.3em; font-weight: bold; color: #2d3748; }
        .status-badge { padding: 5px 12px; border-radius: 20px; font-size: 0.8em; font-weight: 600; background: #fed7d7; color: #c53030; }
        .alias-container { display: flex; flex-wrap: wrap; gap: 5px; margin: 10px 0; }
        .alias-tag { background: #edf2f7; color: #4a5568; padding: 3px 10px; border-radius: 15px; font-size: 0.8em; }
        .info-row { display: flex; margin-bottom: 8px; color: #4a5568; font-size: 0.95em; }
        .info-label { font-weight: 600; width: 120px; color: #718096; }
        .info-value { flex: 1; }
        .card-actions { display: flex; gap: 10px; margin-top: 20px; padding-top: 15px; border-top: 1px solid #e2e8f0; }
        .results-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .results-count { background: #4299e1; color: white; padding: 5px 15px; border-radius: 20px; font-weight: 600; }
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 1000; justify-content: center; align-items: center; }
        .modal.active { display: flex; }
        .modal-content { background: white; padding: 30px; border-radius: 20px; max-width: 800px; width: 90%; max-height: 90vh; overflow-y: auto; }
        .form-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }
        .form-group { display: flex; flex-direction: column; }
        .form-group.full-width { grid-column: span 2; }
        .form-group label { font-weight: 600; color: #4a5568; margin-bottom: 5px; }
        .form-group input, .form-group select, .form-group textarea { padding: 10px; border: 2px solid #e2e8f0; border-radius: 8px; }
        .connection-status { position: fixed; bottom: 20px; right: 20px; padding: 10px 20px; border-radius: 30px; background: white; box-shadow: 0 5px 15px rgba(0,0,0,0.1); display: flex; align-items: center; gap: 10px; }
        .status-indicator { width: 12px; height: 12px; border-radius: 50%; background: #48bb78; animation: pulse 2s infinite; }
        .status-indicator.offline { background: #f56565; animation: none; }
        .wake-up-message { text-align: center; padding: 60px 20px; background: #f7fafc; border-radius: 15px; margin: 30px 0; }
        @keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(72, 187, 120, 0.4); } 70% { box-shadow: 0 0 0 10px rgba(72, 187, 120, 0); } 100% { box-shadow: 0 0 0 0 rgba(72, 187, 120, 0); } }
        @media (max-width: 768px) { .suspects-grid { grid-template-columns: 1fr; } .form-grid { grid-template-columns: 1fr; } .form-group.full-width { grid-column: span 1; } }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>ФСБ РФ - База данных подозреваемых</h1>
            <button class="btn btn-success" onclick="openAddModal()">➕ Добавить подозреваемого</button>
        </div>
        <div class="stats-grid" id="stats"></div>
        <div class="search-section">
            <div class="search-box">
                <input type="text" id="searchInput" placeholder="Поиск по имени, псевдониму..." onkeyup="debounce(searchSuspects, 500)()">
                <button class="btn btn-primary" onclick="searchSuspects()">🔍 Поиск</button>
                <button class="btn btn-outline" onclick="clearFilters()">✕ Сбросить</button>
            </div>
            <div class="filters">
                <select class="filter-select" id="crimeTypeFilter" onchange="searchSuspects()">
                    <option value="">Все типы преступлений</option>
                    <option value="кибер-терроризм">Кибер-терроризм</option>
                    <option value="кибер-экстремизм">Кибер-экстремизм</option>
                </select>
                <select class="filter-select" id="dangerLevelFilter" onchange="searchSuspects()">
                    <option value="">Все уровни опасности</option>
                    <option value="высокий">Высокий</option>
                    <option value="средний">Средний</option>
                    <option value="низкий">Низкий</option>
                </select>
                <select class="filter-select" id="statusFilter" onchange="searchSuspects()">
                    <option value="">Все статусы</option>
                    <option value="в розыске">В розыске</option>
                    <option value="задержан">Задержан</option>
                    <option value="под наблюдением">Под наблюдением</option>
                </select>
            </div>
        </div>
        <div class="results-header">
            <h2>📋 Список подозреваемых</h2>
            <span class="results-count" id="resultsCount">0 записей</span>
        </div>
        <div id="suspectsList" class="suspects-grid"></div>
    </div>

    <div id="suspectModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 class="modal-title" id="modalTitle">➕ Добавить подозреваемого</h2>
                <span class="close-btn" onclick="closeModal()">&times;</span>
            </div>
            <form id="suspectForm" onsubmit="saveSuspect(event)">
                <input type="hidden" id="suspectId">
                <div class="form-grid">
                    <div class="form-group full-width">
                        <label>Полное имя *</label>
                        <input type="text" id="fullName" required placeholder="Иванов Иван Иванович">
                    </div>
                    <div class="form-group">
                        <label>Псевдонимы</label>
                        <input type="text" id="alias" placeholder="через запятую">
                    </div>
                    <div class="form-group">
                        <label>Дата рождения *</label>
                        <input type="date" id="dateOfBirth" required>
                    </div>
                    <div class="form-group">
                        <label>Место рождения</label>
                        <input type="text" id="birthPlace" placeholder="Челябинск">
                    </div>
                    <div class="form-group">
                        <label>Гражданство</label>
                        <input type="text" id="nationality" value="РФ">
                    </div>
                    <div class="form-group">
                        <label>Тип преступления *</label>
                        <select id="crimeType" required>
                            <option value="кибер-терроризм">Кибер-терроризм</option>
                            <option value="кибер-экстремизм">Кибер-экстремизм</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Уровень опасности</label>
                        <select id="dangerLevel">
                            <option value="высокий">Высокий</option>
                            <option value="средний" selected>Средний</option>
                            <option value="низкий">Низкий</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Статус</label>
                        <select id="status">
                            <option value="в розыске">В розыске</option>
                            <option value="задержан">Задержан</option>
                            <option value="под наблюдением">Под наблюдением</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Номер дела</label>
                        <input type="text" id="caseNumber" placeholder="2026-001">
                    </div>
                    <div class="form-group">
                        <label>Следователь</label>
                        <input type="text" id="investigator" placeholder="Иванов И.И.">
                    </div>
                    <div class="form-group">
                        <label>Дата последнего появления</label>
                        <input type="date" id="lastSeen">
                    </div>
                    <div class="form-group">
                        <label>Место последнего появления</label>
                        <input type="text" id="lastSeenLocation" placeholder="Челябинск, ул. Ленина">
                    </div>
                    <div class="form-group full-width">
                        <label>Детали преступления</label>
                        <textarea id="crimeDetails" rows="3"></textarea>
                    </div>
                    <div class="form-group full-width">
                        <label>Примечания</label>
                        <textarea id="notes" rows="2"></textarea>
                    </div>
                </div>
                <div style="display: flex; gap: 15px; justify-content: flex-end; margin-top: 25px;">
                    <button type="button" class="btn btn-outline" onclick="closeModal()">Отмена</button>
                    <button type="submit" class="btn btn-success">Сохранить</button>
                </div>
            </form>
        </div>
    </div>

    <div id="deleteModal" class="modal">
        <div class="modal-content" style="max-width: 400px;">
            <div class="modal-header">
                <h2 class="modal-title">⚠️ Подтверждение удаления</h2>
                <span class="close-btn" onclick="closeDeleteModal()">&times;</span>
            </div>
            <div style="padding: 20px 0; text-align: center;">
                <p style="font-size: 1.1em; margin-bottom: 20px;">Вы уверены, что хотите удалить запись?</p>
                <p id="deleteSuspectName" style="font-weight: bold; color: #c53030;"></p>
            </div>
            <div style="display: flex; gap: 15px; justify-content: center;">
                <button class="btn btn-outline" onclick="closeDeleteModal()">Отмена</button>
                <button class="btn btn-danger" onclick="confirmDelete()">Удалить</button>
            </div>
        </div>
    </div>

    <div class="connection-status">
        <span class="status-indicator" id="statusIndicator"></span>
        <span id="statusText">Проверка соединения...</span>
    </div>

    <script>
        const API_URL = '/api';
        let deleteId = null;
        let searchTimeout = null;

        function debounce(func, wait) {
            return function(...args) {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => func(...args), wait);
            };
        }

        async function checkConnection() {
            try {
                const response = await fetch(`${API_URL}/ping`);
                if (response.ok) {
                    document.getElementById('statusIndicator').className = 'status-indicator';
                    document.getElementById('statusText').textContent = '🟢 Соединение установлено';
                    return true;
                }
            } catch (error) {
                document.getElementById('statusIndicator').className = 'status-indicator offline';
                document.getElementById('statusText').textContent = '🟡 Сервер засыпает...';
                return false;
            }
        }

        setInterval(checkConnection, 10000);
        checkConnection();

        async function loadStats() {
            try {
                const response = await fetch(`${API_URL}/stats`);
                const stats = await response.json();
                const statsHtml = `
                    <div class="stat-card"><h3>Всего</h3><div class="stat-number">${stats.total || 0}</div></div>
                    <div class="stat-card"><h3>Кибер-терроризм</h3><div class="stat-number">${stats.by_crime_type?.['кибер-терроризм'] || 0}</div></div>
                    <div class="stat-card"><h3>Кибер-экстремизм</h3><div class="stat-number">${stats.by_crime_type?.['кибер-экстремизм'] || 0}</div></div>
                    <div class="stat-card"><h3>Высокий риск</h3><div class="stat-number">${stats.by_danger_level?.['высокий'] || 0}</div></div>
                `;
                document.getElementById('stats').innerHTML = statsHtml;
            } catch (error) {
                console.error(error);
            }
        }

        async function loadAllSuspects() {
            try {
                const response = await fetch(`${API_URL}/suspects`);
                const data = await response.json();
                displaySuspects(data.data);
                document.getElementById('resultsCount').textContent = `${data.count || 0} записей`;
                loadStats();
            } catch (error) {
                showWakeUpMessage();
            }
        }

        async function searchSuspects() {
            const query = document.getElementById('searchInput').value;
            const crimeType = document.getElementById('crimeTypeFilter').value;
            const dangerLevel = document.getElementById('dangerLevelFilter').value;
            const status = document.getElementById('statusFilter').value;
            
            let url = `${API_URL}/search?q=${encodeURIComponent(query)}`;
            if (crimeType) url += `&crime_type=${crimeType}`;
            if (dangerLevel) url += `&danger_level=${dangerLevel}`;
            if (status) url += `&status=${status}`;
            
            try {
                const response = await fetch(url);
                const data = await response.json();
                displaySuspects(data.data);
                document.getElementById('resultsCount').textContent = `${data.count || 0} записей`;
            } catch (error) {
                showWakeUpMessage();
            }
        }

        function showWakeUpMessage() {
            document.getElementById('suspectsList').innerHTML = `
                <div style="grid-column: 1/-1;">
                    <div class="wake-up-message">
                        <h2>😴 Сервер на Render "заснул"</h2>
                        <p>Пробуждение занимает 20-30 секунд</p>
                        <button class="btn btn-primary" onclick="wakeUpServer()">🔋 Разбудить сервер</button>
                    </div>
                </div>
            `;
        }

        async function wakeUpServer() {
            try {
                await fetch(`${API_URL}/ping`);
                setTimeout(() => location.reload(), 30000);
            } catch (error) {}
        }

        function displaySuspects(suspects) {
            if (!suspects || suspects.length === 0) {
                document.getElementById('suspectsList').innerHTML = '<div style="text-align: center; padding: 50px;">🔍 Ничего не найдено</div>';
                return;
            }
            
            const html = suspects.map(s => {
                const dangerClass = `danger-${s.danger_level === 'высокий' ? 'high' : s.danger_level === 'средний' ? 'medium' : 'low'}`;
                return `
                    <div class="suspect-card ${dangerClass}">
                        <div class="card-header">
                            <div>
                                <div class="suspect-name">${escapeHtml(s.full_name)}</div>
                                <div class="case-number">Дело № ${s.case_number || 'Н/Д'}</div>
                            </div>
                            <span class="status-badge">${s.status}</span>
                        </div>
                        <div class="alias-container">${(s.alias || []).map(a => `<span class="alias-tag">${escapeHtml(a)}</span>`).join('')}</div>
                        <div class="info-row"><span class="info-label">Дата рождения:</span><span class="info-value">${s.date_of_birth || 'Н/Д'}</span></div>
                        <div class="info-row"><span class="info-label">Место рождения:</span><span class="info-value">${escapeHtml(s.birth_place) || 'Н/Д'}</span></div>
                        <div class="info-row"><span class="info-label">Преступление:</span><span class="info-value">${s.crime_type}</span></div>
                        <div class="info-row"><span class="info-label">Детали:</span><span class="info-value">${escapeHtml(s.crime_details) || 'Н/Д'}</span></div>
                        <div class="info-row"><span class="info-label">Последнее появление:</span><span class="info-value">${s.last_seen || 'Н/Д'} ${s.last_seen_location ? `, ${escapeHtml(s.last_seen_location)}` : ''}</span></div>
                        <div class="card-actions">
                            <button class="btn btn-warning" onclick="editSuspect(${s.id})">✏️ Редактировать</button>
                            <button class="btn btn-danger" onclick="openDeleteModal(${s.id}, '${escapeHtml(s.full_name)}')">🗑️ Удалить</button>
                        </div>
                    </div>
                `;
            }).join('');
            document.getElementById('suspectsList').innerHTML = html;
        }

        function escapeHtml(text) {
            if (!text) return '';
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        function clearFilters() {
            document.getElementById('searchInput').value = '';
            document.getElementById('crimeTypeFilter').value = '';
            document.getElementById('dangerLevelFilter').value = '';
            document.getElementById('statusFilter').value = '';
            loadAllSuspects();
        }

        function openAddModal() {
            document.getElementById('modalTitle').textContent = '➕ Добавить подозреваемого';
            document.getElementById('suspectForm').reset();
            document.getElementById('suspectId').value = '';
            document.getElementById('lastSeen').value = new Date().toISOString().split('T')[0];
            document.getElementById('suspectModal').classList.add('active');
        }

        async function editSuspect(id) {
            try {
                const response = await fetch(`${API_URL}/suspects/${id}`);
                const result = await response.json();
                if (result.status === 'success') {
                    const s = result.data;
                    document.getElementById('modalTitle').textContent = '✏️ Редактировать';
                    document.getElementById('suspectId').value = s.id;
                    document.getElementById('fullName').value = s.full_name || '';
                    document.getElementById('alias').value = s.alias ? s.alias.join(', ') : '';
                    document.getElementById('dateOfBirth').value = s.date_of_birth || '';
                    document.getElementById('birthPlace').value = s.birth_place || '';
                    document.getElementById('nationality').value = s.nationality || 'РФ';
                    document.getElementById('crimeType').value = s.crime_type || '';
                    document.getElementById('dangerLevel').value = s.danger_level || 'средний';
                    document.getElementById('status').value = s.status || 'в розыске';
                    document.getElementById('caseNumber').value = s.case_number || '';
                    document.getElementById('investigator').value = s.investigator || '';
                    document.getElementById('lastSeen').value = s.last_seen || '';
                    document.getElementById('lastSeenLocation').value = s.last_seen_location || '';
                    document.getElementById('crimeDetails').value = s.crime_details || '';
                    document.getElementById('notes').value = s.notes || '';
                    document.getElementById('suspectModal').classList.add('active');
                }
            } catch (error) {
                alert('Ошибка загрузки данных');
            }
        }

        async function saveSuspect(event) {
            event.preventDefault();
            const id = document.getElementById('suspectId').value;
            const data = {
                full_name: document.getElementById('fullName').value,
                alias: document.getElementById('alias').value.split(',').map(a => a.trim()).filter(a => a),
                date_of_birth: document.getElementById('dateOfBirth').value,
                birth_place: document.getElementById('birthPlace').value,
                nationality: document.getElementById('nationality').value,
                crime_type: document.getElementById('crimeType').value,
                crime_details: document.getElementById('crimeDetails').value,
                status: document.getElementById('status').value,
                last_seen: document.getElementById('lastSeen').value,
                last_seen_location: document.getElementById('lastSeenLocation').value,
                danger_level: document.getElementById('dangerLevel').value,
                case_number: document.getElementById('caseNumber').value,
                investigator: document.getElementById('investigator').value,
                notes: document.getElementById('notes').value
            };
            
            try {
                const response = await fetch(`${API_URL}/suspects${id ? '/' + id : ''}`, {
                    method: id ? 'PUT' : 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                if (response.ok) {
                    closeModal();
                    loadAllSuspects();
                }
            } catch (error) {
                alert('Ошибка сохранения');
            }
        }

        function openDeleteModal(id, name) {
            deleteId = id;
            document.getElementById('deleteSuspectName').textContent = name;
            document.getElementById('deleteModal').classList.add('active');
        }

        function closeDeleteModal() {
            deleteId = null;
            document.getElementById('deleteModal').classList.remove('active');
        }

        async function confirmDelete() {
            if (!deleteId) return;
            try {
                const response = await fetch(`${API_URL}/suspects/${deleteId}`, {method: 'DELETE'});
                if (response.ok) {
                    closeDeleteModal();
                    loadAllSuspects();
                }
            } catch (error) {
                alert('Ошибка удаления');
            }
        }

        function closeModal() {
            document.getElementById('suspectModal').classList.remove('active');
        }

        window.onload = async function() {
            showWakeUpMessage();
            try {
                await fetch(`${API_URL}/ping`);
                loadStats();
                loadAllSuspects();
            } catch (error) {}
        };
    </script>
</body>
</html>"""

# === ОСНОВНЫЕ МАРШРУТЫ ===
@app.route('/')
@log_request
def index():
    return render_template_string(INDEX_HTML)

@app.route('/api/ping', methods=['GET'])
@log_request
def ping():
    return jsonify({
        'status': 'active',
        'timestamp': datetime.now().isoformat(),
        'environment': 'render' if IS_RENDER else 'development',
        'suspects_count': len(suspects_db)
    })

@app.route('/api/health', methods=['GET'])
@log_request
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'uptime': time.time() - start_time
    })

# === API ЭНДПОИНТЫ ===
@app.route('/api/suspects', methods=['GET'])
@log_request
def get_all_suspects():
    return jsonify({
        'status': 'success',
        'count': len(suspects_db),
        'data': suspects_db
    })

@app.route('/api/suspects/<int:suspect_id>', methods=['GET'])
@log_request
def get_suspect(suspect_id):
    suspect = next((s for s in suspects_db if s['id'] == suspect_id), None)
    if suspect:
        return jsonify({'status': 'success', 'data': suspect})
    return jsonify({'status': 'error', 'message': 'Не найден'}), 404

@app.route('/api/suspects', methods=['POST'])
@log_request
def add_suspect():
    global next_id
    data = request.json
    
    if not data.get('full_name'):
        return jsonify({'status': 'error', 'message': 'Требуется полное имя'}), 400
    
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
    return jsonify({'status': 'success', 'data': new_suspect}), 201

@app.route('/api/suspects/<int:suspect_id>', methods=['PUT'])
@log_request
def update_suspect(suspect_id):
    suspect = next((s for s in suspects_db if s['id'] == suspect_id), None)
    if not suspect:
        return jsonify({'status': 'error', 'message': 'Не найден'}), 404
    
    data = request.json
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
    
    return jsonify({'status': 'success', 'data': suspect})

@app.route('/api/suspects/<int:suspect_id>', methods=['DELETE'])
@log_request
def delete_suspect(suspect_id):
    global suspects_db
    suspect = next((s for s in suspects_db if s['id'] == suspect_id), None)
    if not suspect:
        return jsonify({'status': 'error', 'message': 'Не найден'}), 404
    
    suspects_db = [s for s in suspects_db if s['id'] != suspect_id]
    return jsonify({'status': 'success', 'message': 'Удалено'})

@app.route('/api/search', methods=['GET'])
@log_request
def search_suspects():
    query = request.args.get('q', '').lower()
    crime_type = request.args.get('crime_type', '')
    danger_level = request.args.get('danger_level', '')
    status = request.args.get('status', '')
    
    results = []
    for suspect in suspects_db:
        match = True
        
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
        'data': results
    })

@app.route('/api/stats', methods=['GET'])
@log_request
def get_stats():
    stats = {
        'total': len(suspects_db),
        'by_crime_type': {},
        'by_danger_level': {},
        'by_status': {},
        'by_city': {},
        'by_age_group': {'до 18': 0, '18-25': 0, '26-35': 0, '36+': 0}
    }
    
    current_year = datetime.now().year
    
    for suspect in suspects_db:
        crime_type = suspect['crime_type']
        stats['by_crime_type'][crime_type] = stats['by_crime_type'].get(crime_type, 0) + 1
        
        danger = suspect['danger_level']
        stats['by_danger_level'][danger] = stats['by_danger_level'].get(danger, 0) + 1
        
        status = suspect['status']
        stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
        
        city = suspect['birth_place']
        if city:
            stats['by_city'][city] = stats['by_city'].get(city, 0) + 1
        
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

# === ЗАПУСК ===
start_time = time.time()

if __name__ == '__main__':
    # Запускаем систему анти-сна
    start_anti_sleep()
    
    logger.info(f"🚀 Сервер запускается на порту {PORT}")
    logger.info(f"📊 В базе {len(suspects_db)} подозреваемых")
    
    app.run(host='0.0.0.0', port=PORT, debug=False)
