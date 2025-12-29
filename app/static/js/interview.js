document.addEventListener('alpine:init', () => {
    Alpine.data('interviewWizard', (examType, problemId) => ({
        examType: examType,
        problemId: problemId,
        // Use problemId as the unique identifier for the exam session, consistent with design_wizard.js
        examId: problemId, 
        messages: [],
        inputMessage: '',
        isLoading: false,
        canGenerate: false, // For Phase 5

        async init() {
            window.addEventListener('open-interview-modal', () => {
                this.open();
            });
        },

        async open() {
            const modal = document.getElementById('interview_modal');
            if (modal) {
                modal.showModal();
                await this.fetchSession();
            }
        },

        async fetchSession() {
            this.isLoading = true;
            try {
                // Encode examId to handle special characters
                const response = await fetch(`/api/interview/sessions/${encodeURIComponent(this.examId)}`);
                if (response.ok) {
                    const session = await response.json();
                    this.messages = session.history || [];
                    // Scroll to bottom
                    this.$nextTick(() => this.scrollToBottom());
                } else {
                    console.error('Failed to fetch session');
                }
            } catch (error) {
                console.error('Error fetching session:', error);
            } finally {
                this.isLoading = false;
            }
        },

        async sendMessage() {
            if (!this.inputMessage.trim() || this.isLoading) return;

            const userMsg = {
                role: 'user',
                content: this.inputMessage,
                timestamp: new Date().toISOString()
            };
            
            this.messages.push(userMsg);
            const currentInput = this.inputMessage;
            this.inputMessage = '';
            this.isLoading = true;
            this.$nextTick(() => this.scrollToBottom());

            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout

            try {
                const response = await fetch(`/api/interview/chat/${encodeURIComponent(this.examId)}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ message: currentInput }),
                    signal: controller.signal
                });
                
                clearTimeout(timeoutId);

                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }

                // Create a placeholder for the assistant's response
                const assistantMsg = {
                    role: 'assistant',
                    content: '',
                    timestamp: new Date().toISOString()
                };
                this.messages.push(assistantMsg);
                
                const reader = response.body.getReader();
                const decoder = new TextDecoder();

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    
                    const chunk = decoder.decode(value, { stream: true });
                    // Update the last message content
                    this.messages[this.messages.length - 1].content += chunk;
                    this.$nextTick(() => this.scrollToBottom());
                }

                // Check for trigger phrase after response is complete
                const lastMsg = this.messages[this.messages.length - 1];
                if (lastMsg.content.includes("設計書を作成しましょうか")) {
                    this.canGenerate = true;
                }

            } catch (error) {
                console.error('Error sending message:', error);
                this.messages.push({
                    role: 'system',
                    content: 'エラーが発生しました。もう一度お試しください。',
                    timestamp: new Date().toISOString()
                });
            } finally {
                this.isLoading = false;
                this.$nextTick(() => this.scrollToBottom());
            }
        },

        scrollToBottom() {
            const container = this.$refs.chatHistory;
            if (container) {
                container.scrollTop = container.scrollHeight;
            }
        },

        formatMessage(content) {
            if (!content) return '';
            // Simple newline to br for now. 
            // In production, use a markdown library like marked.js if needed.
            return content.replace(/\n/g, '<br>');
        },
        
        async generateDesign() {
            if (!confirm('現在の入力内容は上書きされます。よろしいですか？')) {
                return;
            }
            this.isLoading = true;
            try {
                const response = await fetch(`/api/interview/generate/${encodeURIComponent(this.examId)}`, {
                    method: 'POST'
                });
                
                if (response.ok) {
                    const proposal = await response.json();
                    this.applyDesign(proposal);
                    // Close modal
                    document.getElementById('interview_modal').close();
                    // Show success message
                    alert('設計書を生成し、ウィザードに適用しました。');
                } else {
                    console.error('Failed to generate design');
                    alert('設計書の生成に失敗しました。');
                }
            } catch (error) {
                console.error('Error generating design:', error);
                alert('エラーが発生しました。');
            } finally {
                this.isLoading = false;
            }
        },

        applyDesign(proposal) {
            window.dispatchEvent(new CustomEvent('design-generated', { 
                detail: proposal 
            }));
        }
    }));
});
