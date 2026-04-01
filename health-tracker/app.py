from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import json
import os
from datetime import datetime, timedelta
from functools import wraps
import hashlib

app = Flask(__name__)
app.secret_key = 'health_tracker_secret_key_2024'

DATA_DIR = 'data'
os.makedirs(DATA_DIR, exist_ok=True)

def get_users_file():
    return os.path.join(DATA_DIR, 'users.json')

def get_user_data_file(username):
    return os.path.join(DATA_DIR, f'{username}_data.json')

def load_json(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    return {}

def save_json(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def get_default_user_data():
    return {
        'profile': {'name': '', 'age': 0, 'height': 0, 'weight': 0, 'gender': 'male'},
        'daily_logs': [],
        'goals': [],
        'reminders': [],
        'streaks': {'current': 0, 'best': 0, 'last_log_date': ''}
    }

def calculate_bmi(weight, height_cm):
    if height_cm <= 0:
        return 0
    height_m = height_cm / 100
    return round(weight / (height_m ** 2), 1)

def get_bmi_category(bmi):
    if bmi < 18.5:
        return ('Underweight', '#3b82f6', 'Consider increasing caloric intake with nutrient-dense foods.')
    elif bmi < 25:
        return ('Normal', '#10b981', 'Great job! Maintain your healthy lifestyle.')
    elif bmi < 30:
        return ('Overweight', '#f59e0b', 'Consider moderate exercise and balanced diet.')
    else:
        return ('Obese', '#ef4444', 'Consult a healthcare provider for a personalized plan.')

def get_health_suggestions(data):
    suggestions = []
    profile = data.get('profile', {})
    logs = data.get('daily_logs', [])
    
    weight = profile.get('weight', 0)
    height = profile.get('height', 0)
    
    if weight > 0 and height > 0:
        bmi = calculate_bmi(weight, height)
        cat, color, tip = get_bmi_category(bmi)
        suggestions.append({'icon': '⚖️', 'title': f'BMI: {bmi} ({cat})', 'text': tip, 'color': color})
    
    if logs:
        recent = logs[-1]
        water = recent.get('water', 0)
        if water < 8:
            suggestions.append({'icon': '💧', 'title': 'Stay Hydrated', 'text': f'You drank {water} glasses. Aim for 8+ glasses daily.', 'color': '#3b82f6'})
        
        sleep = recent.get('sleep', 0)
        if sleep < 7:
            suggestions.append({'icon': '😴', 'title': 'More Sleep Needed', 'text': f'You slept {sleep}h. Adults need 7-9 hours.', 'color': '#8b5cf6'})
        
        steps = recent.get('steps', 0)
        if steps < 10000:
            suggestions.append({'icon': '🚶', 'title': 'Move More', 'text': f'{steps} steps today. Target: 10,000 steps.', 'color': '#f59e0b'})
        
        calories = recent.get('calories', 0)
        if calories > 2500:
            suggestions.append({'icon': '🍽️', 'title': 'Watch Calories', 'text': f'{calories} cal consumed. Consider lighter meals.', 'color': '#ef4444'})
        elif calories > 0 and calories < 1200:
            suggestions.append({'icon': '🍽️', 'title': 'Eat More', 'text': f'Only {calories} cal. Minimum 1200 cal recommended.', 'color': '#f59e0b'})
    
    if not suggestions:
        suggestions.append({'icon': '📝', 'title': 'Start Logging', 'text': 'Log your first daily entry to get personalized tips!', 'color': '#6366f1'})
    
    return suggestions

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Please fill in all fields.', 'error')
            return render_template('login.html')
        
        users = load_json(get_users_file())
        
        if username in users and users[username]['password'] == hash_password(password):
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials.', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '').strip().lower()
    password = request.form.get('password', '')
    name = request.form.get('name', '').strip()
    
    if not username or not password or not name:
        flash('Please fill in all fields.', 'error')
        return redirect(url_for('login'))
    
    users = load_json(get_users_file())
    
    if username in users:
        flash('Username already exists.', 'error')
        return redirect(url_for('login'))
    
    users[username] = {'password': hash_password(password), 'name': name, 'created': datetime.now().isoformat()}
    save_json(get_users_file(), users)
    
    user_data = get_default_user_data()
    user_data['profile']['name'] = name
    save_json(get_user_data_file(username), user_data)
    
    session['username'] = username
    flash('Account created successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    data = load_json(get_user_data_file(session['username']))
    if not data:
        data = get_default_user_data()
    
    bmi = 0
    bmi_cat = ('', '', '')
    if data['profile'].get('weight', 0) > 0 and data['profile'].get('height', 0) > 0:
        bmi = calculate_bmi(data['profile']['weight'], data['profile']['height'])
        bmi_cat = get_bmi_category(bmi)
    
    suggestions = get_health_suggestions(data)
    
    # Weekly analysis
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    weekly_logs = [l for l in data.get('daily_logs', []) if l.get('date', '') >= str(week_ago)]
    
    weekly_stats = {
        'avg_calories': 0, 'avg_water': 0, 'avg_sleep': 0, 'avg_steps': 0,
        'total_logs': len(weekly_logs)
    }
    if weekly_logs:
        weekly_stats['avg_calories'] = round(sum(l.get('calories', 0) for l in weekly_logs) / len(weekly_logs))
        weekly_stats['avg_water'] = round(sum(l.get('water', 0) for l in weekly_logs) / len(weekly_logs), 1)
        weekly_stats['avg_sleep'] = round(sum(l.get('sleep', 0) for l in weekly_logs) / len(weekly_logs), 1)
        weekly_stats['avg_steps'] = round(sum(l.get('steps', 0) for l in weekly_logs) / len(weekly_logs))
    
    return render_template('index.html', 
        data=data, bmi=bmi, bmi_category=bmi_cat,
        suggestions=suggestions, weekly_stats=weekly_stats,
        weekly_logs=json.dumps(weekly_logs),
        all_logs=json.dumps(data.get('daily_logs', [])[-30:]))

@app.route('/api/profile', methods=['POST'])
@login_required
def update_profile():
    data = load_json(get_user_data_file(session['username']))
    body = request.get_json()
    data['profile'].update({
        'name': body.get('name', data['profile'].get('name', '')),
        'age': int(body.get('age', 0)),
        'height': float(body.get('height', 0)),
        'weight': float(body.get('weight', 0)),
        'gender': body.get('gender', 'male')
    })
    save_json(get_user_data_file(session['username']), data)
    return jsonify({'status': 'ok'})

@app.route('/api/log', methods=['POST'])
@login_required
def add_log():
    data = load_json(get_user_data_file(session['username']))
    body = request.get_json()
    today = datetime.now().strftime('%Y-%m-%d')
    
    entry = {
        'date': today,
        'calories': int(body.get('calories', 0)),
        'water': int(body.get('water', 0)),
        'sleep': float(body.get('sleep', 0)),
        'steps': int(body.get('steps', 0)),
        'exercise': int(body.get('exercise', 0)),
        'mood': body.get('mood', 'good'),
        'notes': body.get('notes', '')
    }
    
    # Replace if same date exists
    data['daily_logs'] = [l for l in data.get('daily_logs', []) if l.get('date') != today]
    data['daily_logs'].append(entry)
    data['daily_logs'].sort(key=lambda x: x['date'])
    
    # Update streaks
    streaks = data.get('streaks', {'current': 0, 'best': 0, 'last_log_date': ''})
    last = streaks.get('last_log_date', '')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    if last == yesterday or last == today:
        if last != today:
            streaks['current'] = streaks.get('current', 0) + 1
    else:
        streaks['current'] = 1
    
    streaks['last_log_date'] = today
    streaks['best'] = max(streaks.get('best', 0), streaks['current'])
    data['streaks'] = streaks
    
    save_json(get_user_data_file(session['username']), data)
    return jsonify({'status': 'ok', 'streaks': streaks})

@app.route('/api/goal', methods=['POST'])
@login_required
def add_goal():
    data = load_json(get_user_data_file(session['username']))
    body = request.get_json()
    goal = {
        'id': datetime.now().timestamp(),
        'title': body.get('title', ''),
        'target': body.get('target', ''),
        'category': body.get('category', 'general'),
        'deadline': body.get('deadline', ''),
        'completed': False,
        'created': datetime.now().isoformat()
    }
    data.setdefault('goals', []).append(goal)
    save_json(get_user_data_file(session['username']), data)
    return jsonify({'status': 'ok', 'goal': goal})

@app.route('/api/goal/<float:goal_id>/toggle', methods=['POST'])
@login_required
def toggle_goal(goal_id):
    data = load_json(get_user_data_file(session['username']))
    for g in data.get('goals', []):
        if g['id'] == goal_id:
            g['completed'] = not g['completed']
            break
    save_json(get_user_data_file(session['username']), data)
    return jsonify({'status': 'ok'})

@app.route('/api/goal/<float:goal_id>', methods=['DELETE'])
@login_required
def delete_goal(goal_id):
    data = load_json(get_user_data_file(session['username']))
    data['goals'] = [g for g in data.get('goals', []) if g['id'] != goal_id]
    save_json(get_user_data_file(session['username']), data)
    return jsonify({'status': 'ok'})

@app.route('/api/reminder', methods=['POST'])
@login_required
def add_reminder():
    data = load_json(get_user_data_file(session['username']))
    body = request.get_json()
    reminder = {
        'id': datetime.now().timestamp(),
        'title': body.get('title', ''),
        'time': body.get('time', ''),
        'repeat': body.get('repeat', 'daily'),
        'active': True
    }
    data.setdefault('reminders', []).append(reminder)
    save_json(get_user_data_file(session['username']), data)
    return jsonify({'status': 'ok', 'reminder': reminder})

@app.route('/api/reminder/<float:rem_id>', methods=['DELETE'])
@login_required
def delete_reminder(rem_id):
    data = load_json(get_user_data_file(session['username']))
    data['reminders'] = [r for r in data.get('reminders', []) if r['id'] != rem_id]
    save_json(get_user_data_file(session['username']), data)
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
