// Global utilities and gear checkbox handlers

async function toggleGear(itemId) {
    try {
        const response = await fetch(`/gear/${itemId}/toggle`, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        if (response.ok) {
            const data = await response.json();
            
            // Обновляем визуальный стиль строки
            const itemRow = document.getElementById(`gear-item-${itemId}`);
            const itemText = document.getElementById(`gear-text-${itemId}`);
            const checkbox = document.getElementById(`gear-check-${itemId}`);
            
            if (checkbox) checkbox.checked = data.is_packed;
            if (itemText) {
                if (data.is_packed) {
                    itemText.classList.add('line-through', 'text-slate-400');
                } else {
                    itemText.classList.remove('line-through', 'text-slate-400');
                }
            }

            // Обновляем глобальный прогресс-бар
            const progressBar = document.getElementById('overall-progress-bar');
            const progressText = document.getElementById('overall-progress-text');
            const progressPercent = document.getElementById('overall-progress-percent');
            
            if (progressBar) progressBar.style.width = `${data.percent}%`;
            if (progressText) progressText.innerText = `Собрано: ${data.packed} из ${data.total}`;
            if (progressPercent) progressPercent.innerText = `${data.percent}%`;
            
            // Если все собрано — красивая анимация
            if (data.percent === 100) {
                progressBar.classList.add('from-emerald-400', 'to-teal-300');
            }
        }
    } catch (err) {
        console.error('Ошибка при сохранении снаряжения:', err);
    }
}

// Загрузка детального прогноза погоды для страницы поездки
async function loadWeatherForecast(lat, lng, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    container.innerHTML = `
        <div class="flex items-center justify-center py-12 text-slate-400 gap-3">
            <i class="fa-solid fa-spinner fa-spin text-emerald-400 text-2xl"></i>
            <span>Загрузка метеоданных и рыболовного барометра...</span>
        </div>
    `;

    try {
        const resp = await fetch(`/api/weather?lat=${lat}&lng=${lng}&days=7`);
        const data = await resp.json();
        
        if (data.status === 'success' && data.days && data.days.length > 0) {
            let html = `
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            `;
            
            data.days.forEach((day, index) => {
                const isToday = index === 0;
                const fishing = day.fishing || {};
                const dateObj = new Date(day.date);
                const dateFormatted = dateObj.toLocaleDateString('ru-RU', { weekday: 'short', day: 'numeric', month: 'short' });
                
                let badgeClass = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
                if (fishing.badge_color === 'amber') badgeClass = 'bg-amber-500/10 text-amber-400 border-amber-500/20';
                if (fishing.badge_color === 'rose') badgeClass = 'bg-rose-500/10 text-rose-400 border-rose-500/20';

                html += `
                    <div class="bg-slate-900/90 rounded-2xl p-4 border ${isToday ? 'border-emerald-500/40 shadow-lg shadow-emerald-950/30' : 'border-slate-800'} flex flex-col justify-between relative overflow-hidden">
                        ${isToday ? '<span class="absolute top-2 right-2 text-[10px] bg-emerald-500 text-slate-950 font-bold px-2 py-0.5 rounded-full">Сегодня</span>' : ''}
                        
                        <div>
                            <div class="flex items-center justify-between mb-2">
                                <span class="text-xs font-semibold uppercase tracking-wider text-slate-400">${dateFormatted}</span>
                                <span class="text-2xl">${day.icon}</span>
                            </div>
                            
                            <div class="flex items-baseline gap-2 mb-1">
                                <span class="text-2xl font-bold text-white">${day.temp_max > 0 ? '+' + day.temp_max : day.temp_max}°</span>
                                <span class="text-sm text-slate-400">ночь: ${day.temp_min > 0 ? '+' + day.temp_min : day.temp_min}°</span>
                            </div>
                            
                            <p class="text-xs text-slate-300 font-medium mb-3">${day.desc}</p>

                            <!-- Метео показатели -->
                            <div class="space-y-1.5 py-2 border-t border-b border-slate-800/80 text-xs">
                                <div class="flex items-center justify-between text-slate-400">
                                    <span class="flex items-center gap-1.5"><i class="fa-solid fa-gauge-high text-indigo-400"></i> Давление:</span>
                                    <span class="font-semibold text-slate-200">${day.pressure_mm} мм рт.ст.</span>
                                </div>
                                <div class="flex items-center justify-between text-slate-400">
                                    <span class="flex items-center gap-1.5"><i class="fa-solid fa-wind text-sky-400"></i> Ветер:</span>
                                    <span class="font-semibold text-slate-200">${day.wind_speed} км/ч</span>
                                </div>
                                <div class="flex items-center justify-between text-slate-400">
                                    <span class="flex items-center gap-1.5"><i class="fa-solid fa-cloud-rain text-blue-400"></i> Дождь:</span>
                                    <span class="font-semibold text-slate-200">${day.precipitation} мм (${day.precip_prob}%)</span>
                                </div>
                            </div>
                        </div>

                        <!-- Оценка клева / условия -->
                        <div class="mt-3 pt-2">
                            <div class="flex items-center justify-between mb-1.5">
                                <span class="text-[11px] font-semibold text-slate-400">Условия клева:</span>
                                <span class="text-xs font-bold px-2 py-0.5 rounded-full border ${badgeClass}">
                                    ${fishing.rating || 'Нормально'}
                                </span>
                            </div>
                            <div class="text-[11px] text-slate-300 bg-slate-950/60 p-2 rounded-lg border border-slate-800">
                                ${fishing.tips && fishing.tips.length > 0 ? fishing.tips[0] : 'Умеренные условия для отдыха и рыбалки.'}
                            </div>
                        </div>
                    </div>
                `;
            });
            
            html += `</div>`;
            container.innerHTML = html;
        } else {
            container.innerHTML = `
                <div class="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 text-center text-slate-400">
                    <i class="fa-solid fa-cloud-sun text-3xl mb-2 text-slate-400"></i>
                    <p>Не удалось получить данные о погоде для этих координат.</p>
                </div>
            `;
        }
    } catch (e) {
        console.error('Weather load error:', e);
        container.innerHTML = `<div class="text-rose-400 text-sm p-4">Ошибка загрузки погоды: ${e.message}</div>`;
    }
}
