/**
 * 採点結果表示 Alpine.js コンポーネント
 */

function scoringResult(submissionId) {
    return {
        submission_id: submissionId,
        result: null,
        loading: true,
        error: null,
        
        // 段階的開示用
        showDetails: false,
        showDetailedResult: false,
        
        // 労働の錯覚用
        loadingStep: 0,
        loadingProgress: 0,
        loadingMessage: '回答を確認しています...',
        currentTip: '',
        
        // 豆知識リスト
        tips: [
            '午後Ⅱ試験では「具体性」が最も重視されます。実際のプロジェクト経験を詳しく書きましょう。',
            '設問アは状況設定、設問イは具体的な施策、設問ウは結果と考察という流れが基本です。',
            '合格者の多くは、問題文の要求を正確に理解し、それに沿った回答をしています。',
            '文字数は目安の範囲内に収めることが重要です。多すぎても少なすぎてもマイナス評価になります。',
            '「〜と考えた」「〜を実施した」など、主語を明確にした文章を心がけましょう。'
        ],
        
        async init() {
            // ローディングアニメーション開始
            this.startLoadingAnimation();
            // 豆知識をランダムに表示
            this.currentTip = this.tips[Math.floor(Math.random() * this.tips.length)];
            
            await this.fetchResult();
        },
        
        startLoadingAnimation() {
            const steps = [
                { step: 1, progress: 25, message: '回答を受信しました...' },
                { step: 2, progress: 50, message: '文章構成を分析しています...' },
                { step: 3, progress: 75, message: '8つの観点で評価中...' },
                { step: 4, progress: 95, message: '最終スコアを計算中...' }
            ];
            
            let i = 0;
            const interval = setInterval(() => {
                if (i < steps.length && this.loading) {
                    this.loadingStep = steps[i].step;
                    this.loadingProgress = steps[i].progress;
                    this.loadingMessage = steps[i].message;
                    i++;
                } else {
                    clearInterval(interval);
                }
            }, 800);
        },
        
        async fetchResult() {
            this.loading = true;
            this.error = null;
            
            try {
                const response = await fetch(`/api/scoring/${encodeURIComponent(this.submission_id)}`);
                
                if (!response.ok) {
                    if (response.status === 404) {
                        throw new Error('採点結果が見つかりません');
                    }
                    throw new Error('採点結果の取得に失敗しました');
                }
                
                this.result = await response.json();
                
                // ローディング完了
                this.loadingStep = 4;
                this.loadingProgress = 100;
                this.loadingMessage = '完了！';
                
                // 少し待ってから結果を表示
                await new Promise(r => setTimeout(r, 500));
                this.loading = false;
                
                // 合格時は紙吹雪を表示
                if (this.result.passed) {
                    setTimeout(() => this.triggerConfetti(), 800);
                }
                
            } catch (e) {
                this.error = e.message;
                this.loading = false;
            }
        },
        
        // 紙吹雪エフェクト
        triggerConfetti() {
            if (typeof confetti === 'function') {
                // 左から
                confetti({
                    particleCount: 100,
                    spread: 70,
                    origin: { x: 0.1, y: 0.6 }
                });
                // 右から
                confetti({
                    particleCount: 100,
                    spread: 70,
                    origin: { x: 0.9, y: 0.6 }
                });
            }
        },
        
        // ランク別カラークラス
        getRankColorClass(rank) {
            switch (rank) {
                case 'A':
                    return 'text-success';
                case 'B':
                    return 'text-info';
                case 'C':
                    return 'text-warning';
                case 'D':
                    return 'text-error';
                default:
                    return 'text-base-content';
            }
        },
        
        // 後方互換性のためのエイリアス
        getRankColor(rank) {
            return this.getRankColorClass(rank);
        },
        
        getProgressColor(score) {
            if (score >= 80) {
                return 'progress-success';
            } else if (score >= 60) {
                return 'progress-info';
            } else if (score >= 40) {
                return 'progress-warning';
            } else {
                return 'progress-error';
            }
        },
        
        // 合格までの残り点数
        getPointsToPass() {
            if (!this.result) return 0;
            const passingScore = 60; // 合格ライン
            return Math.max(0, passingScore - this.result.aggregate_score).toFixed(1);
        },
        
        // 励ましメッセージ
        getEncouragementMessage() {
            if (!this.result) return '';
            
            if (this.result.passed) {
                const messages = [
                    '継続は力なり。この調子で本番も頑張ってください！',
                    '素晴らしい！あなたの実力は本物です。',
                    '合格への道を着実に歩んでいます！',
                    '努力は裏切らない。自信を持って本番に臨みましょう！'
                ];
                return messages[Math.floor(Math.random() * messages.length)];
            } else {
                const messages = [
                    '失敗は成功の母。次回は必ず良くなります！',
                    'もう少しです！あきらめずに挑戦し続けましょう。',
                    '一歩一歩、確実に成長しています。',
                    '弱点が分かれば、それは成長のチャンスです！'
                ];
                return messages[Math.floor(Math.random() * messages.length)];
            }
        },
        
        // 再挑戦
        retryExam() {
            // 結果から試験情報を取得して問題ページに戻る
            // TODO: 実際の実装では exam_type と problem_id を result から取得
            window.location.href = '/';
        }
    };
}

// グローバルに公開
window.scoringResult = scoringResult;
