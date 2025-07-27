document.addEventListener('DOMContentLoaded', function() {
    const analyzeButton = document.getElementById('analyze-button');
    const loadingDiv = document.getElementById('loading');
    const loadingPhase = document.getElementById('loading-phase');
    const progressFill = document.getElementById('progress-fill');
    const threatIndicators = document.getElementById('threat-indicators');
    const threatLevel = document.getElementById('threat-level');
    const analysisSection = document.getElementById('analysis-section');
    const dataSection = document.getElementById('data-section');
    
    let currentTaskId = null;
    let progress = 0;

    analyzeButton.addEventListener('click', function() {
        startAnalysis();
    });

    function startAnalysis() {
        // 重置界面
        hideAllSections();
        showLoading();
        analyzeButton.disabled = true;
        analyzeButton.textContent = '分析中...';
        
        // 開始分析
        fetch('/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.task_id) {
                currentTaskId = data.task_id;
                startProgressUpdates();
            } else {
                showError('無法啟動分析任務');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showError('連接錯誤，請稍後再試');
        });
    }

    function startProgressUpdates() {
        const interval = setInterval(() => {
            if (!currentTaskId) {
                clearInterval(interval);
                return;
            }

            fetch(`/get_report/${currentTaskId}`)
                .then(response => response.json())
                .then(data => {
                    updateProgress(data);
                    
                    if (data.status === 'completed') {
                        clearInterval(interval);
                        showResults(data);
                    } else if (data.status === 'failed') {
                        clearInterval(interval);
                        showError(data.report || '分析失敗');
                    }
                })
                .catch(error => {
                    console.error('Error polling:', error);
                });
        }, 2000);
    }

    function updateProgress(data) {
        if (data.phase === 'indicators') {
            loadingPhase.textContent = '正在收集威脅情報...';
            progress = 30;
        } else if (data.phase === 'report') {
            loadingPhase.textContent = '正在生成 AI 分析報告...';
            progress = 70;
        }
        
        progressFill.style.width = progress + '%';
    }

    function showResults(data) {
        hideLoading();
        
        // 顯示威脅指標
        if (data.indicators) {
            displayThreatIndicators(data.indicators);
        }
        
        // 顯示總體威脅等級
        if (data.threat_level !== undefined) {
            displayThreatLevel(data.threat_level);
        }
        
        // 顯示 AI 報告
        if (data.report) {
            displayAiReport(data.report);
        }
        
        // 顯示詳細數據
        if (data.raw_data) {
            displayDetailedData(data.raw_data);
        }
        
        // 重置按鈕
        analyzeButton.disabled = false;
        analyzeButton.textContent = '啟動威脅掃描';
    }

    function displayThreatIndicators(indicators) {
        document.getElementById('military-indicator').textContent = indicators.military + '/100';
        document.getElementById('economic-indicator').textContent = indicators.economic + '/100';
        document.getElementById('news-indicator').textContent = indicators.news + '/100';
        
        document.getElementById('military-details').textContent = getThreatDescription(indicators.military);
        document.getElementById('economic-details').textContent = getThreatDescription(indicators.economic);
        document.getElementById('news-details').textContent = getThreatDescription(indicators.news);
        
        threatIndicators.style.display = 'block';
    }

    function displayThreatLevel(threatLevel) {
        document.getElementById('threat-value').textContent = threatLevel + '%';
        document.getElementById('threat-description').textContent = getOverallThreatDescription(threatLevel);
        
        threatLevel.style.display = 'block';
    }

    function displayAiReport(report) {
        document.getElementById('report-content').innerHTML = formatReport(report);
        analysisSection.style.display = 'block';
    }

    function displayDetailedData(rawData) {
        // 軍事數據
        if (rawData.military) {
            const militaryHtml = `
                <p><strong>過去一週擾台次數：</strong>${rawData.military.total_incursions_last_week || 0} 次</p>
                <p><strong>最新共機：</strong>${rawData.military.latest_aircrafts || 0} 架次</p>
                <p><strong>最新共艦：</strong>${rawData.military.latest_ships || 0} 艘次</p>
            `;
            document.getElementById('military-data').innerHTML = militaryHtml;
        }
        
        // 經濟數據
        const economicHtml = [];
        if (rawData.gold) {
            economicHtml.push(`<p><strong>黃金價格：</strong>$${rawData.gold.current_price || 'N/A'}/oz</p>`);
            economicHtml.push(`<p><strong>日變動：</strong>${rawData.gold.daily_change_percent || 0}%</p>`);
        }
        if (rawData.food) {
            economicHtml.push(`<p><strong>小麥價格：</strong>$${rawData.food.wheat_price || 'N/A'}/蒲式耳</p>`);
            economicHtml.push(`<p><strong>日變動：</strong>${rawData.food.daily_change_percent || 0}%</p>`);
        }
        document.getElementById('economic-data').innerHTML = economicHtml.join('');
        
        // 新聞數據
        if (rawData.news) {
            const newsHtml = `
                <p><strong>總新聞數：</strong>${rawData.news.total_articles || 0} 篇</p>
                <p><strong>經濟新聞：</strong>${rawData.news.economic_news?.length || 0} 篇</p>
                <p><strong>外交新聞：</strong>${rawData.news.diplomatic_news?.length || 0} 篇</p>
                <p><strong>輿情新聞：</strong>${rawData.news.public_opinion_news?.length || 0} 篇</p>
            `;
            document.getElementById('news-data').innerHTML = newsHtml;
        }
        
        dataSection.style.display = 'block';
    }

    function getThreatDescription(score) {
        if (score >= 80) return '極高威脅';
        if (score >= 60) return '高威脅';
        if (score >= 40) return '中等威脅';
        if (score >= 20) return '低威脅';
        return '極低威脅';
    }

    function getOverallThreatDescription(level) {
        if (level >= 80) return '情勢高度緊張，需要密切關注';
        if (level >= 60) return '情勢較為緊張，保持警戒';
        if (level >= 40) return '情勢穩定，持續監控';
        if (level >= 20) return '情勢相對穩定';
        return '情勢平靜';
    }

    function formatReport(report) {
        // 簡單的文本格式化
        return report.replace(/\n/g, '<br>').replace(/【([^】]+)】/g, '<h3>$1</h3>');
    }

    function hideAllSections() {
        threatIndicators.style.display = 'none';
        threatLevel.style.display = 'none';
        analysisSection.style.display = 'none';
        dataSection.style.display = 'none';
    }

    function showLoading() {
        loadingDiv.style.display = 'block';
        progress = 10;
        progressFill.style.width = progress + '%';
        loadingPhase.textContent = '初始化威脅掃描...';
    }

    function hideLoading() {
        loadingDiv.style.display = 'none';
    }

    function showError(message) {
        hideLoading();
        alert('錯誤：' + message);
        analyzeButton.disabled = false;
        analyzeButton.textContent = '啟動威脅掃描';
    }
});
