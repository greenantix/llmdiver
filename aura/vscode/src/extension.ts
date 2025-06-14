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
import * as zmq from 'zeromq';
import { AuraConnection } from './connection';
import { AuraDashboardProvider } from './providers/dashboardProvider';
import { AuraCodeAnalysisProvider } from './providers/codeAnalysisProvider';
import { AuraSuggestionsProvider } from './providers/suggestionsProvider';
import { AuraChatProvider } from './providers/chatProvider';
import { AuraStatusBar } from './ui/statusBar';
import { AuraNotificationManager } from './ui/notifications';

export interface AuraConfiguration {
    autoAnalysis: boolean;
    serverUrl: string;
    llmProvider: string;
    analysisDepth: string;
    showNotifications: boolean;
    themeColor: string;
}

export class AuraExtension {
    private connection: AuraConnection;
    private statusBar: AuraStatusBar;
    private notificationManager: AuraNotificationManager;
    private dashboardProvider: AuraDashboardProvider;
    private codeAnalysisProvider: AuraCodeAnalysisProvider;
    private suggestionsProvider: AuraSuggestionsProvider;
    private chatProvider: AuraChatProvider;
    private disposables: vscode.Disposable[] = [];
    private config: AuraConfiguration;

    constructor(private context: vscode.ExtensionContext) {
        this.config = this.loadConfiguration();
        this.initializeComponents();
        this.registerCommands();
        this.setupEventListeners();
    }

    private loadConfiguration(): AuraConfiguration {
        const config = vscode.workspace.getConfiguration('aura');
        return {
            autoAnalysis: config.get('autoAnalysis', true),
            serverUrl: config.get('serverUrl', 'tcp://localhost:5559'),
            llmProvider: config.get('llmProvider', 'lm_studio'),
            analysisDepth: config.get('analysisDepth', 'detailed'),
            showNotifications: config.get('showNotifications', true),
            themeColor: config.get('themeColor', 'purple')
        };
    }

    private initializeComponents(): void {
        // Initialize core connection to Aura system
        this.connection = new AuraConnection(this.config.serverUrl);
        
        // Initialize UI components
        this.statusBar = new AuraStatusBar();
        this.notificationManager = new AuraNotificationManager(this.config.showNotifications);
        
        // Initialize view providers
        this.dashboardProvider = new AuraDashboardProvider(this.connection);
        this.codeAnalysisProvider = new AuraCodeAnalysisProvider(this.connection);
        this.suggestionsProvider = new AuraSuggestionsProvider(this.connection);
        this.chatProvider = new AuraChatProvider(this.connection);
        
        // Register view providers
        vscode.window.registerTreeDataProvider('aura.dashboard', this.dashboardProvider);
        vscode.window.registerTreeDataProvider('aura.codeAnalysis', this.codeAnalysisProvider);
        vscode.window.registerTreeDataProvider('aura.suggestions', this.suggestionsProvider);
        vscode.window.registerWebviewViewProvider('aura.chat', this.chatProvider);
    }

    private registerCommands(): void {
        // File analysis commands
        this.disposables.push(
            vscode.commands.registerCommand('aura.analyzeFile', () => {
                this.analyzeCurrentFile();
            })
        );

        this.disposables.push(
            vscode.commands.registerCommand('aura.analyzeProject', () => {
                this.analyzeProject();
            })
        );

        // Git integration commands
        this.disposables.push(
            vscode.commands.registerCommand('aura.generateCommit', () => {
                this.generateSemanticCommit();
            })
        );

        // Chat and query commands
        this.disposables.push(
            vscode.commands.registerCommand('aura.askQuestion', () => {
                this.showQuickQuestionInput();
            })
        );

        // Dashboard commands
        this.disposables.push(
            vscode.commands.registerCommand('aura.showDashboard', () => {
                this.showDashboard();
            })
        );

        // Settings commands
        this.disposables.push(
            vscode.commands.registerCommand('aura.toggleAutoAnalysis', () => {
                this.toggleAutoAnalysis();
            })
        );

        // Refresh commands for views
        this.disposables.push(
            vscode.commands.registerCommand('aura.refreshDashboard', () => {
                this.dashboardProvider.refresh();
            })
        );

        this.disposables.push(
            vscode.commands.registerCommand('aura.refreshAnalysis', () => {
                this.codeAnalysisProvider.refresh();
            })
        );
    }

