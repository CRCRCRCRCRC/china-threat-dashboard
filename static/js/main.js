document.addEventListener('DOMContentLoaded', function() {
    const analyzeButton = document.getElementById('analyze-button');
    const loadingSpinner = document.getElementById('loading-spinner');
    const resultsContainer = document.getElementById('results-container');
    const aiReportContainer = document.getElementById('ai-report-container');
    const userCreditsSpan = document.getElementById('user-credits');
    const reportContentEl = document.getElementById('report-content');
    const chartCanvas = document.getElementById('radar-chart');

    let radarChartInstance;

    if (analyzeButton) {
        analyzeButton.addEventListener('click', analyze);
    }

    async function analyze() {
        analyzeButton.disabled = true;
        loadingSpinner.classList.remove('hidden');
        resultsContainer.classList.add('hidden');
        aiReportContainer.classList.add('hidden');
        resetUI();

        try {
            const response = await fetch('/analyze', { method: 'POST' });
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: '伺服器回應格式錯誤' }));
                throw new Error(`分析啟動失敗: ${response.status} - ${errorData.error || '未知錯誤'}`);
            }
            const data = await response.json();
            if (data.error) throw new Error(data.error);
            if (data.task_id) {
                pollForReport(data.task_id);
            } else {
                throw new Error('未收到分析任務ID');
            }
        } catch (error) {
            console.error('分析請求失敗:', error);
            showErrorState(error.message);
        }
    }

    function pollForReport(taskId, interval = 3000, maxAttempts = 50) {
        let attempts = 0;
        let indicatorsDisplayed = false;

        const intervalId = setInterval(async () => {
            if (attempts >= maxAttempts) {
                clearInterval(intervalId);
                showErrorState("報告生成超時，請稍後重試或檢查伺服器狀態。");
                return;
            }
            try {
                const response = await fetch(`/get_report/${taskId}`);
                if (!response.ok) throw new Error(`獲取狀態時伺服器錯誤: ${response.status}`);
                const result = await response.json();

                if (result.status === 'processing' && !indicatorsDisplayed && result.phase === 'indicators' && result.indicators) {
                    displayInitialResults(result);
                    indicatorsDisplayed = true;
                } else if (result.status === 'completed') {
                    clearInterval(intervalId);
                    if (!indicatorsDisplayed) displayInitialResults(result);
                    displayFinalReport(result);
                } else if (result.status === 'failed') {
                    clearInterval(intervalId);
                    throw new Error(result.report || '報告生成失敗');
                }
            } catch (error) {
                clearInterval(intervalId);
                console.error('輪詢報告時發生錯誤:', error);
                showErrorState(`獲取報告失敗：${error.message}`);
            }
            attempts++;
        }, interval);
    }
    
    function resetUI() {
        if (radarChartInstance) {
            radarChartInstance.destroy();
        }
        reportContentEl.innerHTML = '';
        resultsContainer.classList.add('hidden');
        aiReportContainer.classList.add('hidden');
        updateDataCards({}); 
    }

    function displayInitialResults(data) {
        loadingSpinner.classList.add('hidden');
        resultsContainer.classList.remove('hidden');
        if (data.indicators) updateDataCards(data.indicators);
        if (data.sources) updateDataSources(data.sources);

        showAiReportUI("<h4>AI 報告生成中...</h4><p>正在綜合所有數據，請稍候。</p>");
        aiReportContainer.classList.remove('hidden');

        const cards = resultsContainer.querySelectorAll('.card');
        cards.forEach((card, index) => {
            setTimeout(() => card.classList.add('fade-in'), index * 100);
        });
    }

