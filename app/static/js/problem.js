/**
 * 問題閲覧・回答入力 Alpine.js コンポーネント
 */

function problemViewer(examType, problemId) {
    return {
        examType,
        problemId,
        problem: null,
        loading: true,
        error: null,
        activeTab: '設問ア',
        answers: {
            '設問ア': '',
            '設問イ': '',
            '設問ウ': ''
        },
        submitting: false,
        wordLimits: {
            '設問ア': { min: 600, max: 800 },
            '設問イ': { min: 700, max: 1000 },
            '設問ウ': { min: 600, max: 800 }
        },
        storageKey: `scribo-answer:${examType}:${problemId}`,
        
        async init() {
            // ローカルストレージから回答を復元
            this.restoreAnswers();
            
            // 問題データを取得
            await this.fetchProblem();
            
            // Alpine.storeに登録（ダイアログから参照用）
            Alpine.store('problem', this);
        },
        
        async fetchProblem() {
            this.loading = true;
            this.error = null;
            
            try {
                const response = await fetch(
                    `/api/exams/detail?exam_type=${encodeURIComponent(this.examType)}&problem_id=${encodeURIComponent(this.problemId)}`
                );
                
                if (!response.ok) {
                    throw new Error('問題の取得に失敗しました');
                }
                
                this.problem = await response.json();
                
                // 文字数制限を更新
                if (this.problem.word_count_limits) {
                    this.wordLimits = this.problem.word_count_limits;
                }
                
            } catch (e) {
                this.error = e.message;
            } finally {
                this.loading = false;
            }
        },
        
        getWordCount(question) {
            const text = this.answers[question] || '';
            return countWords(text);
        },
        
        getWordLimit(question) {
            const limit = this.wordLimits[question];
            if (!limit) return '---';
            return `${limit.min}〜${limit.max}字`;
        },
        
        getWordCountBadgeClass(question) {
            const count = this.getWordCount(question);
            const limit = this.wordLimits[question];
            
            if (!limit) return 'badge-ghost';
            
            if (count < limit.min) {
                return 'badge-warning';
            } else if (count > limit.max) {
                return 'badge-error';
            } else {
                return 'badge-success';
            }
        },
        
        // 設問が完了しているか（文字数範囲内）
        isQuestionComplete(question) {
            const count = this.getWordCount(question);
            const limit = this.wordLimits[question];
            if (!limit) return false;
            return count >= limit.min && count <= limit.max;
        },
        
        // 完了した設問数を取得
        getCompletedCount() {
            return ['設問ア', '設問イ', '設問ウ'].filter(q => this.isQuestionComplete(q)).length;
        },
        
        // 目標までの残り文字数
        getRemainingWords(question) {
            const count = this.getWordCount(question);
            const limit = this.wordLimits[question];
            if (!limit) return 0;
            return Math.max(0, limit.min - count);
        },
        
        // 文字数オーバーかどうか
        isOverLimit(question) {
            const count = this.getWordCount(question);
            const limit = this.wordLimits[question];
            if (!limit) return false;
            return count > limit.max;
        },
        
        // オーバーした文字数
        getOverWords(question) {
            const count = this.getWordCount(question);
            const limit = this.wordLimits[question];
            if (!limit) return 0;
            return Math.max(0, count - limit.max);
        },
        
        formatContent(content) {
            if (!content) return '';
            // XSS対策: HTMLエスケープ
            const escaped = content
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#039;');
            // エスケープ後に改行を変換
            return escaped
                .replace(/\n\n/g, '</p><p>')
                .replace(/\n/g, '<br>')
                .replace(/^/, '<p>')
                .replace(/$/, '</p>');
        },
        
        saveToLocalStorage() {
            storage.set(this.storageKey, {
                answers: this.answers,
                savedAt: Date.now()
            });
        },
        
        restoreAnswers() {
            const saved = storage.get(this.storageKey);
            if (saved && saved.answers) {
                this.answers = { ...this.answers, ...saved.answers };
            }
        },
        
        async submitAnswer() {
            // 文字数チェック
            const warnings = [];
            for (const [question, answer] of Object.entries(this.answers)) {
                const count = countWords(answer);
                const limit = this.wordLimits[question];
                
                if (limit) {
                    if (count < limit.min) {
                        warnings.push(`${question}: 文字数が不足しています (${count}/${limit.min}字)`);
                    } else if (count > limit.max) {
                        warnings.push(`${question}: 文字数が超過しています (${count}/${limit.max}字)`);
                    }
                }
            }
            
            if (warnings.length > 0) {
                const proceed = confirm(
                    '以下の警告があります。送信しますか？\n\n' + warnings.join('\n')
                );
                if (!proceed) return;
            }
            
            this.submitting = true;
            
            try {
                // 回答を送信
                const response = await fetch('/api/answers', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        exam_type: this.examType,
                        problem_id: this.problemId,
                        answers: this.answers,
                        metadata: {
                            word_counts: {
                                '設問ア': this.getWordCount('設問ア'),
                                '設問イ': this.getWordCount('設問イ'),
                                '設問ウ': this.getWordCount('設問ウ')
                            }
                        }
                    })
                });
                
                if (!response.ok) {
                    throw new Error('回答の送信に失敗しました');
                }
                
                const result = await response.json();
                
                // 採点リクエスト
                showToast('回答を送信しました。採点中...', 'success');
                
                const scoringResponse = await fetch('/api/scoring', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        submission_id: result.submission_id
                    })
                });
                
                if (!scoringResponse.ok) {
                    throw new Error('採点リクエストに失敗しました');
                }
                
                // ローカルストレージをクリア
                storage.remove(this.storageKey);
                
                // 結果ページへ遷移
                window.location.href = `/result/${result.submission_id}`;
                
            } catch (e) {
                showToast(e.message, 'error');
            } finally {
                this.submitting = false;
            }
        }
    };
}

// グローバルに公開
window.problemViewer = problemViewer;
