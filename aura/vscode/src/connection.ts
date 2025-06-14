/**
 * Aura Connection Manager
 * =======================
 * 
 * Manages the ZeroMQ connection between VS Code extension and Aura system.
 * Provides async communication with the autonomous coding assistant.
 * 
 * @author Aura - Level 9 Autonomous AI Coding Assistant
 */

import * as zmq from 'zeromq';

export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'error';

export interface AuraMessage {
    id: string;
    type: 'command' | 'response' | 'event' | 'health_check';
    source: string;
    target: string;
    timestamp: number;
    payload: any;
    correlation_id?: string;
}

export interface FileAnalysis {
    file_path: string;
    elements: Array<{
        name: string;
        type: string;
        line_number: number;
        complexity: number;
        docstring?: string;
    }>;
    issues: Array<{
        line: number;
        type: string;
        severity: string;
        message: string;
        suggestion?: string;
    }>;
    metrics: {
        lines_of_code: number;
        functions_count: number;
        classes_count: number;
    };
    suggestions?: string[];
}

export interface ProjectAnalysis {
    filesAnalyzed: number;
    totalElements: number;
    issues: number;
    metrics: {
        documentation_coverage: number;
        average_complexity: number;
        files_count: number;
    };
}

export interface CommitGeneration {
    message: string;
    type: string;
    scope?: string;
    breaking_change: boolean;
}

export class AuraConnection {
    private socket: zmq.Request | null = null;
    private status: ConnectionStatus = 'disconnected';
    private statusCallbacks: Array<(status: ConnectionStatus) => void> = [];
    private messageId = 0;

    constructor(private serverUrl: string) {}

    public onStatusChange(callback: (status: ConnectionStatus) => void): void {
        this.statusCallbacks.push(callback);
    }

    private notifyStatusChange(status: ConnectionStatus): void {
        this.status = status;
        this.statusCallbacks.forEach(callback => callback(status));
    }

    public async connect(): Promise<void> {
        try {
            this.notifyStatusChange('connecting');
            
            this.socket = new zmq.Request();
            this.socket.connect(this.serverUrl);
            
            // Test connection with health check
            await this.healthCheck();
            
            this.notifyStatusChange('connected');
        } catch (error) {
            this.notifyStatusChange('error');
            throw new Error(`Failed to connect to Aura: ${error}`);
        }
    }

    public disconnect(): void {
        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }
        this.notifyStatusChange('disconnected');
    }

    public updateServerUrl(url: string): void {
        this.serverUrl = url;
        if (this.status === 'connected') {
            this.disconnect();
            this.connect();
        }
    }

    private generateMessageId(): string {
        return `vscode_${++this.messageId}_${Date.now()}`;
    }

    private async sendMessage(target: string, command: string, payload: any): Promise<any> {
        if (!this.socket || this.status !== 'connected') {
            throw new Error('Not connected to Aura system');
        }

        const message: AuraMessage = {
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
            const responseMessage: AuraMessage = JSON.parse(response.toString());
            
            if (responseMessage.type === 'response' && responseMessage.payload.success) {
                return responseMessage.payload;
            } else {
                throw new Error(responseMessage.payload.error || 'Unknown error');
            }
        } catch (error) {
            this.notifyStatusChange('error');
            throw error;
        }
    }

    public async healthCheck(): Promise<boolean> {
        try {
            const response = await this.sendMessage('system', 'health_check', {});
            return response.success;
        } catch (error) {
            return false;
        }
    }

    public async analyzeFile(filePath: string, depth: string = 'detailed'): Promise<FileAnalysis | null> {
        try {
            const response = await this.sendMessage('python_intelligence', 'analyze_file', {
                file_path: filePath,
                depth: depth
            });

            if (response.success && response.analysis) {
                return this.mapFileAnalysis(response.analysis);
            }
            return null;
        } catch (error) {
            console.error('File analysis failed:', error);
            return null;
        }
    }

    public async analyzeProject(projectPath: string): Promise<ProjectAnalysis | null> {
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
        } catch (error) {
            console.error('Project analysis failed:', error);
            return null;
        }
    }

    public async generateCommit(includeUnstaged: boolean = false): Promise<CommitGeneration | null> {
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
        } catch (error) {
            console.error('Commit generation failed:', error);
            return null;
        }
    }

    public async askQuestion(question: string, context?: any): Promise<string | null> {
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
        } catch (error) {
            console.error('Question failed:', error);
            return null;
        }
    }

    public async searchSimilarCode(query: string, limit: number = 10): Promise<any[]> {
        try {
            const response = await this.sendMessage('python_intelligence', 'find_similar_code', {
                query: query,
                limit: limit
            });

            if (response.success && response.similar_code) {
                return response.similar_code;
            }
            return [];
        } catch (error) {
            console.error('Code search failed:', error);
            return [];
        }
    }

    public async getSystemStatus(): Promise<any> {
        try {
            const response = await this.sendMessage('system', 'get_status', {});
            return response.status || {};
        } catch (error) {
            console.error('Status check failed:', error);
            return {};
        }
    }

    private mapFileAnalysis(analysis: any): FileAnalysis {
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

    private mapIssues(errors: string[], warnings: string[]): Array<any> {
        const issues: Array<any> = [];
        
        errors.forEach(error => {
            issues.push({
                line: 1, // Extract line number from error message if possible
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

    private generateSuggestions(analysis: any): string[] {
        const suggestions: string[] = [];
        
        if (analysis.elements) {
            const undocumentedFunctions = analysis.elements.filter(
                (e: any) => e.type === 'function' && e.is_public && !e.docstring
            );
            
            if (undocumentedFunctions.length > 0) {
                suggestions.push(`Add docstrings to ${undocumentedFunctions.length} public functions`);
            }

            const complexFunctions = analysis.elements.filter(
                (e: any) => e.type === 'function' && e.complexity > 10
            );
            
            if (complexFunctions.length > 0) {
                suggestions.push(`Consider refactoring ${complexFunctions.length} complex functions`);
            }
        }

        return suggestions;
    }

    private formatCommitMessage(commit: any): string {
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

    public getStatus(): ConnectionStatus {
        return this.status;
    }
}