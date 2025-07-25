// 修復百分比顯示閃爍問題
document.addEventListener('DOMContentLoaded', function() {
    
    // 平滑更新威脅百分比
    function updateThreatPercentage(newValue) {
        const element = document.getElementById('threat-percentage');
        if (!element) return;
        
        // 移除可能的閃爍動畫
        element.style.animation = 'none';
        element.style.transition = 'all 0.3s ease';
        
        // 確保數值格式正確
        const cleanValue = parseFloat(newValue);
        if (!isNaN(cleanValue)) {
            element.textContent = Math.round(cleanValue) + '%';
        }
        
        // 根據威脅等級調整顏色
        if (cleanValue >= 80) {
            element.style.color = '#ff0040';
            element.style.textShadow = '0 0 3px #ff0040, 0 0 6px #ff0040';
        } else if (cleanValue >= 60) {
            element.style.color = '#ff4000';
            element.style.textShadow = '0 0 3px #ff4000, 0 0 6px #ff4000';
        } else if (cleanValue >= 40) {
            element.style.color = '#ffff00';
            element.style.textShadow = '0 0 3px #ffff00, 0 0 6px #ffff00';
        } else if (cleanValue >= 20) {
            element.style.color = '#80ff00';
            element.style.textShadow = '0 0 3px #80ff00, 0 0 6px #80ff00';
        } else {
            element.style.color = '#00ff80';
            element.style.textShadow = '0 0 3px #00ff80, 0 0 6px #00ff80';
        }
    }
    
    // 監聽威脅百分比變化
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList' || mutation.type === 'characterData') {
                const element = document.getElementById('threat-percentage');
                if (element && element.textContent && element.textContent !== '0%') {
                    const value = element.textContent.replace('%', '');
                    updateThreatPercentage(value);
                }
            }
        });
    });
    
    const threatElement = document.getElementById('threat-percentage');
    if (threatElement) {
        observer.observe(threatElement, {
            childList: true,
            characterData: true,
            subtree: true
        });
    }
    
    // 確保儀表盤動畫平滑
    function updateGaugeAngle(percentage) {
        const gaugeFill = document.querySelector('.gauge-fill');
        if (gaugeFill) {
            // 計算角度 (0-180度)
            const angle = (percentage / 100) * 180;
            gaugeFill.style.setProperty('--gauge-angle', angle);
            gaugeFill.style.transition = 'all 1s ease-out';
        }
    }
    
    // 全局函數供 main.js 使用
    window.updateThreatDisplay = function(percentage) {
        updateThreatPercentage(percentage);
        updateGaugeAngle(percentage);
    };
});