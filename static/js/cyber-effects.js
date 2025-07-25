// 賽博朋克特效增強
document.addEventListener('DOMContentLoaded', function() {
    
    // 添加掃描線效果
    function createScanLines() {
        const scanLine = document.createElement('div');
        scanLine.className = 'scan-line';
        scanLine.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 2px;
            background: linear-gradient(90deg, transparent, #00ffff, transparent);
            z-index: 9999;
            pointer-events: none;
            animation: scan 3s linear infinite;
        `;
        
        const style = document.createElement('style');
        style.textContent = `
            @keyframes scan {
                0% { transform: translateY(-2px); opacity: 0; }
                10% { opacity: 1; }
                90% { opacity: 1; }
                100% { transform: translateY(100vh); opacity: 0; }
            }
        `;
        document.head.appendChild(style);
        document.body.appendChild(scanLine);
        
        // 每5秒創建一次掃描線
        setTimeout(createScanLines, 5000);
    }
    
    // 啟動掃描線效果
    setTimeout(createScanLines, 2000);
    
    // 添加鼠標跟蹤光效
    let mouseGlow = null;
    
    function createMouseGlow() {
        mouseGlow = document.createElement('div');
        mouseGlow.style.cssText = `
            position: fixed;
            width: 200px;
            height: 200px;
            background: radial-gradient(circle, rgba(0, 255, 255, 0.1) 0%, transparent 70%);
            border-radius: 50%;
            pointer-events: none;
            z-index: 9998;
            transition: all 0.1s ease;
        `;
        document.body.appendChild(mouseGlow);
    }
    
    createMouseGlow();
    
    document.addEventListener('mousemove', function(e) {
        if (mouseGlow) {
            mouseGlow.style.left = (e.clientX - 100) + 'px';
            mouseGlow.style.top = (e.clientY - 100) + 'px';
        }
    });
    
    // 數字跳動效果
    function animateNumber(element, start, end, duration = 1000) {
        const startTime = performance.now();
        
        function update(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            const current = Math.floor(start + (end - start) * progress);
            element.textContent = current + (element.textContent.includes('%') ? '%' : '');
            
            if (progress < 1) {
                requestAnimationFrame(update);
            }
        }
        
        requestAnimationFrame(update);
    }
    
    // 為數據卡片添加特效
    function enhanceDataCards() {
        const dataCards = document.querySelectorAll('.data-card');
        dataCards.forEach((card, index) => {
            card.style.animationDelay = (index * 0.1) + 's';
            card.classList.add('cyber-fade-in');
        });
    }
    
    // 添加CSS動畫
    const cyberStyle = document.createElement('style');
    cyberStyle.textContent = `
        .cyber-fade-in {
            animation: cyberFadeIn 0.8s ease-out forwards;
            opacity: 0;
            transform: translateY(30px);
        }
        
        @keyframes cyberFadeIn {
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .glitch-text {
            animation: glitch 2s infinite;
        }
        
        @keyframes glitch {
            0%, 100% { transform: translate(0); }
            20% { transform: translate(-1px, 1px); }
            40% { transform: translate(-1px, -1px); }
            60% { transform: translate(1px, 1px); }
            80% { transform: translate(1px, -1px); }
        }
        
        .neon-pulse {
            animation: neonPulse 2s ease-in-out infinite alternate;
        }
        
        @keyframes neonPulse {
            from { text-shadow: 0 0 10px currentColor, 0 0 20px currentColor; }
            to { text-shadow: 0 0 20px currentColor, 0 0 30px currentColor, 0 0 40px currentColor; }
        }
    `;
    document.head.appendChild(cyberStyle);
    
    // 監聽結果顯示
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList') {
                const resultsContainer = document.getElementById('results-container');
                if (resultsContainer && !resultsContainer.classList.contains('hidden')) {
                    enhanceDataCards();
                    
                    // 為威脅百分比添加特效
                    const threatPercentage = document.getElementById('threat-percentage');
                    if (threatPercentage && threatPercentage.textContent !== '0%') {
                        threatPercentage.classList.add('neon-pulse');
                    }
                }
            }
        });
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    
    // 為按鈕添加音效模擬（視覺反饋）
    const analyzeButton = document.getElementById('analyze-button');
    if (analyzeButton) {
        analyzeButton.addEventListener('click', function() {
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = '';
            }, 150);
        });
    }
    
    // 添加隨機故障效果
    function randomGlitch() {
        const elements = document.querySelectorAll('h1, h3, .level-name');
        const randomElement = elements[Math.floor(Math.random() * elements.length)];
        
        if (randomElement && Math.random() < 0.1) { // 10% 機率
            randomElement.classList.add('glitch-text');
            setTimeout(() => {
                randomElement.classList.remove('glitch-text');
            }, 500);
        }
        
        setTimeout(randomGlitch, Math.random() * 10000 + 5000); // 5-15秒隨機間隔
    }
    
    // 啟動隨機故障效果
    setTimeout(randomGlitch, 5000);
});