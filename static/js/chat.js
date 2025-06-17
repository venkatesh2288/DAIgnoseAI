// Chat functionality for DAIgnoseAI AI Assistant

document.addEventListener('DOMContentLoaded', function() {
    const chatMessages = document.getElementById('chatMessages');
    const chatForm = document.getElementById('chatForm');
    const messageInput = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendButton');
    const typingIndicator = document.getElementById('typingIndicator');
    const quickQuestionBtns = document.querySelectorAll('.quick-question-btn');

    // Auto-scroll to bottom of chat
    function scrollToBottom() {
        if (chatMessages) {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }

    // Initialize chat
    function initChat() {
        scrollToBottom();
        
        // Focus on message input
        if (messageInput) {
            messageInput.focus();
        }

        // Add message animations
        const messages = document.querySelectorAll('.message');
        messages.forEach((message, index) => {
            message.style.animationDelay = `${index * 0.1}s`;
            message.classList.add('fade-in');
        });
    }

    // Handle Enter key press
    if (messageInput) {
        messageInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                chatForm.dispatchEvent(new Event('submit'));
            }
        });
    }

    // Handle form submission
    if (chatForm) {
        chatForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const message = messageInput.value.trim();
            
            if (!message) {
                showToast('Please enter a message', 'warning');
                return;
            }

            // Clear input immediately
            messageInput.value = '';
            
            // Disable form during submission
            disableForm();
            
            // Add user message to chat immediately for better UX
            addMessageToChat(message, 'user');
            
            // Show typing indicator
            showTypingIndicator();
            
            // Clear input
            messageInput.value = '';
        });
    }

    // Handle quick question buttons
    quickQuestionBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const question = this.dataset.question;
            if (question && messageInput) {
                messageInput.value = question;
                messageInput.focus();
                
                // Auto-submit after a short delay
                setTimeout(() => {
                    if (chatForm) {
                        chatForm.submit();
                    }
                }, 100);
            }
        });
    });

    // Add message to chat interface
    function addMessageToChat(content, type) {
        if (!chatMessages) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        
        const now = new Date();
        const timeString = now.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        
        let messageHTML;
        if (type === 'user') {
            messageHTML = `
                <div class="message-content">
                    <div class="message-header">
                        <i class="fas fa-user-circle me-2"></i>
                        <strong>You</strong>
                        <small class="text-muted ms-2">${timeString}</small>
                    </div>
                    <div class="message-text">${escapeHtml(content)}</div>
                </div>
            `;
        } else {
            messageHTML = `
                <div class="message-content">
                    <div class="message-header">
                        <i class="fas fa-robot me-2"></i>
                        <strong>AI Assistant</strong>
                        <small class="text-muted ms-2">${timeString}</small>
                    </div>
                    <div class="message-text">${content.replace(/\n/g, '<br>')}</div>
                </div>
            `;
        }
        
        messageDiv.innerHTML = messageHTML;
        messageDiv.style.animationDelay = '0s';
        messageDiv.classList.add('fade-in');
        
        chatMessages.appendChild(messageDiv);
        scrollToBottom();
    }

    // Show typing indicator
    function showTypingIndicator() {
        if (typingIndicator) {
            typingIndicator.style.display = 'block';
            scrollToBottom();
        }
    }

    // Hide typing indicator
    function hideTypingIndicator() {
        if (typingIndicator) {
            typingIndicator.style.display = 'none';
        }
    }

    // Disable form during submission
    function disableForm() {
        if (messageInput) messageInput.disabled = true;
        if (sendButton) {
            sendButton.disabled = true;
            sendButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        }
        
        quickQuestionBtns.forEach(btn => {
            btn.disabled = true;
        });
    }

    // Enable form after submission
    function enableForm() {
        if (messageInput) {
            messageInput.disabled = false;
            messageInput.focus();
        }
        if (sendButton) {
            sendButton.disabled = false;
            sendButton.innerHTML = '<i class="fas fa-paper-plane"></i>';
        }
        
        quickQuestionBtns.forEach(btn => {
            btn.disabled = false;
        });
        
        hideTypingIndicator();
    }

    // Handle Enter key in message input
    if (messageInput) {
        messageInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (chatForm && !sendButton.disabled) {
                    chatForm.submit();
                }
            }
        });

        // Auto-resize textarea as user types
        messageInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = this.scrollHeight + 'px';
        });
    }

    // Escape HTML for security
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Show toast notification
    function showToast(message, type = 'info') {
        if (window.DiagnAIzerUtils && window.DiagnAIzerUtils.showToast) {
            window.DiagnAIzerUtils.showToast(message, type);
        } else {
            // Fallback alert
            alert(message);
        }
    }

    // Handle page unload during chat submission
    let formSubmitted = false;
    if (chatForm) {
        chatForm.addEventListener('submit', function() {
            formSubmitted = true;
        });
    }

    window.addEventListener('beforeunload', function(e) {
        if (formSubmitted) {
            // Let the user know the message is being processed
            e.preventDefault();
            e.returnValue = 'Your message is being processed. Are you sure you want to leave?';
        }
    });

    // Handle back button navigation
    window.addEventListener('popstate', function() {
        if (formSubmitted) {
            location.reload();
        }
    });

    // Message text selection and copy functionality
    chatMessages.addEventListener('click', function(e) {
        const messageText = e.target.closest('.message-text');
        if (messageText && e.detail === 2) { // Double click
            selectText(messageText);
        }
    });

    // Add copy button to AI messages
    function addCopyButton(messageElement) {
        if (!messageElement.classList.contains('assistant-message')) return;
        
        const messageContent = messageElement.querySelector('.message-content');
        const copyBtn = document.createElement('button');
        copyBtn.className = 'btn btn-sm btn-outline-secondary copy-message-btn';
        copyBtn.innerHTML = '<i class="fas fa-copy"></i>';
        copyBtn.title = 'Copy message';
        
        copyBtn.addEventListener('click', function() {
            const messageText = messageElement.querySelector('.message-text').textContent;
            navigator.clipboard.writeText(messageText).then(() => {
                this.innerHTML = '<i class="fas fa-check"></i>';
                setTimeout(() => {
                    this.innerHTML = '<i class="fas fa-copy"></i>';
                }, 2000);
            });
        });
        
        messageContent.appendChild(copyBtn);
    }

    // Select text utility
    function selectText(element) {
        if (window.getSelection && document.createRange) {
            const selection = window.getSelection();
            const range = document.createRange();
            range.selectNodeContents(element);
            selection.removeAllRanges();
            selection.addRange(range);
        }
    }

    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + / to focus message input
        if ((e.ctrlKey || e.metaKey) && e.key === '/') {
            e.preventDefault();
            if (messageInput) {
                messageInput.focus();
            }
        }
        
        // Escape to clear message input
        if (e.key === 'Escape' && messageInput === document.activeElement) {
            messageInput.value = '';
            messageInput.blur();
        }
    });

    // Auto-save draft message
    const DRAFT_KEY = 'diagnaizer_chat_draft';
    
    if (messageInput) {
        // Load saved draft
        const savedDraft = localStorage.getItem(DRAFT_KEY);
        if (savedDraft && !messageInput.value) {
            messageInput.value = savedDraft;
        }
        
        // Save draft as user types
        const saveDraft = debounce(() => {
            if (messageInput.value.trim()) {
                localStorage.setItem(DRAFT_KEY, messageInput.value);
            } else {
                localStorage.removeItem(DRAFT_KEY);
            }
        }, 1000);
        
        messageInput.addEventListener('input', saveDraft);
        
        // Clear draft when message is sent
        if (chatForm) {
            chatForm.addEventListener('submit', () => {
                localStorage.removeItem(DRAFT_KEY);
            });
        }
    }

    // Debounce utility function
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }





    // Chat performance optimization
    function optimizeChatPerformance() {
        const messages = chatMessages.querySelectorAll('.message');
        const maxVisibleMessages = 50;
        
        if (messages.length > maxVisibleMessages) {
            // Hide older messages to improve performance
            for (let i = 0; i < messages.length - maxVisibleMessages; i++) {
                messages[i].style.display = 'none';
            }
            
            // Add button to show older messages
            const showOlderBtn = document.createElement('button');
            showOlderBtn.className = 'btn btn-sm btn-outline-secondary mb-3';
            showOlderBtn.textContent = 'Show older messages';
            showOlderBtn.addEventListener('click', function() {
                messages.forEach(msg => msg.style.display = 'block');
                this.remove();
            });
            
            chatMessages.insertBefore(showOlderBtn, chatMessages.firstChild);
        }
    }

    // Run optimization after messages load
    setTimeout(optimizeChatPerformance, 1000);

    // Initialize chat
    initChat();

    // Expose useful functions globally
    window.ChatUtils = {
        addMessageToChat,
        scrollToBottom,
        showTypingIndicator,
        hideTypingIndicator,
        enableForm,
        disableForm
    };
});
