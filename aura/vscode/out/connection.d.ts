/**
 * Aura Connection Manager
 * =======================
 *
 * Manages the ZeroMQ connection between VS Code extension and Aura system.
 * Provides async communication with the autonomous coding assistant.
 *
 * @author Aura - Level 9 Autonomous AI Coding Assistant
 */
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
export declare class AuraConnection {
    private serverUrl;
    private socket;
    private status;
    private statusCallbacks;
    private messageId;
    constructor(serverUrl: string);
    onStatusChange(callback: (status: ConnectionStatus) => void): void;
    private notifyStatusChange;
    connect(): Promise<void>;
    disconnect(): void;
    updateServerUrl(url: string): void;
    private generateMessageId;
    private sendMessage;
    healthCheck(): Promise<boolean>;
    analyzeFile(filePath: string, depth?: string): Promise<FileAnalysis | null>;
    analyzeProject(projectPath: string): Promise<ProjectAnalysis | null>;
    generateCommit(includeUnstaged?: boolean): Promise<CommitGeneration | null>;
    askQuestion(question: string, context?: any): Promise<string | null>;
    searchSimilarCode(query: string, limit?: number): Promise<any[]>;
    getSystemStatus(): Promise<any>;
    private mapFileAnalysis;
    private mapIssues;
    private generateSuggestions;
    private formatCommitMessage;
    getStatus(): ConnectionStatus;
}
//# sourceMappingURL=connection.d.ts.map