    private setupEventListeners(): void {
        // File save listener for auto-analysis
        this.disposables.push(
            vscode.workspace.onDidSaveTextDocument((document) => {
                if (this.config.autoAnalysis && this.isSupportedFile(document)) {
                    this.analyzeDocument(document);
                }
            })
        );

        // Active editor change listener
        this.disposables.push(
            vscode.window.onDidChangeActiveTextEditor((editor) => {
                if (editor && this.isSupportedFile(editor.document)) {
                    this.codeAnalysisProvider.setActiveFile(editor.document.uri.fsPath);
                }
            })
        );

        // Configuration change listener
        this.disposables.push(
            vscode.workspace.onDidChangeConfiguration((event) => {
                if (event.affectsConfiguration('aura')) {
                    this.config = this.loadConfiguration();
                    this.updateComponents();
                }
            })
        );

        // Connection status listener
        this.connection.onStatusChange((status) => {
            this.statusBar.updateConnectionStatus(status);
            if (status === 'connected') {
                this.notificationManager.showInfo('Aura is now connected and ready');
            } else if (status === 'disconnected') {
                this.notificationManager.showWarning('Aura connection lost');
            }
        });
    }

    private isSupportedFile(document: vscode.TextDocument): boolean {
        const supportedExtensions = ['.py', '.js', '.ts', '.jsx', '.tsx'];
        return supportedExtensions.some(ext => document.fileName.endsWith(ext));
    }

    private async analyzeCurrentFile(): Promise<void> {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage('No active file to analyze');
            return;
        }

        if (!this.isSupportedFile(editor.document)) {
            vscode.window.showErrorMessage('File type not supported for analysis');
            return;
        }