<<<<<<< HEAD
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
=======
    function displayFinalReport(data) {
        if (data.report) showAiReportUI(data.report);
        if (data.chart_data) renderRadarChart(data.chart_data);
        if (data.updated_credits !== undefined) {
            userCreditsSpan.textContent = data.updated_credits;
            userCreditsSpan.classList.add('highlight-update');
            setTimeout(() => userCreditsSpan.classList.remove('highlight-update'), 1500);
        }
        analyzeButton.disabled = false;
        loadingSpinner.classList.add('hidden');
>>>>>>> 582f439752d7dd09671e0ddbe1ded2923f47c81d
    }

    function renderRadarChart(chartData) {
        if (radarChartInstance) {
            radarChartInstance.destroy();
        }
        const ctx = chartCanvas.getContext('2d');
        radarChartInstance = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: chartData.labels,
                datasets: [{
                    label: '威脅指標',
                    data: chartData.data,
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        angleLines: { color: 'rgba(255, 255, 255, 0.2)' },
                        grid: { color: 'rgba(255, 255, 255, 0.2)' },
                        pointLabels: { color: 'white', font: { size: 14 } },
                        ticks: {
                            color: 'white',
                            backdropColor: 'rgba(0, 0, 0, 0.5)',
                            stepSize: 25,
                            beginAtZero: true,
                            max: 100
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }
    
    function showErrorState(errorMessage) {
        loadingSpinner.classList.add('hidden');
        resultsContainer.classList.remove('hidden');
        aiReportContainer.classList.remove('hidden');
        showAiReportUI(`<div class="error-message">${errorMessage}</div>`);
        analyzeButton.disabled = false;
    }

    function showAiReportUI(content) {
        if (reportContentEl) {
            reportContentEl.innerHTML = marked.parse(content);
        }
    }

    function updateDataCards(indicators) {
        if (!indicators) return;
        const setCardValue = (id, value, changeId = null, changeValue = null) => {
            const el = document.getElementById(id);
            if (el) el.textContent = value ?? '--';
            if (changeId && changeValue) {
                const changeEl = document.getElementById(changeId);
                if (changeEl) {
                    changeEl.textContent = changeValue ?? '--';
                    setChangeColor(changeEl, changeValue);
                }
            }
        };

        setCardValue('latest-intrusions', indicators.military_latest_intrusions);
        setCardValue('total-incursions-week', indicators.military_total_incursions_last_week);
        setCardValue('total-news-count', indicators.total_news_count);
        setCardValue('gold-price', indicators.gold_price, 'gold-change', indicators.gold_price_change);
        setCardValue('food-price', indicators.food_price, 'food-change', indicators.food_price_change);
    }
    
    function setChangeColor(element, value) {
        if (!element || typeof value !== 'string') return;
        element.classList.remove('positive', 'negative');
        if (value.startsWith('+')) element.classList.add('positive');
        else if (value.startsWith('-')) element.classList.add('negative');
    }

    function updateDataSources(sources) {
        const container = document.getElementById('data-sources-container');
        if (!container || !sources) return;
        container.innerHTML = '';
        const list = document.createElement('ul');

        const createLink = (url) => url && url !== '#' ? `<a href="${url}" target="_blank" rel="noopener noreferrer" class="source-link">${new URL(url).hostname}</a>` : '<span>N/A</span>';

        let listItems = '';
        if (sources.military) listItems += `<li><strong>軍事動態:</strong> ${createLink(sources.military)}</li>`;
        if (sources.gold) listItems += `<li><strong>黃金價格:</strong> ${createLink(sources.gold)}</li>`;
        if (sources.food) listItems += `<li><strong>糧食價格:</strong> ${createLink(sources.food)}</li>`;

        if (sources.news) {
            const publisherLinks = Object.entries(sources.news)
                .map(([name, url]) => `<a href="${url}" target="_blank" rel="noopener noreferrer" class="source-link">${name}</a>`)
                .join(', ');
            if(publisherLinks) listItems += `<li><strong>新聞來源:</strong> ${publisherLinks}</li>`;
        }
        
        list.innerHTML = listItems;
        container.appendChild(list);
    }
});
