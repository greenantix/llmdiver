"use strict";
/**
 * Aura Code Analysis Provider
 * ===========================
 *
 * Provides code analysis view in VS Code sidebar.
 * Shows analysis results, code metrics, and detected issues.
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
exports.AuraCodeAnalysisProvider = exports.CodeAnalysisItem = void 0;
const vscode = __importStar(require("vscode"));
class CodeAnalysisItem extends vscode.TreeItem {
    constructor(label, collapsibleState, command, iconPath, description, tooltip, contextValue) {
        super(label, collapsibleState);
        this.label = label;
        this.collapsibleState = collapsibleState;
        this.command = command;
        this.iconPath = iconPath;
        this.description = description;
        this.tooltip = tooltip;
        this.contextValue = contextValue;
    }
}
exports.CodeAnalysisItem = CodeAnalysisItem;
class AuraCodeAnalysisProvider {
    constructor(connection) {
        this.connection = connection;
        this._onDidChangeTreeData = new vscode.EventEmitter();
        this.onDidChangeTreeData = this._onDidChangeTreeData.event;
        this.currentFile = null;
        this.fileAnalysis = null;
    }
    refresh() {
        this._onDidChangeTreeData.fire();
    }
    setActiveFile(filePath) {
        this.currentFile = filePath;
        this.refresh();
    }
    updateAnalysis(filePath, analysis) {
        if (filePath === this.currentFile) {
            this.fileAnalysis = analysis;
            this.refresh();
        }
    }
    getTreeItem(element) {
        return element;
    }
    getChildren(element) {
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
    getRootItems() {
        const items = [];
        if (!this.currentFile) {
            items.push(new CodeAnalysisItem('No file selected', vscode.TreeItemCollapsibleState.None, undefined, new vscode.ThemeIcon('info'), undefined, 'Open a Python or JavaScript file to see analysis'));
            return items;
        }
        // File Info Section
        items.push(new CodeAnalysisItem('File Information', vscode.TreeItemCollapsibleState.Expanded, undefined, new vscode.ThemeIcon('file-code'), undefined, 'Basic file information and status', 'fileInfo'));
        if (this.fileAnalysis) {
            // Code Elements Section
            if (this.fileAnalysis.elements.length > 0) {
                items.push(new CodeAnalysisItem('Code Elements', vscode.TreeItemCollapsibleState.Collapsed, undefined, new vscode.ThemeIcon('symbol-class'), `${this.fileAnalysis.elements.length}`, 'Functions, classes, and other code elements', 'codeElements'));
            }
            // Issues Section
            if (this.fileAnalysis.issues.length > 0) {
                items.push(new CodeAnalysisItem('Issues', vscode.TreeItemCollapsibleState.Expanded, undefined, new vscode.ThemeIcon('warning'), `${this.fileAnalysis.issues.length}`, 'Detected issues and warnings', 'issues'));
            }
            // Metrics Section
            items.push(new CodeAnalysisItem('Metrics', vscode.TreeItemCollapsibleState.Collapsed, undefined, new vscode.ThemeIcon('graph'), undefined, 'Code quality metrics and statistics', 'metrics'));
        }
        else {
            items.push(new CodeAnalysisItem('Not analyzed', vscode.TreeItemCollapsibleState.None, {
                command: 'aura.analyzeFile',
                title: 'Analyze File'
            }, new vscode.ThemeIcon('search'), undefined, 'Click to analyze this file'));
        }
        return items;
    }
    getFileInfoItems() {
        const items = [];
        if (this.currentFile) {
            const fileName = this.currentFile.split('/').pop() || 'Unknown';
            const fileExtension = fileName.split('.').pop()?.toUpperCase() || 'Unknown';
            items.push(new CodeAnalysisItem('Name', vscode.TreeItemCollapsibleState.None, undefined, new vscode.ThemeIcon('file'), fileName, `File name: ${fileName}`));
            items.push(new CodeAnalysisItem('Type', vscode.TreeItemCollapsibleState.None, undefined, new vscode.ThemeIcon('symbol-keyword'), fileExtension, `File type: ${fileExtension}`));
            if (this.fileAnalysis) {
                const analysisTime = new Date(this.fileAnalysis.timestamp || Date.now()).toLocaleTimeString();
                items.push(new CodeAnalysisItem('Last Analysis', vscode.TreeItemCollapsibleState.None, undefined, new vscode.ThemeIcon('clock'), analysisTime, `Last analyzed at ${analysisTime}`));
            }
        }
        return items;
    }
    getCodeElementItems() {
        if (!this.fileAnalysis)
            return [];
        const items = [];
        const elements = this.fileAnalysis.elements;
        // Group elements by type
        const elementsByType = elements.reduce((acc, element) => {
            if (!acc[element.type])
                acc[element.type] = [];
            acc[element.type].push(element);
            return acc;
        }, {});
        for (const [type, typeElements] of Object.entries(elementsByType)) {
            const typeIcon = this.getIconForElementType(type);
            typeElements.forEach(element => {
                const complexityDesc = element.complexity > 0 ? ` (${element.complexity})` : '';
                const hasDocstring = element.docstring ? '📖' : '';
                items.push(new CodeAnalysisItem(element.name, vscode.TreeItemCollapsibleState.None, {
                    command: 'vscode.open',
                    title: 'Go to definition',
                    arguments: [
                        vscode.Uri.file(this.currentFile),
                        { selection: new vscode.Range(element.line_number - 1, 0, element.line_number - 1, 0) }
                    ]
                }, new vscode.ThemeIcon(typeIcon), `${type}${complexityDesc} ${hasDocstring}`, `${type} at line ${element.line_number}${element.docstring ? ' (documented)' : ''}`));
            });
        }
        return items;
    }
    getIssueItems() {
        if (!this.fileAnalysis)
            return [];
        const items = [];
        this.fileAnalysis.issues.forEach(issue => {
            const severityIcon = this.getIconForSeverity(issue.severity);
            items.push(new CodeAnalysisItem(issue.message, vscode.TreeItemCollapsibleState.None, {
                command: 'vscode.open',
                title: 'Go to issue',
                arguments: [
                    vscode.Uri.file(this.currentFile),
                    { selection: new vscode.Range(issue.line - 1, 0, issue.line - 1, 0) }
                ]
            }, new vscode.ThemeIcon(severityIcon), `Line ${issue.line}`, `${issue.severity}: ${issue.message} (line ${issue.line})`));
        });
        return items;
    }
    getMetricItems() {
        if (!this.fileAnalysis)
            return [];
        const items = [];
        const metrics = this.fileAnalysis.metrics;
        items.push(new CodeAnalysisItem('Lines of Code', vscode.TreeItemCollapsibleState.None, undefined, new vscode.ThemeIcon('file-text'), metrics.lines_of_code.toString(), `${metrics.lines_of_code} lines of code`));
        items.push(new CodeAnalysisItem('Functions', vscode.TreeItemCollapsibleState.None, undefined, new vscode.ThemeIcon('symbol-function'), metrics.functions_count.toString(), `${metrics.functions_count} functions`));
        items.push(new CodeAnalysisItem('Classes', vscode.TreeItemCollapsibleState.None, undefined, new vscode.ThemeIcon('symbol-class'), metrics.classes_count.toString(), `${metrics.classes_count} classes`));
        return items;
    }
    getIconForElementType(type) {
        switch (type) {
            case 'function': return 'symbol-function';
            case 'class': return 'symbol-class';
            case 'variable': return 'symbol-variable';
            case 'constant': return 'symbol-constant';
            case 'import': return 'symbol-namespace';
            default: return 'symbol-misc';
        }
    }
    getIconForSeverity(severity) {
        switch (severity.toLowerCase()) {
            case 'error': return 'error';
            case 'warning': return 'warning';
            case 'info': return 'info';
            default: return 'lightbulb';
        }
    }
}
exports.AuraCodeAnalysisProvider = AuraCodeAnalysisProvider;
//# sourceMappingURL=codeAnalysisProvider.js.map