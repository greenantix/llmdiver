"use strict";
/**
 * Aura Dashboard Provider
 * =======================
 *
 * Provides the main dashboard view in VS Code sidebar.
 * Shows system status, project metrics, and quick actions.
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
exports.AuraDashboardProvider = exports.AuraDashboardItem = void 0;
const vscode = __importStar(require("vscode"));
class AuraDashboardItem extends vscode.TreeItem {
    constructor(label, collapsibleState, command, iconPath, description, tooltip, contextValue) {
        super(label, collapsibleState);
        this.label = label;
        this.collapsibleState = collapsibleState;
        this.command = command;
        this.iconPath = iconPath;
        this.description = description;
        this.tooltip = tooltip;
        this.contextValue = contextValue;
        this.description = description;
        this.tooltip = tooltip;
        this.contextValue = contextValue;
    }
}
exports.AuraDashboardItem = AuraDashboardItem;
class AuraDashboardProvider {
    constructor(connection) {
        this.connection = connection;
        this._onDidChangeTreeData = new vscode.EventEmitter();
        this.onDidChangeTreeData = this._onDidChangeTreeData.event;
        this.projectAnalysis = null;
    }
    refresh() {
        this._onDidChangeTreeData.fire();
    }
    updateProjectAnalysis(analysis) {
        this.projectAnalysis = analysis;
        this.refresh();
    }
    getTreeItem(element) {
        return element;
    }
    getChildren(element) {
        if (!element) {
            return Promise.resolve(this.getRootItems());
        }
        switch (element.contextValue) {
            case 'systemStatus':
                return Promise.resolve(this.getSystemStatusItems());
            case 'projectMetrics':
                return Promise.resolve(this.getProjectMetricsItems());
            case 'quickActions':
                return Promise.resolve(this.getQuickActionItems());
            default:
                return Promise.resolve([]);
        }
    }
    getRootItems() {
        const items = [];
        // System Status Section
        items.push(new AuraDashboardItem('System Status', vscode.TreeItemCollapsibleState.Expanded, undefined, new vscode.ThemeIcon('pulse'), undefined, 'Aura system health and connection status', 'systemStatus'));
        // Project Metrics Section
        if (this.projectAnalysis) {
            items.push(new AuraDashboardItem('Project Metrics', vscode.TreeItemCollapsibleState.Expanded, undefined, new vscode.ThemeIcon('graph'), undefined, 'Current project analysis metrics', 'projectMetrics'));
        }
        // Quick Actions Section
        items.push(new AuraDashboardItem('Quick Actions', vscode.TreeItemCollapsibleState.Expanded, undefined, new vscode.ThemeIcon('zap'), undefined, 'Common Aura commands and actions', 'quickActions'));
        return items;
    }
    getSystemStatusItems() {
        const items = [];
        // Connection Status
        const connectionStatus = this.connection.getStatus();
        const statusIcon = connectionStatus === 'connected' ? 'check' : 'error';
        const statusColor = connectionStatus === 'connected' ? 'green' : 'red';
        items.push(new AuraDashboardItem('Connection', vscode.TreeItemCollapsibleState.None, undefined, new vscode.ThemeIcon(statusIcon), connectionStatus, `Aura system is ${connectionStatus}`));
        // LLM Provider Status
        items.push(new AuraDashboardItem('LLM Provider', vscode.TreeItemCollapsibleState.None, {
            command: 'aura.checkLLMStatus',
            title: 'Check LLM Status'
        }, new vscode.ThemeIcon('brain'), 'Unknown', 'Click to check LLM provider status'));
        // Code Intelligence Status
        items.push(new AuraDashboardItem('Code Intelligence', vscode.TreeItemCollapsibleState.None, undefined, new vscode.ThemeIcon('code'), 'Active', 'Python code analysis engine'));
        return items;
    }
    getProjectMetricsItems() {
        if (!this.projectAnalysis) {
            return [];
        }
        const items = [];
        const metrics = this.projectAnalysis.metrics;
        // Files Analyzed
        items.push(new AuraDashboardItem('Files Analyzed', vscode.TreeItemCollapsibleState.None, undefined, new vscode.ThemeIcon('file-code'), metrics.files_count.toString(), `${metrics.files_count} Python files in project`));
        // Total Elements
        items.push(new AuraDashboardItem('Code Elements', vscode.TreeItemCollapsibleState.None, undefined, new vscode.ThemeIcon('symbol-class'), this.projectAnalysis.totalElements.toString(), `Functions, classes, and other code elements`));
        // Documentation Coverage
        const docCoverage = Math.round(metrics.documentation_coverage * 100);
        const docIcon = docCoverage >= 80 ? 'check' : docCoverage >= 50 ? 'warning' : 'error';
        items.push(new AuraDashboardItem('Documentation', vscode.TreeItemCollapsibleState.None, undefined, new vscode.ThemeIcon(docIcon), `${docCoverage}%`, `Documentation coverage: ${docCoverage}%`));
        // Average Complexity
        const avgComplexity = metrics.average_complexity.toFixed(1);
        const complexityIcon = metrics.average_complexity <= 5 ? 'check' :
            metrics.average_complexity <= 10 ? 'warning' : 'error';
        items.push(new AuraDashboardItem('Complexity', vscode.TreeItemCollapsibleState.None, undefined, new vscode.ThemeIcon(complexityIcon), avgComplexity, `Average cyclomatic complexity: ${avgComplexity}`));
        // Issues Found
        const issuesIcon = this.projectAnalysis.issues === 0 ? 'check' :
            this.projectAnalysis.issues < 10 ? 'warning' : 'error';
        items.push(new AuraDashboardItem('Issues', vscode.TreeItemCollapsibleState.None, {
            command: 'aura.showIssues',
            title: 'Show Issues'
        }, new vscode.ThemeIcon(issuesIcon), this.projectAnalysis.issues.toString(), `${this.projectAnalysis.issues} potential issues found`));
        return items;
    }
    getQuickActionItems() {
        const items = [];
        // Analyze Current File
        items.push(new AuraDashboardItem('Analyze File', vscode.TreeItemCollapsibleState.None, {
            command: 'aura.analyzeFile',
            title: 'Analyze Current File'
        }, new vscode.ThemeIcon('search'), undefined, 'Analyze the currently open file'));
        // Analyze Project
        items.push(new AuraDashboardItem('Analyze Project', vscode.TreeItemCollapsibleState.None, {
            command: 'aura.analyzeProject',
            title: 'Analyze Entire Project'
        }, new vscode.ThemeIcon('project'), undefined, 'Analyze the entire project codebase'));
        // Generate Commit
        items.push(new AuraDashboardItem('Generate Commit', vscode.TreeItemCollapsibleState.None, {
            command: 'aura.generateCommit',
            title: 'Generate Semantic Commit'
        }, new vscode.ThemeIcon('git-commit'), undefined, 'Generate a semantic commit message'));
        // Ask Question
        items.push(new AuraDashboardItem('Ask Aura', vscode.TreeItemCollapsibleState.None, {
            command: 'aura.askQuestion',
            title: 'Ask Aura a Question'
        }, new vscode.ThemeIcon('comment-discussion'), undefined, 'Ask Aura a question about your code'));
        // Toggle Auto-Analysis
        items.push(new AuraDashboardItem('Auto-Analysis', vscode.TreeItemCollapsibleState.None, {
            command: 'aura.toggleAutoAnalysis',
            title: 'Toggle Auto-Analysis'
        }, new vscode.ThemeIcon('settings-gear'), undefined, 'Toggle automatic code analysis on save'));
        return items;
    }
}
exports.AuraDashboardProvider = AuraDashboardProvider;
//# sourceMappingURL=dashboardProvider.js.map