// ============================================
// HealthPulse - Frontend JavaScript
// ============================================

// Navigation
document.querySelectorAll('.nav-item[data-section]').forEach(item => {
    item.addEventListener('click', e => {
        e.preventDefault();
        const section = item.dataset.section;
        document.querySelectorAll('.nav-item[data-section]').forEach(n => n.classList.remove('active'));
        item.classList.add('active');
        document.querySelectorAll('.content-section').forEach(s => s.classList.remove('active'));
        document.getElementById('section-' + section).classList.add('active');
        // Close sidebar on mobile
        document.getElementById('sidebar').classList.remove('open');
        // Init charts when analytics/calories section opens
        if (section === 'analytics') initAnalyticsCharts();
        if (section === 'calories') initCalorieChart();
        if (section === 'overview') initOverviewChart();
    });
});

function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('open');
}

// Toast notification
function showToast(message, isError = false) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = 'toast show' + (isError ? ' error' : '');
    setTimeout(() => toast.className = 'toast', 3000);
}

// API helper
async function apiCall(url, method = 'POST', data = null) {
    const opts = { method, headers: { 'Content-Type': 'application/json' } };
    if (data) opts.body = JSON.stringify(data);
    const res = await fetch(url, opts);
    return res.json();
}

// Daily Log Form
document.getElementById('dailyLogForm').addEventListener('submit', async e => {
    e.preventDefault();
    const data = {
        calories: document.getElementById('logCalories').value || 0,
        water: document.getElementById('logWater').value || 0,
        sleep: document.getElementById('logSleep').value || 0,
        steps: document.getElementById('logSteps').value || 0,
        exercise: document.getElementById('logExercise').value || 0,
        mood: document.getElementById('logMood').value,
        notes: document.getElementById('logNotes').value
    };
    const result = await apiCall('/api/log', 'POST', data);
    if (result.status === 'ok') {
        showToast('✅ Daily log saved! Streak: ' + result.streaks.current + ' days');
        setTimeout(() => location.reload(), 1000);
    } else {
        showToast('Failed to save log', true);
    }
});

// Profile Form
document.getElementById('profileForm').addEventListener('submit', async e => {
    e.preventDefault();
    const data = {
        name: document.getElementById('profileName').value,
        age: document.getElementById('profileAge').value,
        height: document.getElementById('profileHeight').value,
        weight: document.getElementById('profileWeight').value,
        gender: document.getElementById('profileGender').value
    };
    const result = await apiCall('/api/profile', 'POST', data);
    if (result.status === 'ok') {
        showToast('✅ Profile updated!');
        setTimeout(() => location.reload(), 1000);
    }
});

// Goal Form
document.getElementById('goalForm').addEventListener('submit', async e => {
    e.preventDefault();
    const data = {
        title: document.getElementById('goalTitle').value,
        category: document.getElementById('goalCategory').value,
        target: document.getElementById('goalTarget').value,
        deadline: document.getElementById('goalDeadline').value
    };
    if (!data.title) return;
    const result = await apiCall('/api/goal', 'POST', data);
    if (result.status === 'ok') {
        showToast('🎯 Goal added!');
        setTimeout(() => location.reload(), 800);
    }
});

async function toggleGoal(id) {
    await apiCall('/api/goal/' + id + '/toggle');
    location.reload();
}

async function deleteGoal(id) {
    if (!confirm('Delete this goal?')) return;
    await apiCall('/api/goal/' + id, 'DELETE');
    location.reload();
}

// Reminder Form
document.getElementById('reminderForm').addEventListener('submit', async e => {
    e.preventDefault();
    const data = {
        title: document.getElementById('reminderTitle').value,
        time: document.getElementById('reminderTime').value,
        repeat: document.getElementById('reminderRepeat').value
    };
    if (!data.title || !data.time) return;
    const result = await apiCall('/api/reminder', 'POST', data);
    if (result.status === 'ok') {
        showToast('🔔 Reminder set!');
        setTimeout(() => location.reload(), 800);
    }
});

async function deleteReminder(id) {
    if (!confirm('Delete this reminder?')) return;
    await apiCall('/api/reminder/' + id, 'DELETE');
    location.reload();
}

// Browser notification for reminders
function checkReminders() {
    if (!('Notification' in window)) return;
    if (Notification.permission === 'default') Notification.requestPermission();
    
    const now = new Date();
    const currentTime = now.getHours().toString().padStart(2,'0') + ':' + now.getMinutes().toString().padStart(2,'0');
    
    document.querySelectorAll('.reminder-item').forEach(item => {
        const timeEl = item.querySelector('.reminder-info span');
        if (timeEl && timeEl.textContent.includes(currentTime)) {
            const title = item.querySelector('h4').textContent;
            if (Notification.permission === 'granted') {
                new Notification('HealthPulse Reminder', { body: title, icon: '💊' });
            }
        }
    });
}
setInterval(checkReminders, 60000);

