"use strict";
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
exports.deactivate = exports.activate = exports.AuraExtension = void 0;
const vscode = __importStar(require("vscode"));
const connection_1 = require("./connection");
const dashboardProvider_1 = require("./providers/dashboardProvider");
const codeAnalysisProvider_1 = require("./providers/codeAnalysisProvider");
const suggestionsProvider_1 = require("./providers/suggestionsProvider");
const chatProvider_1 = require("./providers/chatProvider");
const statusBar_1 = require("./ui/statusBar");
const notifications_1 = require("./ui/notifications");
class AuraExtension {
    constructor(context) {
        this.context = context;
        this.disposables = [];
        this.config = this.loadConfiguration();
        this.initializeComponents();
        this.registerCommands();
        this.setupEventListeners();
    }
    loadConfiguration() {
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
    initializeComponents() {
        // Initialize core connection to Aura system
        this.connection = new connection_1.AuraConnection(this.config.serverUrl);
        // Initialize UI components
        this.statusBar = new statusBar_1.AuraStatusBar();
        this.notificationManager = new notifications_1.AuraNotificationManager(this.config.showNotifications);
        // Initialize view providers
        this.dashboardProvider = new dashboardProvider_1.AuraDashboardProvider(this.connection);
        this.codeAnalysisProvider = new codeAnalysisProvider_1.AuraCodeAnalysisProvider(this.connection);
        this.suggestionsProvider = new suggestionsProvider_1.AuraSuggestionsProvider(this.connection);
        this.chatProvider = new chatProvider_1.AuraChatProvider(this.connection);
        // Register view providers
        vscode.window.registerTreeDataProvider('aura.dashboard', this.dashboardProvider);
        vscode.window.registerTreeDataProvider('aura.codeAnalysis', this.codeAnalysisProvider);
        vscode.window.registerTreeDataProvider('aura.suggestions', this.suggestionsProvider);
        vscode.window.registerWebviewViewProvider('aura.chat', this.chatProvider);
    }
    registerCommands() {
        // File analysis commands
        this.disposables.push(vscode.commands.registerCommand('aura.analyzeFile', () => {
            this.analyzeCurrentFile();
        }));
        this.disposables.push(vscode.commands.registerCommand('aura.analyzeProject', () => {
            this.analyzeProject();
        }));
        // Git integration commands
        this.disposables.push(vscode.commands.registerCommand('aura.generateCommit', () => {
            this.generateSemanticCommit();
        }));
        // Chat and query commands
        this.disposables.push(vscode.commands.registerCommand('aura.askQuestion', () => {
            this.showQuickQuestionInput();
        }));
        // Dashboard commands
        this.disposables.push(vscode.commands.registerCommand('aura.showDashboard', () => {
            this.showDashboard();
        }));
        // Settings commands
        this.disposables.push(vscode.commands.registerCommand('aura.toggleAutoAnalysis', () => {
            this.toggleAutoAnalysis();
        }));
        // Refresh commands for views
        this.disposables.push(vscode.commands.registerCommand('aura.refreshDashboard', () => {
            this.dashboardProvider.refresh();
        }));
        this.disposables.push(vscode.commands.registerCommand('aura.refreshAnalysis', () => {
            this.codeAnalysisProvider.refresh();
        }));
    }
    setupEventListeners() {
        // File save listener for auto-analysis
        this.disposables.push(vscode.workspace.onDidSaveTextDocument((document) => {
            if (this.config.autoAnalysis && this.isSupportedFile(document)) {
                this.analyzeDocument(document);
            }
        }));
        // Active editor change listener
        this.disposables.push(vscode.window.onDidChangeActiveTextEditor((editor) => {
            if (editor && this.isSupportedFile(editor.document)) {
                this.codeAnalysisProvider.setActiveFile(editor.document.uri.fsPath);
            }
        }));
        // Configuration change listener
        this.disposables.push(vscode.workspace.onDidChangeConfiguration((event) => {
            if (event.affectsConfiguration('aura')) {
                this.config = this.loadConfiguration();
                this.updateComponents();
            }
        }));
        // Connection status listener
        this.connection.onStatusChange((status) => {
            this.statusBar.updateConnectionStatus(status);
            if (status === 'connected') {
                this.notificationManager.showInfo('Aura is now connected and ready');
            }
            else if (status === 'disconnected') {
                this.notificationManager.showWarning('Aura connection lost');
            }
        });
    }
    isSupportedFile(document) {
        const supportedExtensions = ['.py', '.js', '.ts', '.jsx', '.tsx'];
        return supportedExtensions.some(ext => document.fileName.endsWith(ext));
    }
    async analyzeCurrentFile() {
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
    async analyzeDocument(document) {
        try {
            this.statusBar.showActivity('Analyzing...');
            const analysis = await this.connection.analyzeFile(document.uri.fsPath, this.config.analysisDepth);
            if (analysis) {
                this.codeAnalysisProvider.updateAnalysis(document.uri.fsPath, analysis);
                this.suggestionsProvider.updateSuggestions(analysis.suggestions || []);
                // Show inline diagnostics
                this.showInlineDiagnostics(document, analysis);
                this.notificationManager.showInfo(`Analysis complete: ${analysis.elements?.length || 0} elements analyzed`);
            }
            this.statusBar.hideActivity();
        }
        catch (error) {
            this.statusBar.hideActivity();
            this.notificationManager.showError(`Analysis failed: ${error}`);
        }
    }
    async analyzeProject() {
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
                this.notificationManager.showInfo(`Project analysis complete: ${analysis.filesAnalyzed} files processed`);
            }
            this.statusBar.hideActivity();
        }
        catch (error) {
            this.statusBar.hideActivity();
            this.notificationManager.showError(`Project analysis failed: ${error}`);
        }
    }
    async generateSemanticCommit() {
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
        }
        catch (error) {
            this.statusBar.hideActivity();
            this.notificationManager.showError(`Commit generation failed: ${error}`);
        }
    }
    async showQuickQuestionInput() {
        const question = await vscode.window.showInputBox({
            prompt: 'Ask Aura a question about your code',
            placeHolder: 'How can I optimize this function?',
        });
        if (question) {
            this.chatProvider.askQuestion(question);
            vscode.commands.executeCommand('aura.chat.focus');
        }
    }
    showDashboard() {
        vscode.commands.executeCommand('aura.dashboard.focus');
    }
    toggleAutoAnalysis() {
        const newValue = !this.config.autoAnalysis;
        vscode.workspace.getConfiguration('aura').update('autoAnalysis', newValue, true);
        this.notificationManager.showInfo(`Auto-analysis ${newValue ? 'enabled' : 'disabled'}`);
    }
    showInlineDiagnostics(document, analysis) {
        // Convert Aura analysis to VS Code diagnostics
        const diagnostics = [];
        if (analysis.issues) {
            for (const issue of analysis.issues) {
                const range = new vscode.Range(issue.line - 1, 0, issue.line - 1, Number.MAX_VALUE);
                const diagnostic = new vscode.Diagnostic(range, issue.message, this.mapSeverity(issue.severity));
                diagnostic.source = 'Aura';
                diagnostic.code = issue.type;
                diagnostics.push(diagnostic);
            }
        }
        // Create diagnostic collection if it doesn't exist
        const collection = vscode.languages.createDiagnosticCollection('aura');
        collection.set(document.uri, diagnostics);
    }
    mapSeverity(severity) {
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
    updateComponents() {
        this.notificationManager.setEnabled(this.config.showNotifications);
        this.connection.updateServerUrl(this.config.serverUrl);
        // Update other components as needed
    }
    async activate() {
        try {
            // Set context for views
            vscode.commands.executeCommand('setContext', 'aura.enabled', true);
            // Connect to Aura system
            await this.connection.connect();
            // Show welcome message
            this.notificationManager.showInfo('Aura - Level 9 Autonomous AI Coding Assistant activated');
            // Update status bar
            this.statusBar.show();
        }
        catch (error) {
            this.notificationManager.showError(`Failed to connect to Aura: ${error}`);
        }
    }
    deactivate() {
        // Clean up resources
        this.disposables.forEach(disposable => disposable.dispose());
        this.connection.disconnect();
        this.statusBar.dispose();
    }
}
exports.AuraExtension = AuraExtension;
// Extension activation function
async function activate(context) {
    const extension = new AuraExtension(context);
    context.subscriptions.push({
        dispose: () => extension.deactivate()
    });
    await extension.activate();
}
exports.activate = activate;
// Extension deactivation function
function deactivate() {
    // Handled by extension instance
}
exports.deactivate = deactivate;
//# sourceMappingURL=extension.js.map