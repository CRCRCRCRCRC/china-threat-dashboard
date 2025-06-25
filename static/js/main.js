document.addEventListener('DOMContentLoaded', function() {
    const analyzeButton = document.getElementById('analyze-button');
    const loadingSpinner = document.getElementById('loading-spinner');
    const resultsContainer = document.getElementById('results-container');
    const aiReportContainer = document.getElementById('ai-report-container');
    const radarChartContainer = document.getElementById('radar-chart-container');
    const userCreditsSpan = document.getElementById('user-credits');

    let radarChart;

    if (analyzeButton) {
        analyzeButton.addEventListener('click', analyze);
    }

    async function analyze() {
        // 1. Reset UI and show loading spinner
        analyzeButton.disabled = true;
        loadingSpinner.classList.remove('hidden');
        resultsContainer.classList.add('hidden');
        if (aiReportContainer) aiReportContainer.classList.add('hidden');
        if (radarChartContainer) radarChartContainer.classList.add('hidden');

        // Reset previous results
        resetUI();

        try {
            // 2. Fetch initial indicators data
            const response = await fetch('/analyze', { method: 'POST' });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: '伺服器回應格式錯誤' }));
                throw new Error(`伺服器錯誤: ${response.status} - ${errorData.error}`);
            }
            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            // 3. Immediately display indicator results
            displayInitialResults(data);
            
            // 4. Start polling for the full report
            if (data.task_id) {
                pollForReport(data.task_id);
            } else {
                throw new Error('未收到報告生成任務ID');
            }

        } catch (error) {
            console.error('分析請求失敗:', error);
            const reportContent = document.getElementById('report-content');
            if(reportContent) reportContent.innerHTML = `<div class="error-message">分析啟動失敗：${error.message}</div>`;
            showAiReportUI("分析啟動失敗");
            loadingSpinner.classList.add('hidden');
            analyzeButton.disabled = false;
        }
    }

    function pollForReport(taskId, interval = 3000, maxAttempts = 20) {
        let attempts = 0;
        const intervalId = setInterval(async () => {
            if (attempts >= maxAttempts) {
                clearInterval(intervalId);
                showAiReportUI("報告生成超時，請稍後重試。");
                analyzeButton.disabled = false;
                loadingSpinner.classList.add('hidden');
                return;
            }

            try {
                const response = await fetch(`/get_report/${taskId}`);
                const result = await response.json();

                if (response.ok) {
                    if (result.status === 'completed') {
                        clearInterval(intervalId);
                        displayFinalReport(result);
                        loadingSpinner.classList.add('hidden');
                        analyzeButton.disabled = false;
                    } else if (result.status === 'failed') {
                        clearInterval(intervalId);
                        throw new Error(result.error || '報告生成失敗');
                    }
                    // If 'pending', do nothing and wait for the next poll.
                } else {
                     // Handle non-ok responses, e.g. 404
                    if (response.status === 404) {
                       // continue polling
                    } else {
                       throw new Error(`獲取報告時伺服器錯誤: ${response.status}`);
                    }
                }
            } catch (error) {
                clearInterval(intervalId);
                console.error('輪詢報告時發生錯誤:', error);
                showAiReportUI(`獲取報告失敗：${error.message}`);
                loadingSpinner.classList.add('hidden');
                analyzeButton.disabled = false;
            }
            attempts++;
        }, interval);
    }
    
    function resetUI() {
        // Clear previous report content
        const reportContent = document.getElementById('report-content');
        if(reportContent) reportContent.innerHTML = '';
        const chartContainer = document.getElementById('radar-chart');
        if (chartContainer) chartContainer.innerHTML = ''; // Clear old canvas if any
    }

    function displayInitialResults(data) {
        resultsContainer.classList.remove('hidden');

        // Update data cards
        if (data.indicators) {
            updateDataCards(data.indicators);
        }
        
        // Update data sources
        if(data.sources) {
            updateDataSources(data.sources);
        }

        // Show AI report section with a "loading" message
        showAiReportUI("AI 報告生成中，請稍候...");

        // Staggered animation
        const cards = resultsContainer.querySelectorAll('.card, .grid-container, .chart-grid-single');
        cards.forEach((card, index) => {
            setTimeout(() => card.classList.add('fade-in'), index * 100);
        });
    }

    function displayFinalReport(data) {
        // Update AI report with final content
        if (data.report) {
            showAiReportUI(data.report);
        } else {
            showAiReportUI("報告為空。");
        }

        // Update radar chart
        if (data.chart_image_url) {
            const chartContainer = document.getElementById('radar-chart');
            if (chartContainer) {
                chartContainer.innerHTML = `<img src="${data.chart_image_url}" alt="威脅指標雷達圖" class="w-full h-auto">`;
                if(radarChartContainer) radarChartContainer.classList.remove('hidden');
            }
        }
        
        // Update user credits
        if (data.updated_credits !== undefined && userCreditsSpan) {
            userCreditsSpan.textContent = data.updated_credits;
            userCreditsSpan.classList.add('highlight-update');
            setTimeout(() => userCreditsSpan.classList.remove('highlight-update'), 1500);
        }
    }

    function showAiReportUI(content) {
        if (aiReportContainer) aiReportContainer.classList.remove('hidden');
        const reportContent = document.getElementById('report-content');
        
        if (reportContent) {
            // Use a library like 'marked' in a real project for security.
            // For now, simple replacement.
            let htmlContent = content.replace(/\n/g, '<br>');
            htmlContent = htmlContent.replace(/### (.*?)(<br>|$)/g, '<h3>$1</h3>');
            htmlContent = htmlContent.replace(/#### (.*?)(<br>|$)/g, '<h4>$1</h4>');
            htmlContent = htmlContent.replace(/\*\* (.*?)(<br>|$)/g, '<strong>$1</strong>');
            
            reportContent.innerHTML = htmlContent;
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
        if (!element) return;
        element.classList.remove('positive', 'negative');
        if (typeof value !== 'string') return;
        if (value.startsWith('+')) {
            element.classList.add('positive');
        } else if (value.startsWith('-')) {
            element.classList.add('negative');
        }
    }

    function updateDataSources(sources) {
        const container = document.getElementById('data-sources-container');
        if (!container) return;
        container.innerHTML = '';
        if (!sources) return;

        const list = document.createElement('ul');

        const createLink = (url) => `<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>`;

        const militarySource = sources.military ? `<li><strong>軍事動態:</strong> ${createLink(sources.military)}</li>` : '';
        const goldSource = sources.gold ? `<li><strong>黃金價格:</strong> ${createLink(sources.gold)}</li>` : '';
        const foodSource = sources.food ? `<li><strong>糧食價格:</strong> ${createLink(sources.food)}</li>` : '';
        
        let newsSourceItems = '';
        if (sources.news) {
            // Flatten the news sources from the new structure
             const allNewsUrls = Object.values(sources.news).flat();
             if (allNewsUrls.length > 0) {
                 newsSourceItems += `<li><strong>相關新聞:</strong> ${allNewsUrls.map(createLink).join(', ')}</li>`;
             }
        }
        
        list.innerHTML = `${militarySource}${goldSource}${foodSource}${newsSourceItems}`;
        container.appendChild(list);
    }

    // Since radar chart is now an image, we don't need Chart.js logic here anymore.
    // The chart update logic is now in displayFinalReport.
});
