/**
 * Aura Chat Provider
 * ==================
 * 
 * Provides an interactive chat interface with Aura in VS Code.
 * Allows developers to ask questions and get intelligent responses.
 */

import * as vscode from 'vscode';
import { AuraConnection } from '../connection';

export class AuraChatProvider implements vscode.WebviewViewProvider {
    public static readonly viewType = 'aura.chat';

    private _view?: vscode.WebviewView;

    constructor(
        private readonly _extensionUri: vscode.Uri,
        private connection: AuraConnection
    ) {}

    public resolveWebviewView(
        webviewView: vscode.WebviewView,
        context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken,
    ) {
        this._view = webviewView;

        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [
                this._extensionUri
            ]
        };

        webviewView.webview.html = this._getHtmlForWebview(webviewView.webview);

        webviewView.webview.onDidReceiveMessage(async data => {
            switch (data.type) {
                case 'askQuestion':
                    await this.handleQuestion(data.question);
                    break;
                case 'clearChat':
                    this.clearChat();
                    break;
            }
        });
    }

    public async askQuestion(question: string): Promise<void> {
        if (this._view) {
            await this._view.show?.(true);
            this._view.webview.postMessage({
                type: 'addQuestion',
                question: question
            });
            await this.handleQuestion(question);
        }
    }

    private async handleQuestion(question: string): Promise<void> {
        try {
            // Add thinking indicator
            this._view?.webview.postMessage({
                type: 'thinking',
                show: true
            });

            // Get active editor context
            const editor = vscode.window.activeTextEditor;
            const context = editor ? {
                fileName: editor.document.fileName,
                language: editor.document.languageId,
                selectedText: editor.document.getText(editor.selection),
                lineNumber: editor.selection.active.line + 1
            } : undefined;

            // Send question to Aura
            const response = await this.connection.askQuestion(question, context);

            // Hide thinking indicator
            this._view?.webview.postMessage({
                type: 'thinking',
                show: false
            });

            if (response) {
                this._view?.webview.postMessage({
                    type: 'addResponse',
                    response: response
                });
            } else {
                this._view?.webview.postMessage({
                    type: 'addResponse',
                    response: 'Sorry, I couldn\\'t process your question. Please check the connection to Aura.'
                });
            }
        } catch (error) {
            this._view?.webview.postMessage({
                type: 'thinking',
                show: false
            });
            this._view?.webview.postMessage({
                type: 'addResponse',
                response: `Error: ${error}`
            });
        }
    }

    private clearChat(): void {
        this._view?.webview.postMessage({
            type: 'clearMessages'
        });
    }

    private _getHtmlForWebview(webview: vscode.Webview): string {
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aura Chat</title>
    <style>
        body {
            font-family: var(--vscode-font-family);
            font-size: var(--vscode-font-size);
            color: var(--vscode-foreground);
            background-color: var(--vscode-editor-background);
            margin: 0;
            padding: 0;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }

        .chat-container {
            flex: 1;
            overflow-y: auto;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .message {
            max-width: 90%;
            padding: 12px;
            border-radius: 8px;
            line-height: 1.4;
        }

        .message.user {
            background-color: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            align-self: flex-end;
            margin-left: auto;
        }

        .message.aura {
            background-color: var(--vscode-editor-inactiveSelectionBackground);
            border-left: 3px solid #9f7aea;
            align-self: flex-start;
        }

        .message.aura::before {
            content: "🤖 Aura";
            display: block;
            font-weight: bold;
            margin-bottom: 6px;
            color: #9f7aea;
            font-size: 0.9em;
        }

        .thinking {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 12px;
            font-style: italic;
            opacity: 0.7;
        }

        .thinking-dots {
            display: inline-flex;
            gap: 2px;
        }

        .thinking-dot {
            width: 4px;
            height: 4px;
            background-color: #9f7aea;
            border-radius: 50%;
            animation: thinking 1.4s infinite ease-in-out;
        }

        .thinking-dot:nth-child(1) { animation-delay: -0.32s; }
        .thinking-dot:nth-child(2) { animation-delay: -0.16s; }

        @keyframes thinking {
            0%, 80%, 100% { transform: scale(0); }
            40% { transform: scale(1); }
        }

        .input-container {
            padding: 16px;
            border-top: 1px solid var(--vscode-panel-border);
            display: flex;
            gap: 8px;
        }

        .input-container input {
            flex: 1;
            padding: 8px 12px;
            border: 1px solid var(--vscode-input-border);
            background-color: var(--vscode-input-background);
            color: var(--vscode-input-foreground);
            border-radius: 4px;
            outline: none;
        }

        .input-container input:focus {
            border-color: var(--vscode-focusBorder);
        }

        .input-container button {
            padding: 8px 16px;
            background-color: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            border-radius: 4px;
            cursor: pointer;
            outline: none;
        }

        .input-container button:hover {
            background-color: var(--vscode-button-hoverBackground);
        }

        .input-container button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }

        .clear-button {
            margin-left: 4px;
            background-color: var(--vscode-button-secondaryBackground) !important;
            color: var(--vscode-button-secondaryForeground) !important;
        }

        .welcome-message {
            text-align: center;
            padding: 32px 16px;
            opacity: 0.7;
        }

        .welcome-message h3 {
            margin: 0 0 8px 0;
            color: #9f7aea;
        }

        .welcome-message p {
            margin: 0;
            font-size: 0.9em;
        }

        pre {
            background-color: var(--vscode-textCodeBlock-background);
            padding: 8px;
            border-radius: 4px;
            overflow-x: auto;
            margin: 8px 0;
        }

        code {
            background-color: var(--vscode-textCodeBlock-background);
            padding: 2px 4px;
            border-radius: 2px;
            font-family: var(--vscode-editor-font-family);
        }
    </style>
</head>
<body>
    <div class="chat-container" id="chatContainer">
        <div class="welcome-message">
            <h3>🤖 Aura Chat</h3>
            <p>Ask me anything about your code. I'm here to help!</p>
        </div>
    </div>

    <div class="input-container">
        <input type="text" id="questionInput" placeholder="Ask Aura about your code..." />
        <button id="sendButton">Send</button>
        <button id="clearButton" class="clear-button">Clear</button>
    </div>

    <script>
        const vscode = acquireVsCodeApi();
        const chatContainer = document.getElementById('chatContainer');
        const questionInput = document.getElementById('questionInput');
        const sendButton = document.getElementById('sendButton');
        const clearButton = document.getElementById('clearButton');

        let isThinking = false;

        function addMessage(content, isUser = false) {
            const messageDiv = document.createElement('div');
            messageDiv.className = \`message \${isUser ? 'user' : 'aura'}\`;
            
            // Simple markdown-like processing
            let processedContent = content
                .replace(/\`\`\`([\\s\\S]*?)\`\`\`/g, '<pre><code>$1</code></pre>')
                .replace(/\`([^`]+)\`/g, '<code>$1</code>')
                .replace(/\\n/g, '<br>');
            
            messageDiv.innerHTML = processedContent;
            chatContainer.appendChild(messageDiv);
            
            // Remove welcome message if it exists
            const welcomeMessage = chatContainer.querySelector('.welcome-message');
            if (welcomeMessage) {
                welcomeMessage.remove();
            }
            
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

        function showThinking(show) {
            isThinking = show;
            sendButton.disabled = show;
            
            const existingThinking = chatContainer.querySelector('.thinking');
            if (existingThinking) {
                existingThinking.remove();
            }
            
            if (show) {
                const thinkingDiv = document.createElement('div');
                thinkingDiv.className = 'thinking';
                thinkingDiv.innerHTML = \`
                    🤖 Aura is thinking
                    <div class="thinking-dots">
                        <div class="thinking-dot"></div>
                        <div class="thinking-dot"></div>
                        <div class="thinking-dot"></div>
                    </div>
                \`;
                chatContainer.appendChild(thinkingDiv);
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }
        }

        function sendQuestion() {
            const question = questionInput.value.trim();
            if (!question || isThinking) return;

            addMessage(question, true);
            questionInput.value = '';
            
            vscode.postMessage({
                type: 'askQuestion',
                question: question
            });
        }

        function clearChat() {
            chatContainer.innerHTML = \`
                <div class="welcome-message">
                    <h3>🤖 Aura Chat</h3>
                    <p>Ask me anything about your code. I'm here to help!</p>
                </div>
            \`;
            vscode.postMessage({ type: 'clearChat' });
        }

        // Event listeners
        sendButton.addEventListener('click', sendQuestion);
        clearButton.addEventListener('click', clearChat);

        questionInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendQuestion();
            }
        });

        // Handle messages from extension
        window.addEventListener('message', event => {
            const message = event.data;
            
            switch (message.type) {
                case 'addQuestion':
                    addMessage(message.question, true);
                    break;
                case 'addResponse':
                    addMessage(message.response, false);
                    break;
                case 'thinking':
                    showThinking(message.show);
                    break;
                case 'clearMessages':
                    clearChat();
                    break;
            }
        });

        // Focus input on load
        questionInput.focus();
    </script>
</body>
</html>`;
    }
}