// ============ CHARTS ============
const chartDefaults = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: { legend: { labels: { color: '#94a3b8', font: { family: 'Inter' } } } },
    scales: {
        x: { ticks: { color: '#64748b' }, grid: { color: 'rgba(42,46,66,0.5)' } },
        y: { ticks: { color: '#64748b' }, grid: { color: 'rgba(42,46,66,0.5)' } }
    }
};

let overviewChart, calChart, sleepChart, stepsChart, waterChart, calHistChart;

function initOverviewChart() {
    if (overviewChart) overviewChart.destroy();
    const labels = weeklyLogs.map(l => l.date.slice(5));
    const ctx = document.getElementById('weeklyOverviewChart');
    if (!ctx) return;
    overviewChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: [
                { label: 'Calories (÷10)', data: weeklyLogs.map(l => Math.round((l.calories||0)/10)), borderColor: '#ef4444', backgroundColor: 'rgba(239,68,68,0.1)', fill: true, tension: 0.4 },
                { label: 'Steps (÷100)', data: weeklyLogs.map(l => Math.round((l.steps||0)/100)), borderColor: '#10b981', backgroundColor: 'rgba(16,185,129,0.1)', fill: true, tension: 0.4 },
                { label: 'Sleep (h)', data: weeklyLogs.map(l => l.sleep||0), borderColor: '#8b5cf6', backgroundColor: 'rgba(139,92,246,0.1)', fill: true, tension: 0.4 },
                { label: 'Water', data: weeklyLogs.map(l => l.water||0), borderColor: '#0ea5e9', backgroundColor: 'rgba(14,165,233,0.1)', fill: true, tension: 0.4 }
            ]
        },
        options: chartDefaults
    });
}

function initAnalyticsCharts() {
    const logs = allLogs;
    const labels = logs.map(l => l.date.slice(5));
    
    if (calChart) calChart.destroy();
    if (sleepChart) sleepChart.destroy();
    if (stepsChart) stepsChart.destroy();
    if (waterChart) waterChart.destroy();

    const cc = document.getElementById('caloriesChart');
    if (cc) calChart = new Chart(cc, {
        type: 'bar', data: { labels, datasets: [{ label: 'Calories', data: logs.map(l=>l.calories||0), backgroundColor: 'rgba(239,68,68,0.6)', borderColor: '#ef4444', borderWidth: 1, borderRadius: 6 }] }, options: chartDefaults
    });

    const sc = document.getElementById('sleepChart');
    if (sc) sleepChart = new Chart(sc, {
        type: 'line', data: { labels, datasets: [{ label: 'Hours', data: logs.map(l=>l.sleep||0), borderColor: '#8b5cf6', backgroundColor: 'rgba(139,92,246,0.15)', fill: true, tension: 0.4 }] }, options: chartDefaults
    });

    const stc = document.getElementById('stepsChart');
    if (stc) stepsChart = new Chart(stc, {
        type: 'bar', data: { labels, datasets: [{ label: 'Steps', data: logs.map(l=>l.steps||0), backgroundColor: 'rgba(16,185,129,0.6)', borderColor: '#10b981', borderWidth: 1, borderRadius: 6 }] }, options: chartDefaults
    });

    const wc = document.getElementById('waterChart');
    if (wc) waterChart = new Chart(wc, {
        type: 'line', data: { labels, datasets: [{ label: 'Glasses', data: logs.map(l=>l.water||0), borderColor: '#0ea5e9', backgroundColor: 'rgba(14,165,233,0.15)', fill: true, tension: 0.4 }] }, options: chartDefaults
    });
}

function initCalorieChart() {
    if (calHistChart) calHistChart.destroy();
    const logs = allLogs;
    const labels = logs.map(l => l.date.slice(5));
    const ctx = document.getElementById('calorieHistoryChart');
    if (!ctx) return;
    calHistChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'Calories',
                data: logs.map(l => l.calories || 0),
                backgroundColor: logs.map(l => (l.calories||0) > 2500 ? 'rgba(239,68,68,0.6)' : (l.calories||0) < 1200 ? 'rgba(245,158,11,0.6)' : 'rgba(16,185,129,0.6)'),
                borderRadius: 6
            }]
        },
        options: { ...chartDefaults, plugins: { ...chartDefaults.plugins, legend: { display: false } } }
    });
}

// Init overview chart on load
window.addEventListener('DOMContentLoaded', () => {
    initOverviewChart();
});
