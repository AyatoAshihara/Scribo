/**
 * Scribo メインアプリケーションスクリプト
 * 共通ユーティリティ関数
 */

// htmx設定
document.body.addEventListener('htmx:configRequest', (event) => {
    // 必要に応じてリクエストをカスタマイズ
});

// htmxエラーハンドリング
document.body.addEventListener('htmx:responseError', (event) => {
    console.error('htmx error:', event.detail);
    // エラー通知を表示
    showToast('エラーが発生しました', 'error');
});

/**
 * トースト通知を表示
 * @param {string} message - メッセージ
 * @param {string} type - 'success' | 'error' | 'warning' | 'info'
 */
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} fixed bottom-4 right-4 w-auto max-w-sm z-50 shadow-lg`;
    toast.innerHTML = `<span>${message}</span>`;
    
    document.body.appendChild(toast);
    
    // 3秒後に削除
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

/**
 * ローカルストレージヘルパー
 */
const storage = {
    get(key) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : null;
        } catch (e) {
            console.error('localStorage get error:', e);
            return null;
        }
    },
    
    set(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch (e) {
            console.error('localStorage set error:', e);
        }
    },
    
    remove(key) {
        try {
            localStorage.removeItem(key);
        } catch (e) {
            console.error('localStorage remove error:', e);
        }
    }
};

/**
 * 文字数カウント（空白・改行除外）
 * @param {string} text - テキスト
 * @returns {number} 文字数
 */
function countWords(text) {
    if (!text) return 0;
    return text.replace(/[\s\n\r]/g, '').length;
}

/**
 * 時間フォーマット（mm:ss）
 * @param {number} seconds - 秒数
 * @returns {string} フォーマット済み文字列
 */
function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

// グローバルに公開
window.showToast = showToast;
window.storage = storage;
window.countWords = countWords;
window.formatTime = formatTime;
