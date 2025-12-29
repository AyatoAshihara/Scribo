document.addEventListener('alpine:init', () => {
    Alpine.data('modulesPage', () => ({
        modules: [],
        loading: false,
        error: null,
        showModal: false,
        isEditing: false,
        
        // フォームデータ
        form: {
            module_id: null,
            title: '',
            category: '背景', // デフォルト
            content: '',
            tags: '' // カンマ区切り文字列として扱う
        },
        
        categories: ['背景', '課題', '解決策', '効果', 'その他'],

        async init() {
            await this.fetchModules();
        },

        async fetchModules() {
            this.loading = true;
            this.error = null;
            try {
                const response = await fetch('/api/modules');
                if (!response.ok) throw new Error('モジュールの取得に失敗しました');
                this.modules = await response.json();
            } catch (e) {
                this.error = e.message;
            } finally {
                this.loading = false;
            }
        },

        openCreateModal() {
            this.isEditing = false;
            this.form = {
                module_id: null,
                title: '',
                category: '背景',
                content: '',
                tags: ''
            };
            this.showModal = true;
            document.getElementById('module-modal').showModal();
        },

        openEditModal(module) {
            this.isEditing = true;
            this.form = {
                module_id: module.module_id,
                title: module.title,
                category: module.category,
                content: module.content,
                tags: module.tags ? module.tags.join(', ') : ''
            };
            this.showModal = true;
            document.getElementById('module-modal').showModal();
        },

        closeModal() {
            this.showModal = false;
            document.getElementById('module-modal').close();
        },

        async saveModule() {
            if (!this.form.title || !this.form.content) {
                alert('タイトルと内容は必須です');
                return;
            }

            const tagsArray = this.form.tags
                .split(',')
                .map(t => t.trim())
                .filter(t => t.length > 0);

            const payload = {
                title: this.form.title,
                category: this.form.category,
                content: this.form.content,
                tags: tagsArray
            };

            this.loading = true;
            try {
                let response;
                if (this.isEditing) {
                    response = await fetch(`/api/modules/${this.form.module_id}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });
                } else {
                    response = await fetch('/api/modules', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });
                }

                if (!response.ok) throw new Error('保存に失敗しました');
                
                await this.fetchModules();
                this.closeModal();
            } catch (e) {
                alert(e.message);
            } finally {
                this.loading = false;
            }
        },

        async deleteModule(moduleId) {
            if (!confirm('本当に削除しますか？')) return;

            this.loading = true;
            try {
                const response = await fetch(`/api/modules/${moduleId}`, {
                    method: 'DELETE'
                });
                if (!response.ok) throw new Error('削除に失敗しました');
                await this.fetchModules();
            } catch (e) {
                alert(e.message);
            } finally {
                this.loading = false;
            }
        },

        async seedModules() {
            this.loading = true;
            try {
                const response = await fetch('/api/modules/seed', {
                    method: 'POST'
                });
                if (!response.ok) throw new Error('テンプレートの投入に失敗しました');
                await this.fetchModules();
            } catch (e) {
                alert(e.message);
            } finally {
                this.loading = false;
            }
        },

        async rewriteContent() {
            if (!this.form.content) {
                alert('リライトする内容を入力してください');
                return;
            }

            const originalContent = this.form.content;
            this.loading = true; // モーダル内でのローディング表示用フラグが必要かも

            try {
                const response = await fetch('/api/modules/rewrite', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        text: this.form.content,
                        category: this.form.category
                    })
                });

                if (!response.ok) throw new Error('リライトに失敗しました');
                
                const data = await response.json();
                this.form.content = data.rewritten_text;
                
            } catch (e) {
                alert(e.message);
            } finally {
                this.loading = false;
            }
        },
        
        // カテゴリごとのバッジ色
        getCategoryClass(category) {
            const map = {
                '背景': 'badge-soft-primary',
                '課題': 'badge-soft-error',
                '解決策': 'badge-soft-success',
                '効果': 'badge-soft-info',
                'その他': 'badge-soft-secondary'
            };
            return map[category] || 'badge-ghost';
        }
    }));
});
