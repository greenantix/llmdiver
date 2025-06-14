/**
 * Aura Dashboard Provider
 * =======================
 * 
 * Provides the main dashboard view in VS Code sidebar.
 * Shows system status, project metrics, and quick actions.
 */

import * as vscode from 'vscode';
import { AuraConnection, ProjectAnalysis } from '../connection';

export class AuraDashboardItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState,
        public readonly command?: vscode.Command,
        public readonly iconPath?: vscode.ThemeIcon,
        public readonly description?: string,
        public readonly tooltip?: string,
        public readonly contextValue?: string
    ) {
        super(label, collapsibleState);
        this.description = description;
        this.tooltip = tooltip;
        this.contextValue = contextValue;
    }
}

export class AuraDashboardProvider implements vscode.TreeDataProvider<AuraDashboardItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<AuraDashboardItem | undefined | null | void> = new vscode.EventEmitter<AuraDashboardItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<AuraDashboardItem | undefined | null | void> = this._onDidChangeTreeData.event;

    private projectAnalysis: ProjectAnalysis | null = null;

    constructor(private connection: AuraConnection) {}

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    updateProjectAnalysis(analysis: ProjectAnalysis): void {
        this.projectAnalysis = analysis;
        this.refresh();
    }

    getTreeItem(element: AuraDashboardItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: AuraDashboardItem): Thenable<AuraDashboardItem[]> {
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

    private getRootItems(): AuraDashboardItem[] {
        const items: AuraDashboardItem[] = [];

        // System Status Section
        items.push(new AuraDashboardItem(
            'System Status',
            vscode.TreeItemCollapsibleState.Expanded,
            undefined,
            new vscode.ThemeIcon('pulse'),
            undefined,
            'Aura system health and connection status',
            'systemStatus'
        ));

        // Project Metrics Section
        if (this.projectAnalysis) {
            items.push(new AuraDashboardItem(
                'Project Metrics',
                vscode.TreeItemCollapsibleState.Expanded,
                undefined,
                new vscode.ThemeIcon('graph'),
                undefined,
                'Current project analysis metrics',
                'projectMetrics'
            ));
        }

        // Quick Actions Section
        items.push(new AuraDashboardItem(
            'Quick Actions',
            vscode.TreeItemCollapsibleState.Expanded,
            undefined,
            new vscode.ThemeIcon('zap'),
            undefined,
            'Common Aura commands and actions',
            'quickActions'
        ));

        return items;
    }

    private getSystemStatusItems(): AuraDashboardItem[] {
        const items: AuraDashboardItem[] = [];

        // Connection Status
        const connectionStatus = this.connection.getStatus();
        const statusIcon = connectionStatus === 'connected' ? 'check' : 'error';
        const statusColor = connectionStatus === 'connected' ? 'green' : 'red';
        
        items.push(new AuraDashboardItem(
            'Connection',
            vscode.TreeItemCollapsibleState.None,
            undefined,
            new vscode.ThemeIcon(statusIcon),
            connectionStatus,
            `Aura system is ${connectionStatus}`
        ));

        // LLM Provider Status
        items.push(new AuraDashboardItem(
            'LLM Provider',
            vscode.TreeItemCollapsibleState.None,
            {
                command: 'aura.checkLLMStatus',
                title: 'Check LLM Status'
            },
            new vscode.ThemeIcon('brain'),
            'Unknown',
            'Click to check LLM provider status'
        ));

        // Code Intelligence Status
        items.push(new AuraDashboardItem(
            'Code Intelligence',
            vscode.TreeItemCollapsibleState.None,
            undefined,
            new vscode.ThemeIcon('code'),
            'Active',
            'Python code analysis engine'
        ));

        return items;
    }

    private getProjectMetricsItems(): AuraDashboardItem[] {
        if (!this.projectAnalysis) {
            return [];
        }

        const items: AuraDashboardItem[] = [];
        const metrics = this.projectAnalysis.metrics;

        // Files Analyzed
        items.push(new AuraDashboardItem(
            'Files Analyzed',
            vscode.TreeItemCollapsibleState.None,
            undefined,
            new vscode.ThemeIcon('file-code'),
            metrics.files_count.toString(),
            `${metrics.files_count} Python files in project`
        ));

        // Total Elements
        items.push(new AuraDashboardItem(
            'Code Elements',
            vscode.TreeItemCollapsibleState.None,
            undefined,
            new vscode.ThemeIcon('symbol-class'),
            this.projectAnalysis.totalElements.toString(),
            `Functions, classes, and other code elements`
        ));

        // Documentation Coverage
        const docCoverage = Math.round(metrics.documentation_coverage * 100);
        const docIcon = docCoverage >= 80 ? 'check' : docCoverage >= 50 ? 'warning' : 'error';
        
        items.push(new AuraDashboardItem(
            'Documentation',
            vscode.TreeItemCollapsibleState.None,
            undefined,
            new vscode.ThemeIcon(docIcon),
            `${docCoverage}%`,
            `Documentation coverage: ${docCoverage}%`
        ));

        // Average Complexity
        const avgComplexity = metrics.average_complexity.toFixed(1);
        const complexityIcon = metrics.average_complexity <= 5 ? 'check' : 
                             metrics.average_complexity <= 10 ? 'warning' : 'error';
        
        items.push(new AuraDashboardItem(
            'Complexity',
            vscode.TreeItemCollapsibleState.None,
            undefined,
            new vscode.ThemeIcon(complexityIcon),
            avgComplexity,
            `Average cyclomatic complexity: ${avgComplexity}`
        ));

        // Issues Found
        const issuesIcon = this.projectAnalysis.issues === 0 ? 'check' : 
                          this.projectAnalysis.issues < 10 ? 'warning' : 'error';
        
        items.push(new AuraDashboardItem(
            'Issues',
            vscode.TreeItemCollapsibleState.None,
            {
                command: 'aura.showIssues',
                title: 'Show Issues'
            },
            new vscode.ThemeIcon(issuesIcon),
            this.projectAnalysis.issues.toString(),
            `${this.projectAnalysis.issues} potential issues found`
        ));

        return items;
    }

    private getQuickActionItems(): AuraDashboardItem[] {
        const items: AuraDashboardItem[] = [];

        // Analyze Current File
        items.push(new AuraDashboardItem(
            'Analyze File',
            vscode.TreeItemCollapsibleState.None,
            {
                command: 'aura.analyzeFile',
                title: 'Analyze Current File'
            },
            new vscode.ThemeIcon('search'),
            undefined,
            'Analyze the currently open file'
        ));

        // Analyze Project
        items.push(new AuraDashboardItem(
            'Analyze Project',
            vscode.TreeItemCollapsibleState.None,
            {
                command: 'aura.analyzeProject',
                title: 'Analyze Entire Project'
            },
            new vscode.ThemeIcon('project'),
            undefined,
            'Analyze the entire project codebase'
        ));

        // Generate Commit
        items.push(new AuraDashboardItem(
            'Generate Commit',
            vscode.TreeItemCollapsibleState.None,
            {
                command: 'aura.generateCommit',
                title: 'Generate Semantic Commit'
            },
            new vscode.ThemeIcon('git-commit'),
            undefined,
            'Generate a semantic commit message'
        ));

        // Ask Question
        items.push(new AuraDashboardItem(
            'Ask Aura',
            vscode.TreeItemCollapsibleState.None,
            {
                command: 'aura.askQuestion',
                title: 'Ask Aura a Question'
            },
            new vscode.ThemeIcon('comment-discussion'),
            undefined,
            'Ask Aura a question about your code'
        ));

        // Toggle Auto-Analysis
        items.push(new AuraDashboardItem(
            'Auto-Analysis',
            vscode.TreeItemCollapsibleState.None,
            {
                command: 'aura.toggleAutoAnalysis',
                title: 'Toggle Auto-Analysis'
            },
            new vscode.ThemeIcon('settings-gear'),
            undefined,
            'Toggle automatic code analysis on save'
        ));

        return items;
    }
}