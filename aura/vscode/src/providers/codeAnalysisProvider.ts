/**
 * Aura Code Analysis Provider
 * ===========================
 * 
 * Provides code analysis view in VS Code sidebar.
 * Shows analysis results, code metrics, and detected issues.
 */

import * as vscode from 'vscode';
import { AuraConnection, FileAnalysis } from '../connection';

export class CodeAnalysisItem extends vscode.TreeItem {
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
    }
}

export class AuraCodeAnalysisProvider implements vscode.TreeDataProvider<CodeAnalysisItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<CodeAnalysisItem | undefined | null | void> = new vscode.EventEmitter<CodeAnalysisItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<CodeAnalysisItem | undefined | null | void> = this._onDidChangeTreeData.event;

    private currentFile: string | null = null;
    private fileAnalysis: FileAnalysis | null = null;

    constructor(private connection: AuraConnection) {}

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    setActiveFile(filePath: string): void {
        this.currentFile = filePath;
        this.refresh();
    }

    updateAnalysis(filePath: string, analysis: FileAnalysis): void {
        if (filePath === this.currentFile) {
            this.fileAnalysis = analysis;
            this.refresh();
        }
    }

    getTreeItem(element: CodeAnalysisItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: CodeAnalysisItem): Thenable<CodeAnalysisItem[]> {
        if (!element) {
            return Promise.resolve(this.getRootItems());
        }

        switch (element.contextValue) {
            case 'fileInfo':
                return Promise.resolve(this.getFileInfoItems());
            case 'codeElements':
                return Promise.resolve(this.getCodeElementItems());
            case 'issues':
                return Promise.resolve(this.getIssueItems());
            case 'metrics':
                return Promise.resolve(this.getMetricItems());
            default:
                return Promise.resolve([]);
        }
    }

    private getRootItems(): CodeAnalysisItem[] {
        const items: CodeAnalysisItem[] = [];

        if (!this.currentFile) {
            items.push(new CodeAnalysisItem(
                'No file selected',
                vscode.TreeItemCollapsibleState.None,
                undefined,
                new vscode.ThemeIcon('info'),
                undefined,
                'Open a Python or JavaScript file to see analysis'
            ));
            return items;
        }

        // File Info Section
        items.push(new CodeAnalysisItem(
            'File Information',
            vscode.TreeItemCollapsibleState.Expanded,
            undefined,
            new vscode.ThemeIcon('file-code'),
            undefined,
            'Basic file information and status',
            'fileInfo'
        ));

        if (this.fileAnalysis) {
            // Code Elements Section
            if (this.fileAnalysis.elements.length > 0) {
                items.push(new CodeAnalysisItem(
                    'Code Elements',
                    vscode.TreeItemCollapsibleState.Collapsed,
                    undefined,
                    new vscode.ThemeIcon('symbol-class'),
                    `${this.fileAnalysis.elements.length}`,
                    'Functions, classes, and other code elements',
                    'codeElements'
                ));
            }

            // Issues Section
            if (this.fileAnalysis.issues.length > 0) {
                items.push(new CodeAnalysisItem(
                    'Issues',
                    vscode.TreeItemCollapsibleState.Expanded,
                    undefined,
                    new vscode.ThemeIcon('warning'),
                    `${this.fileAnalysis.issues.length}`,
                    'Detected issues and warnings',
                    'issues'
                ));
            }

            // Metrics Section
            items.push(new CodeAnalysisItem(
                'Metrics',
                vscode.TreeItemCollapsibleState.Collapsed,
                undefined,
                new vscode.ThemeIcon('graph'),
                undefined,
                'Code quality metrics and statistics',
                'metrics'
            ));
        } else {
            items.push(new CodeAnalysisItem(
                'Not analyzed',
                vscode.TreeItemCollapsibleState.None,
                {
                    command: 'aura.analyzeFile',
                    title: 'Analyze File'
                },
                new vscode.ThemeIcon('search'),
                undefined,
                'Click to analyze this file'
            ));
        }

        return items;
    }

    private getFileInfoItems(): CodeAnalysisItem[] {
        const items: CodeAnalysisItem[] = [];

        if (this.currentFile) {
            const fileName = this.currentFile.split('/').pop() || 'Unknown';
            const fileExtension = fileName.split('.').pop()?.toUpperCase() || 'Unknown';

            items.push(new CodeAnalysisItem(
                'Name',
                vscode.TreeItemCollapsibleState.None,
                undefined,
                new vscode.ThemeIcon('file'),
                fileName,
                `File name: ${fileName}`
            ));

            items.push(new CodeAnalysisItem(
                'Type',
                vscode.TreeItemCollapsibleState.None,
                undefined,
                new vscode.ThemeIcon('symbol-keyword'),
                fileExtension,
                `File type: ${fileExtension}`
            ));

            if (this.fileAnalysis) {
                const analysisTime = new Date(this.fileAnalysis.timestamp || Date.now()).toLocaleTimeString();
                items.push(new CodeAnalysisItem(
                    'Last Analysis',
                    vscode.TreeItemCollapsibleState.None,
                    undefined,
                    new vscode.ThemeIcon('clock'),
                    analysisTime,
                    `Last analyzed at ${analysisTime}`
                ));
            }
        }

        return items;
    }

    private getCodeElementItems(): CodeAnalysisItem[] {
        if (!this.fileAnalysis) return [];

        const items: CodeAnalysisItem[] = [];
        const elements = this.fileAnalysis.elements;

        // Group elements by type
        const elementsByType = elements.reduce((acc, element) => {
            if (!acc[element.type]) acc[element.type] = [];
            acc[element.type].push(element);
            return acc;
        }, {} as Record<string, any[]>);

        for (const [type, typeElements] of Object.entries(elementsByType)) {
            const typeIcon = this.getIconForElementType(type);
            
            typeElements.forEach(element => {
                const complexityDesc = element.complexity > 0 ? ` (${element.complexity})` : '';
                const hasDocstring = element.docstring ? '📖' : '';
                
                items.push(new CodeAnalysisItem(
                    element.name,
                    vscode.TreeItemCollapsibleState.None,
                    {
                        command: 'vscode.open',
                        title: 'Go to definition',
                        arguments: [
                            vscode.Uri.file(this.currentFile!),
                            { selection: new vscode.Range(element.line_number - 1, 0, element.line_number - 1, 0) }
                        ]
                    },
                    new vscode.ThemeIcon(typeIcon),
                    `${type}${complexityDesc} ${hasDocstring}`,
                    `${type} at line ${element.line_number}${element.docstring ? ' (documented)' : ''}`
                ));
            });
        }

        return items;
    }

    private getIssueItems(): CodeAnalysisItem[] {
        if (!this.fileAnalysis) return [];

        const items: CodeAnalysisItem[] = [];
        
        this.fileAnalysis.issues.forEach(issue => {
            const severityIcon = this.getIconForSeverity(issue.severity);
            
            items.push(new CodeAnalysisItem(
                issue.message,
                vscode.TreeItemCollapsibleState.None,
                {
                    command: 'vscode.open',
                    title: 'Go to issue',
                    arguments: [
                        vscode.Uri.file(this.currentFile!),
                        { selection: new vscode.Range(issue.line - 1, 0, issue.line - 1, 0) }
                    ]
                },
                new vscode.ThemeIcon(severityIcon),
                `Line ${issue.line}`,
                `${issue.severity}: ${issue.message} (line ${issue.line})`
            ));
        });

        return items;
    }

    private getMetricItems(): CodeAnalysisItem[] {
        if (!this.fileAnalysis) return [];

        const items: CodeAnalysisItem[] = [];
        const metrics = this.fileAnalysis.metrics;

        items.push(new CodeAnalysisItem(
            'Lines of Code',
            vscode.TreeItemCollapsibleState.None,
            undefined,
            new vscode.ThemeIcon('file-text'),
            metrics.lines_of_code.toString(),
            `${metrics.lines_of_code} lines of code`
        ));

        items.push(new CodeAnalysisItem(
            'Functions',
            vscode.TreeItemCollapsibleState.None,
            undefined,
            new vscode.ThemeIcon('symbol-function'),
            metrics.functions_count.toString(),
            `${metrics.functions_count} functions`
        ));

        items.push(new CodeAnalysisItem(
            'Classes',
            vscode.TreeItemCollapsibleState.None,
            undefined,
            new vscode.ThemeIcon('symbol-class'),
            metrics.classes_count.toString(),
            `${metrics.classes_count} classes`
        ));

        return items;
    }

    private getIconForElementType(type: string): string {
        switch (type) {
            case 'function': return 'symbol-function';
            case 'class': return 'symbol-class';
            case 'variable': return 'symbol-variable';
            case 'constant': return 'symbol-constant';
            case 'import': return 'symbol-namespace';
            default: return 'symbol-misc';
        }
    }

    private getIconForSeverity(severity: string): string {
        switch (severity.toLowerCase()) {
            case 'error': return 'error';
            case 'warning': return 'warning';
            case 'info': return 'info';
            default: return 'lightbulb';
        }
    }
}