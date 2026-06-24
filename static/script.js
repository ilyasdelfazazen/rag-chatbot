document.addEventListener('DOMContentLoaded', function() {
    const chatBox = document.getElementById('chat-box');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const clearBtn = document.getElementById('clear-btn');
    const uploadBtn = document.getElementById('upload-btn');
    const fileUpload = document.getElementById('file-upload');
    const uploadStatus = document.getElementById('upload-status');
    const ragToggle = document.getElementById('rag-toggle');

    // Function to add a message to the chat box
    function addMessage(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;

        const roleSpan = document.createElement('span');
        roleSpan.className = 'role';
        roleSpan.textContent = role === 'user' ? 'You:' : 'Assistant:';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'content';
        contentDiv.textContent = content;

        messageDiv.appendChild(roleSpan);
        messageDiv.appendChild(contentDiv);
        chatBox.appendChild(messageDiv);

        // Scroll to bottom
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // Send message to server
    async function sendMessage() {
        const message = userInput.value.trim();
        if (!message) return;

        const selectedModel = document.getElementById('model-select').value;
        const useRAG = ragToggle.checked;

        addMessage('user', message);
        userInput.value = '';

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    model: selectedModel,
                    use_rag: useRAG
                })
            });

            const data = await response.json();
            if (data.reply) {
                addMessage('assistant', data.reply);
            } else if (data.error) {
                addMessage('error', 'Error: ' + JSON.stringify(data.error));
            }
        } catch (error) {
            addMessage('error', 'Failed to get response: ' + error.message);
        }
    }

    // Handle file upload
    uploadBtn.addEventListener('click', async function() {
        const file = fileUpload.files[0];
        if (!file) {
            uploadStatus.textContent = 'Please select a file first';
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        try {
            uploadStatus.textContent = 'Uploading...';
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            if (data.success) {
                uploadStatus.textContent = 'File uploaded and processed!';
                fileUpload.value = '';
            } else {
                uploadStatus.textContent = data.error || 'Upload failed';
            }
        } catch (error) {
            uploadStatus.textContent = 'Upload failed: ' + error.message;
        }
    });

    // Event listeners
    sendBtn.addEventListener('click', sendMessage);

    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    clearBtn.addEventListener('click', function() {
        chatBox.innerHTML = '';
    });
});