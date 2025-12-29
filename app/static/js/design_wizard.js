document.addEventListener('alpine:init', () => {
    Alpine.data('designWizard', (examType, problemId) => ({
        step: 1,
        loading: false,
        saving: false,
        problem: null,
        modules: [],
        problemId: problemId, // Expose problemId to the template scope
        design: {
            theme: '',
            breakdown: {
                'ア': '',
                'イ': '',
                'ウ': ''
            },
            structure: [
                { id: 1, title: '第1章 ...', content: '' },
                { id: 2, title: '第2章 ...', content: '' },
                { id: 3, title: '第3章 ...', content: '' }
            ],
            module_map: {} // { chapter_id: [module_id, ...] }
        },
        
        async init() {
            await Promise.all([
                this.fetchProblem(),
                this.fetchModules(),
                this.fetchDesign()
            ]);

            window.addEventListener('design-generated', (event) => {
                this.applyGeneratedDesign(event.detail);
            });
        },

        applyGeneratedDesign(proposal) {
            this.design.theme = proposal.theme;
            
            // Map A, B, C to ア, イ, ウ
            if (proposal.breakdown) {
                this.design.breakdown['ア'] = proposal.breakdown.A || '';
                this.design.breakdown['イ'] = proposal.breakdown.B || '';
                this.design.breakdown['ウ'] = proposal.breakdown.C || '';
            }
            
            // Map structure
            if (proposal.structure && Array.isArray(proposal.structure)) {
                this.design.structure = proposal.structure.map((s, index) => ({
                    id: index + 1,
                    title: s.title || `第${index + 1}章`,
                    content: (s.sections || []).join('\n')
                }));
            }
            
            // Map module_map
            if (proposal.module_map) {
                const newModuleMap = {};
                for (const [key, value] of Object.entries(proposal.module_map)) {
                    // key might be "chapter1"
                    const match = key.match(/chapter(\d+)/);
                    if (match) {
                        newModuleMap[parseInt(match[1])] = value;
                    }
                }
                this.design.module_map = newModuleMap;
            }
            
            // Go to step 1
            this.step = 1;
        },

        async fetchProblem() {
            try {
                const res = await fetch(`/api/exams/detail?exam_type=${examType}&problem_id=${encodeURIComponent(problemId)}`);
                if (!res.ok) throw new Error('Failed to fetch problem');
                this.problem = await res.json();
            } catch (e) {
                console.error('Failed to fetch problem', e);
            }
        },

        async fetchModules() {
            try {
                const res = await fetch('/api/modules');
                this.modules = await res.json();
            } catch (e) {
                console.error('Failed to fetch modules', e);
            }
        },

        async fetchDesign() {
            try {
                const res = await fetch(`/api/designs/${encodeURIComponent(problemId)}`);
                const data = await res.json();
                if (data.created_at) {
                    this.design = {
                        theme: data.theme || '',
                        breakdown: data.breakdown || { 'ア': '', 'イ': '', 'ウ': '' },
                        structure: data.structure.length > 0 ? data.structure : this.design.structure,
                        module_map: data.module_map || {}
                    };
                }
            } catch (e) {
                console.error('Failed to fetch design', e);
            }
        },

        async saveDesign() {
            this.saving = true;
            try {
                const payload = {
                    exam_id: problemId,
                    theme: this.design.theme,
                    breakdown: this.design.breakdown,
                    structure: this.design.structure,
                    module_map: this.design.module_map
                };
                
                const res = await fetch('/api/designs', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                
                if (!res.ok) throw new Error('保存に失敗しました');
                
                // トースト表示（簡易実装）
                const toast = document.createElement('div');
                toast.className = 'alert alert-success fixed bottom-4 right-4 w-auto shadow-lg z-50';
                toast.innerHTML = '<span>設計図を保存しました</span>';
                document.body.appendChild(toast);
                setTimeout(() => toast.remove(), 3000);
                
            } catch (e) {
                alert(e.message);
            } finally {
                this.saving = false;
            }
        },

        nextStep() {
            if (this.step < 3) this.step++;
            this.saveDesign();
        },

        prevStep() {
            if (this.step > 1) this.step--;
        },
        
        // 設問分解ヘルパー
        formatProblemContent(content) {
            if (!content) return '';
            return content.replace(/\n/g, '<br>');
        },
        
        // 章構成操作
        addChapter() {
            const newId = this.design.structure.length + 1;
            this.design.structure.push({ id: newId, title: `第${newId}章 ...`, content: '' });
        },
        
        removeChapter(index) {
            this.design.structure.splice(index, 1);
        },
        
        // モジュールマッピング操作
        toggleModule(chapterId, moduleId) {
            if (!this.design.module_map[chapterId]) {
                this.design.module_map[chapterId] = [];
            }
            
            const list = this.design.module_map[chapterId];
            const index = list.indexOf(moduleId);
            
            if (index === -1) {
                list.push(moduleId);
            } else {
                list.splice(index, 1);
            }
        },
        
        isModuleSelected(chapterId, moduleId) {
            return this.design.module_map[chapterId]?.includes(moduleId);
        },
        
        getModuleById(moduleId) {
            return this.modules.find(m => m.module_id === moduleId);
        }
    }));
});
