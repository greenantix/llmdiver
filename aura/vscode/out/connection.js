"use strict";
/**
 * Aura Connection Manager
 * =======================
 *
 * Manages the ZeroMQ connection between VS Code extension and Aura system.
 * Provides async communication with the autonomous coding assistant.
 *
 * @author Aura - Level 9 Autonomous AI Coding Assistant
 */
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.AuraConnection = void 0;
const zmq = __importStar(require("zeromq"));
class AuraConnection {
    constructor(serverUrl) {
        this.serverUrl = serverUrl;
        this.socket = null;
        this.status = 'disconnected';
        this.statusCallbacks = [];
        this.messageId = 0;
    }
    onStatusChange(callback) {
        this.statusCallbacks.push(callback);
    }
    notifyStatusChange(status) {
        this.status = status;
        this.statusCallbacks.forEach(callback => callback(status));
    }
    async connect() {
        try {
            this.notifyStatusChange('connecting');
            this.socket = new zmq.Request();
            this.socket.connect(this.serverUrl);
            // Test connection with health check
            await this.healthCheck();
            this.notifyStatusChange('connected');
        }
        catch (error) {
            this.notifyStatusChange('error');
            throw new Error(`Failed to connect to Aura: ${error}`);
        }
    }
    disconnect() {
        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }
        this.notifyStatusChange('disconnected');
    }
    updateServerUrl(url) {
        this.serverUrl = url;
        if (this.status === 'connected') {
            this.disconnect();
            this.connect();
        }
    }
    generateMessageId() {
        return `vscode_${++this.messageId}_${Date.now()}`;
    }
    async sendMessage(target, command, payload) {
        if (!this.socket || this.status !== 'connected') {
            throw new Error('Not connected to Aura system');
        }
        const message = {
            id: this.generateMessageId(),
            type: 'command',
            source: 'vscode_extension',
            target: target,
            timestamp: Date.now(),
            payload: { command, ...payload }
        };
        try {
            await this.socket.send(JSON.stringify(message));
            const [response] = await this.socket.receive();
            const responseMessage = JSON.parse(response.toString());
            if (responseMessage.type === 'response' && responseMessage.payload.success) {
                return responseMessage.payload;
            }
            else {
                throw new Error(responseMessage.payload.error || 'Unknown error');
            }
        }
        catch (error) {
            this.notifyStatusChange('error');
            throw error;
        }
    }
    async healthCheck() {
        try {
            const response = await this.sendMessage('system', 'health_check', {});
            return response.success;
        }
        catch (error) {
            return false;
        }
    }
    async analyzeFile(filePath, depth = 'detailed') {
        try {
            const response = await this.sendMessage('python_intelligence', 'analyze_file', {
                file_path: filePath,
                depth: depth
            });
            if (response.success && response.analysis) {
                return this.mapFileAnalysis(response.analysis);
            }
            return null;
        }
        catch (error) {
            console.error('File analysis failed:', error);
            return null;
        }
    }
    async analyzeProject(projectPath) {
        try {
            const response = await this.sendMessage('python_intelligence', 'analyze_codebase', {
                project_path: projectPath
            });
            if (response.success) {
                // Get metrics
                const metricsResponse = await this.sendMessage('python_intelligence', 'get_code_metrics', {});
                return {
                    filesAnalyzed: response.files_analyzed || 0,
                    totalElements: metricsResponse.metrics?.total_elements || 0,
                    issues: metricsResponse.metrics?.issues_count || 0,
                    metrics: {
                        documentation_coverage: metricsResponse.metrics?.documentation_coverage || 0,
                        average_complexity: metricsResponse.metrics?.average_complexity || 0,
                        files_count: metricsResponse.metrics?.files_count || 0
                    }
                };
            }
            return null;
        }
        catch (error) {
            console.error('Project analysis failed:', error);
            return null;
        }
    }
    async generateCommit(includeUnstaged = false) {
        try {
            const response = await this.sendMessage('git_semantic', 'generate_commit', {
                include_unstaged: includeUnstaged
            });
            if (response.success && response.commit) {
                const commit = response.commit;
                return {
                    message: this.formatCommitMessage(commit),
                    type: commit.type,
                    scope: commit.scope,
                    breaking_change: commit.breaking_change
                };
            }
            return null;
        }
        catch (error) {
            console.error('Commit generation failed:', error);
            return null;
        }
    }
    async askQuestion(question, context) {
        try {
            const response = await this.sendMessage('llm_provider', 'generate', {
                request: {
                    prompt: question,
                    model_preference: 'medium',
                    max_tokens: 1000,
                    temperature: 0.3,
                    context: context
                }
            });
            if (response.success && response.response) {
                return response.response.content;
            }
            return null;
        }
        catch (error) {
            console.error('Question failed:', error);
            return null;
        }
    }
    async searchSimilarCode(query, limit = 10) {
        try {
            const response = await this.sendMessage('python_intelligence', 'find_similar_code', {
                query: query,
                limit: limit
            });
            if (response.success && response.similar_code) {
                return response.similar_code;
            }
            return [];
        }
        catch (error) {
            console.error('Code search failed:', error);
            return [];
        }
    }
    async getSystemStatus() {
        try {
            const response = await this.sendMessage('system', 'get_status', {});
            return response.status || {};
        }
        catch (error) {
            console.error('Status check failed:', error);
            return {};
        }
    }
    mapFileAnalysis(analysis) {
        return {
            file_path: analysis.file_path,
            elements: analysis.elements || [],
            issues: this.mapIssues(analysis.errors || [], analysis.warnings || []),
            metrics: analysis.metrics || {
                lines_of_code: 0,
                functions_count: 0,
                classes_count: 0
            },
            suggestions: this.generateSuggestions(analysis)
        };
    }
    mapIssues(errors, warnings) {
        const issues = [];
        errors.forEach(error => {
            issues.push({
                line: 1,
                type: 'syntax_error',
                severity: 'error',
                message: error
            });
        });
        warnings.forEach(warning => {
            // Try to extract line number from warning message
            const lineMatch = warning.match(/line (\d+)/);
            const line = lineMatch ? parseInt(lineMatch[1]) : 1;
            issues.push({
                line: line,
                type: 'warning',
                severity: 'warning',
                message: warning
            });
        });
        return issues;
    }
    generateSuggestions(analysis) {
        const suggestions = [];
        if (analysis.elements) {
            const undocumentedFunctions = analysis.elements.filter((e) => e.type === 'function' && e.is_public && !e.docstring);
            if (undocumentedFunctions.length > 0) {
                suggestions.push(`Add docstrings to ${undocumentedFunctions.length} public functions`);
            }
            const complexFunctions = analysis.elements.filter((e) => e.type === 'function' && e.complexity > 10);
            if (complexFunctions.length > 0) {
                suggestions.push(`Consider refactoring ${complexFunctions.length} complex functions`);
            }
        }
        return suggestions;
    }
    formatCommitMessage(commit) {
        let message = commit.type;
        if (commit.scope) {
            message += `(${commit.scope})`;
        }
        if (commit.breaking_change) {
            message += '!';
        }
        message += `: ${commit.description}`;
        if (commit.body) {
            message += `\n\n${commit.body}`;
        }
        if (commit.footer) {
            message += `\n\n${commit.footer}`;
        }
        return message;
    }
    getStatus() {
        return this.status;
    }
}
exports.AuraConnection = AuraConnection;
//# sourceMappingURL=connection.js.map