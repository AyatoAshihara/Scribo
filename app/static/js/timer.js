/**
 * 試験タイマー Alpine.js コンポーネント
 * 制限時間のカウントダウンとローカルストレージ永続化
 */

function examTimer(totalMinutes = 120) {
    return {
        totalSeconds: totalMinutes * 60,
        remainingSeconds: totalMinutes * 60,
        isRunning: false,
        intervalId: null,
        storageKey: 'scribo-timer-state',
        
        init() {
            // ローカルストレージから復元
            this.restore();
            
            // ページ離脱時に保存
            window.addEventListener('beforeunload', () => {
                this.save();
            });
        },
        
        start() {
            if (this.isRunning) return;
            
            this.isRunning = true;
            this.intervalId = setInterval(() => {
                this.tick();
            }, 1000);
            
            this.save();
        },
        
        stop() {
            if (!this.isRunning) return;
            
            this.isRunning = false;
            if (this.intervalId) {
                clearInterval(this.intervalId);
                this.intervalId = null;
            }
            
            this.save();
        },
        
        toggle() {
            if (this.isRunning) {
                this.stop();
            } else {
                this.start();
            }
        },
        
        reset() {
            this.stop();
            this.remainingSeconds = this.totalSeconds;
            storage.remove(this.storageKey);
        },
        
        tick() {
            if (this.remainingSeconds > 0) {
                this.remainingSeconds--;
                
                // 5分ごとに保存
                if (this.remainingSeconds % 300 === 0) {
                    this.save();
                }
                
                // 警告チェック
                this.checkWarnings();
            } else {
                this.stop();
                this.onTimeUp();
            }
        },
        
        checkWarnings() {
            // 10分前
            if (this.remainingSeconds === 600) {
                showToast('残り10分です', 'warning');
            }
            // 5分前
            if (this.remainingSeconds === 300) {
                showToast('残り5分です！', 'error');
            }
            // 1分前
            if (this.remainingSeconds === 60) {
                showToast('残り1分です！', 'error');
            }
        },
        
        onTimeUp() {
            // 時間切れダイアログを表示
            const dialog = document.getElementById('timeup-dialog');
            if (dialog) {
                dialog.showModal();
            }
        },
        
        save() {
            storage.set(this.storageKey, {
                remainingSeconds: this.remainingSeconds,
                isRunning: this.isRunning,
                savedAt: Date.now()
            });
        },
        
        restore() {
            const saved = storage.get(this.storageKey);
            if (!saved) return;
            
            // 1時間以上経過していたらリセット
            const elapsed = Date.now() - saved.savedAt;
            if (elapsed > 3600000) {
                storage.remove(this.storageKey);
                return;
            }
            
            // 実行中だった場合、経過時間を差し引く
            if (saved.isRunning) {
                const elapsedSeconds = Math.floor(elapsed / 1000);
                this.remainingSeconds = Math.max(0, saved.remainingSeconds - elapsedSeconds);
                this.start();
            } else {
                this.remainingSeconds = saved.remainingSeconds;
            }
        },
        
        formatTime(seconds) {
            const mins = Math.floor(seconds / 60);
            const secs = seconds % 60;
            return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        }
    };
}

// グローバルに公開
window.examTimer = examTimer;
