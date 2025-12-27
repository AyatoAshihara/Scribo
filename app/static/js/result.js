/**
 * 採点結果表示 Alpine.js コンポーネント
 */

function scoringResult(submissionId) {
    return {
        submission_id: submissionId,
        result: null,
        loading: true,
        error: null,
        
        async init() {
            await this.fetchResult();
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
                
            } catch (e) {
                this.error = e.message;
            } finally {
                this.loading = false;
            }
        },
        
        getRankColor(rank) {
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
        }
    };
}

// グローバルに公開
window.scoringResult = scoringResult;
