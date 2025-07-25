document.addEventListener('DOMContentLoaded', function() {
    const analyzeButton = document.getElementById('analyze-button');
    const loadingSpinner = document.getElementById('loading-spinner');
    const resultsContainer = document.getElementById('results-container');

    let dailyIncursionsChart;

    if (analyzeButton) {
        analyzeButton.addEventListener('click', async () => {
            // 1. Reset UI and show loading spinner
            analyzeButton.disabled = true;
            loadingSpinner.classList.remove('hidden');
            resultsContainer.classList.add('hidden');
            const animatedCards = resultsContainer.querySelectorAll('.fade-in');
            animatedCards.forEach(card => card.classList.remove('fade-in'));

            try {
                // 2. Fetch data from the correct endpoint
                const response = await fetch('/analyze', { method: 'POST' });
                
                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({ message: '伺服器回應格式錯誤' }));
                    throw new Error(`伺服器錯誤: ${response.status} - ${errorData.message}`);
                }
                const data = await response.json();

                if (data.error) {
                    throw new Error(data.error);
                }

                // 3. Display results
                displayResults(data);

            } catch (error) {
                console.error('分析請求失敗:', error);
                alert(`發生錯誤：${error.message}`);
            } finally {
                // 4. Hide loading spinner and re-enable button
                loadingSpinner.classList.add('hidden');
                if (analyzeButton) {
                   analyzeButton.disabled = false;
                }
            }
        });
    }

    function displayResults(data) {
        resultsContainer.classList.remove('hidden');

        // Update all sections with the new data structure
        updateGauge(data.threat_probability);
        updateThreeMonthProbability(data.ai_report.three_month_probability);
        updateDataCards(data.indicators);
        updateAiReport(data.ai_report);
        updateDataSources(data.sources);
        updateCharts(data.indicators);

        // Staggered animation for a nicer reveal
        const cards = resultsContainer.querySelectorAll('.card, .grid-container, .chart-grid-single');
        cards.forEach((card, index) => {
            setTimeout(() => {
                card.classList.add('fade-in');
            }, index * 100);
        });
    }

    function updateGauge(probability) {
        const gaugeFill = document.querySelector('.gauge-fill');
        const percentageText = document.getElementById('threat-percentage');
        if (!gaugeFill || !percentageText) return;

        const prob = parseFloat(probability) || 0;
        const angle = (prob / 100) * 180;
        gaugeFill.style.setProperty('--gauge-angle', angle);
        percentageText.textContent = `${prob.toFixed(1)}%`;
    }

    function updateThreeMonthProbability(probData) {
        const percentageEl = document.getElementById('three-month-percentage');
        const justificationEl = document.getElementById('three-month-justification');
        if (!percentageEl || !justificationEl || !probData) return;

        const pyramidLayers = document.querySelectorAll('.pyramid-layer');

        const prob = parseInt(probData.percentage, 10);

        percentageEl.textContent = (prob >= 0) ? `${prob}` : 'N/A';
        justificationEl.innerHTML = probData.justification ? probData.justification.replace(/\n/g, '<br>') : 'N/A';

        pyramidLayers.forEach(layer => layer.classList.remove('highlight'));
        
        let currentLevelId = '';
        if (prob >= 80) { currentLevelId = 'level-5'; }
        else if (prob >= 60) { currentLevelId = 'level-4'; }
        else if (prob >= 40) { currentLevelId = 'level-3'; }
        else if (prob >= 20) { currentLevelId = 'level-2'; }
        else if (prob >= 0) { currentLevelId = 'level-1'; }
        
        if (currentLevelId) {
            const layer = document.getElementById(currentLevelId);
            if (layer) layer.classList.add('highlight');
        }
    }

    function updateDataCards(indicators) {
        if (!indicators) return;

        const latestIntrusionsEl = document.getElementById('latest-intrusions');
        if (latestIntrusionsEl) latestIntrusionsEl.textContent = indicators.military_latest_intrusions ?? '--';

        const totalIncursionsWeekEl = document.getElementById('total-incursions-week');
        if (totalIncursionsWeekEl) totalIncursionsWeekEl.textContent = indicators.military_total_incursions_last_week ?? '--';

        const totalNewsCountEl = document.getElementById('total-news-count');
        if (totalNewsCountEl) totalNewsCountEl.textContent = indicators.total_news_count ?? '--';
        
        const goldPriceEl = document.getElementById('gold-price');
        if (goldPriceEl) goldPriceEl.textContent = indicators.gold_price ?? '--';
        
        const goldChangeEl = document.getElementById('gold-change');
        if (goldChangeEl) {
            goldChangeEl.textContent = indicators.gold_price_change ?? '--';
            setChangeColor(goldChangeEl, indicators.gold_price_change);
        }
        
        const foodPriceEl = document.getElementById('food-price');
        if (foodPriceEl) foodPriceEl.textContent = indicators.food_price ?? '--';

        const foodChangeEl = document.getElementById('food-change');
        if (foodChangeEl) {
            foodChangeEl.textContent = indicators.food_price_change ?? '--';
            setChangeColor(foodChangeEl, indicators.food_price_change);
        }
    }
    
    function setChangeColor(element, value) {
        if (!element) return;
        element.classList.remove('positive', 'negative');
        if (typeof value !== 'string') return;
        if (value.startsWith('+')) {
            element.classList.add('positive');
        } else if (value.startsWith('-')) {
            element.classList.add('negative');
        }
    }

    function updateAiReport(report) {
        const zhReportContainer = document.getElementById('report-summary-zh');
        const enReportContainer = document.getElementById('report-summary-en');
        if (!zhReportContainer || !enReportContainer) return;
        
        zhReportContainer.innerHTML = '';
        enReportContainer.innerHTML = '';

        if (report && report.report_summary_zh && report.report_summary_zh.sections) {
            report.report_summary_zh.sections.forEach(section => {
                const sectionEl = document.createElement('div');
                sectionEl.innerHTML = `<h4>${section.heading}</h4><p>${section.content ? section.content.replace(/\n/g, '<br>') : ''}</p>`;
                zhReportContainer.appendChild(sectionEl);
            });
        }

        if (report && report.report_summary_en && report.report_summary_en.sections) {
            report.report_summary_en.sections.forEach(section => {
                const sectionEl = document.createElement('div');
                sectionEl.innerHTML = `<h4>${section.heading}</h4><p>${section.content ? section.content.replace(/\n/g, '<br>') : ''}</p>`;
                enReportContainer.appendChild(sectionEl);
            });
        }
    }

    function updateDataSources(sources) {
        const container = document.getElementById('data-sources-container');
        if (!container) return;
        container.innerHTML = ''; // Clear previous content
        if (!sources || Object.keys(sources).length === 0) {
            container.innerHTML = '<p>無可用數據來源。</p>';
            return;
        }

        const list = document.createElement('ul');
        list.className = 'sources-list';

        const categoryMap = {
            military: '軍事動態',
            economic: '經濟數據',
            diplomatic: '外交情資',
            public_opinion: '社會輿情'
        };

        // Sort keys to maintain a consistent order
        const sortedCategories = Object.keys(sources).sort((a, b) => {
            const order = ['military', 'economic', 'diplomatic', 'public_opinion'];
            return order.indexOf(a) - order.indexOf(b);
        });

        for (const category of sortedCategories) {
            const urls = sources[category];
            if (urls && urls.length > 0) {
                const displayName = categoryMap[category] || category.charAt(0).toUpperCase() + category.slice(1);
                
                const uniqueUrls = [...new Set(urls)]; // Remove duplicates

                const linksHtml = uniqueUrls.map(url => {
                    try {
                        return `<a href="${url}" target="_blank" rel="noopener noreferrer">${new URL(url).hostname}</a>`;
                    } catch (e) {
                        return `<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>`;
                    }
                }).join(', ');

                const listItem = document.createElement('li');
                listItem.innerHTML = `<strong>${displayName}:</strong> ${linksHtml}`;
                list.appendChild(listItem);
            }
        }
        
        container.appendChild(list);
    }

    function updateCharts(indicators) {
        if (!indicators || !indicators.military_daily_chart_data) return;

        const incursionsData = indicators.military_daily_chart_data;
        if (incursionsData && incursionsData.labels && incursionsData.data) {
            const incursionsCtx = document.getElementById('dailyIncursionsChart');
            if (!incursionsCtx) return;

            if (dailyIncursionsChart) {
                dailyIncursionsChart.destroy();
            }
            dailyIncursionsChart = new Chart(incursionsCtx.getContext('2d'), createChartConfig(
                incursionsData.labels, 
                incursionsData.data, 
                '共軍擾台兵力', 
                '#f85149'
            ));
        }
        // Gold and Food charts have been removed.
    }

    function createChartConfig(labels, data, label, color) {
        return {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: label,
                    data: data,
                    backgroundColor: color,
                    borderColor: color,
                    borderWidth: 1,
                    borderRadius: 4,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { color: 'white', font: { family: "'Inter', sans-serif" } },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' }
                    },
                    x: {
                        ticks: { color: 'white', font: { family: "'Inter', sans-serif" } },
                        grid: { display: false }
                    }
                }
            }
        };
    }
});
