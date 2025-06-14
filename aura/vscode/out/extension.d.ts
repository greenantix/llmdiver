/**
 * Aura VS Code Extension - Main Entry Point
 * =========================================
 *
 * The vessel through which Aura manifests in the sacred space of the IDE.
 * Real-time intelligence, seamless integration, autonomous assistance.
 *
 * @author Aura - Level 9 Autonomous AI Coding Assistant
 * @date 2025-06-13
 * @phase 2.2 - VS Code Integration
 */
import * as vscode from 'vscode';
export interface AuraConfiguration {
    autoAnalysis: boolean;
    serverUrl: string;
    llmProvider: string;
    analysisDepth: string;
    showNotifications: boolean;
    themeColor: string;
}
export declare class AuraExtension {
    private context;
    private connection;
    private statusBar;
    private notificationManager;
    private dashboardProvider;
    private codeAnalysisProvider;
    private suggestionsProvider;
    private chatProvider;
    private disposables;
    private config;
    constructor(context: vscode.ExtensionContext);
    private loadConfiguration;
    private initializeComponents;
    private registerCommands;
    private setupEventListeners;
    private isSupportedFile;
    private analyzeCurrentFile;
    private analyzeDocument;
    private analyzeProject;
    private generateSemanticCommit;
    private showQuickQuestionInput;
    private showDashboard;
    private toggleAutoAnalysis;
    private showInlineDiagnostics;
    private mapSeverity;
    private updateComponents;
    activate(): Promise<void>;
    deactivate(): void;
}
export declare function activate(context: vscode.ExtensionContext): Promise<void>;
export declare function deactivate(): void;
//# sourceMappingURL=extension.d.ts.map