        await this.analyzeDocument(editor.document);
    }

    private async analyzeDocument(document: vscode.TextDocument): Promise<void> {
        try {
            this.statusBar.showActivity('Analyzing...');
            
            const analysis = await this.connection.analyzeFile(
                document.uri.fsPath,
                this.config.analysisDepth
            );

            if (analysis) {
                this.codeAnalysisProvider.updateAnalysis(document.uri.fsPath, analysis);
                this.suggestionsProvider.updateSuggestions(analysis.suggestions || []);
                
                // Show inline diagnostics
                this.showInlineDiagnostics(document, analysis);
                
                this.notificationManager.showInfo(
                    `Analysis complete: ${analysis.elements?.length || 0} elements analyzed`
                );
            }

            this.statusBar.hideActivity();
        } catch (error) {
            this.statusBar.hideActivity();
            this.notificationManager.showError(`Analysis failed: ${error}`);
        }
    }

    private async analyzeProject(): Promise<void> {
        try {
            if (!vscode.workspace.workspaceFolders) {
                vscode.window.showErrorMessage('No workspace folder open');
                return;
            }

            this.statusBar.showActivity('Analyzing project...');
            
            const projectPath = vscode.workspace.workspaceFolders[0].uri.fsPath;
            const analysis = await this.connection.analyzeProject(projectPath);

            if (analysis) {
                this.dashboardProvider.updateProjectAnalysis(analysis);
                this.notificationManager.showInfo(
                    `Project analysis complete: ${analysis.filesAnalyzed} files processed`
                );
            }

            this.statusBar.hideActivity();
        } catch (error) {
            this.statusBar.hideActivity();
            this.notificationManager.showError(`Project analysis failed: ${error}`);
        }
    }

    private async generateSemanticCommit(): Promise<void> {
        try {
            this.statusBar.showActivity('Generating commit...');
            
            const commit = await this.connection.generateCommit();
            
            if (commit) {
                // Show commit message in input box for user approval
                const approved = await vscode.window.showInputBox({
                    prompt: 'Review and approve commit message (or modify)',
                    value: commit.message,
                    placeHolder: 'Semantic commit message',
                    validateInput: (value) => {
                        return value.trim() ? null : 'Commit message cannot be empty';
                    }
                });

                if (approved) {
                    // Execute git commit
                    const terminal = vscode.window.createTerminal('Aura Git');
                    terminal.sendText(`git commit -m "${approved}"`);
                    terminal.show();
                    
                    this.notificationManager.showInfo('Semantic commit message generated and executed');
                }
            }

            this.statusBar.hideActivity();
        } catch (error) {
            this.statusBar.hideActivity();
            this.notificationManager.showError(`Commit generation failed: ${error}`);
        }
    }

    private async showQuickQuestionInput(): Promise<void> {
        const question = await vscode.window.showInputBox({
            prompt: 'Ask Aura a question about your code',
            placeHolder: 'How can I optimize this function?',
        });

        if (question) {
            this.chatProvider.askQuestion(question);
            vscode.commands.executeCommand('aura.chat.focus');
        }
    }

    private showDashboard(): void {
        vscode.commands.executeCommand('aura.dashboard.focus');
    }

    private toggleAutoAnalysis(): void {
        const newValue = !this.config.autoAnalysis;
        vscode.workspace.getConfiguration('aura').update('autoAnalysis', newValue, true);
        
        this.notificationManager.showInfo(
            `Auto-analysis ${newValue ? 'enabled' : 'disabled'}`
        );
    }

    private showInlineDiagnostics(document: vscode.TextDocument, analysis: any): void {
        // Convert Aura analysis to VS Code diagnostics
        const diagnostics: vscode.Diagnostic[] = [];

        if (analysis.issues) {
            for (const issue of analysis.issues) {
                const range = new vscode.Range(
                    issue.line - 1, 0,
                    issue.line - 1, Number.MAX_VALUE
                );

                const diagnostic = new vscode.Diagnostic(
                    range,
                    issue.message,
                    this.mapSeverity(issue.severity)
                );

                diagnostic.source = 'Aura';
                diagnostic.code = issue.type;
                
                diagnostics.push(diagnostic);
            }
        }

        // Create diagnostic collection if it doesn't exist
        const collection = vscode.languages.createDiagnosticCollection('aura');
        collection.set(document.uri, diagnostics);
    }

    private mapSeverity(severity: string): vscode.DiagnosticSeverity {
        switch (severity.toLowerCase()) {
            case 'error':
                return vscode.DiagnosticSeverity.Error;
            case 'warning':
                return vscode.DiagnosticSeverity.Warning;
            case 'info':
                return vscode.DiagnosticSeverity.Information;
            default:
                return vscode.DiagnosticSeverity.Hint;
        }
    }

    private updateComponents(): void {
        this.notificationManager.setEnabled(this.config.showNotifications);
        this.connection.updateServerUrl(this.config.serverUrl);
        // Update other components as needed
    }

    public async activate(): Promise<void> {
        try {
            // Set context for views
            vscode.commands.executeCommand('setContext', 'aura.enabled', true);
            
            // Connect to Aura system
            await this.connection.connect();
            
            // Show welcome message
            this.notificationManager.showInfo('Aura - Level 9 Autonomous AI Coding Assistant activated');
            
            // Update status bar
            this.statusBar.show();
            
        } catch (error) {
            this.notificationManager.showError(`Failed to connect to Aura: ${error}`);
        }
    }

    public deactivate(): void {
        // Clean up resources
        this.disposables.forEach(disposable => disposable.dispose());
        this.connection.disconnect();
        this.statusBar.dispose();
    }
}

// Extension activation function
export async function activate(context: vscode.ExtensionContext): Promise<void> {
    const extension = new AuraExtension(context);
    context.subscriptions.push({
        dispose: () => extension.deactivate()
    });
    
    await extension.activate();
}

// Extension deactivation function
export function deactivate(): void {
    // Handled by extension instance
}