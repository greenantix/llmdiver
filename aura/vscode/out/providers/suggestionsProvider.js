"use strict";
/**
 * Aura Suggestions Provider
 * =========================
 *
 * Provides intelligent suggestions and recommendations in VS Code sidebar.
 * Shows code improvements, refactoring opportunities, and best practices.
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
exports.AuraSuggestionsProvider = exports.SuggestionItem = void 0;
const vscode = __importStar(require("vscode"));
class SuggestionItem extends vscode.TreeItem {
    constructor(suggestion, collapsibleState) {
        super(suggestion.title, collapsibleState);
        this.suggestion = suggestion;
        this.collapsibleState = collapsibleState;
        this.description = this.getPriorityLabel(suggestion.priority);
        this.tooltip = suggestion.description;
        this.iconPath = this.getIconForCategory(suggestion.category);
        this.contextValue = 'suggestion';
        if (suggestion.file && suggestion.line) {
            this.command = {
                command: 'vscode.open',
                title: 'Go to suggestion',
                arguments: [
                    vscode.Uri.file(suggestion.file),
                    { selection: new vscode.Range(suggestion.line - 1, 0, suggestion.line - 1, 0) }
                ]
            };
        }
    }
    getPriorityLabel(priority) {
        switch (priority) {
            case 'high': return '🔴 High';
            case 'medium': return '🟡 Medium';
            case 'low': return '🟢 Low';
            default: return '';
        }
    }
    getIconForCategory(category) {
        switch (category) {
            case 'refactor': return new vscode.ThemeIcon('code');
            case 'performance': return new vscode.ThemeIcon('rocket');
            case 'style': return new vscode.ThemeIcon('paintcan');
            case 'documentation': return new vscode.ThemeIcon('book');
            case 'testing': return new vscode.ThemeIcon('beaker');
            case 'security': return new vscode.ThemeIcon('shield');
            default: return new vscode.ThemeIcon('lightbulb');
        }
    }
}
exports.SuggestionItem = SuggestionItem;
class AuraSuggestionsProvider {
    constructor(connection) {
        this.connection = connection;
        this._onDidChangeTreeData = new vscode.EventEmitter();
        this.onDidChangeTreeData = this._onDidChangeTreeData.event;
        this.suggestions = [];
        this.loadDefaultSuggestions();
    }
    refresh() {
        this._onDidChangeTreeData.fire();
    }
    updateSuggestions(suggestions) {
        // Convert string suggestions to Suggestion objects
        const newSuggestions = suggestions.map((suggestion, index) => ({
            id: `suggestion_${index}`,
            title: this.extractTitle(suggestion),
            description: suggestion,
            category: this.categorizeByContent(suggestion),
            priority: this.prioritizeByContent(suggestion)
        }));
        this.suggestions = [...this.getDefaultSuggestions(), ...newSuggestions];
        this.refresh();
    }
    getTreeItem(element) {
        return element;
    }
    getChildren(element) {
        if (!element) {
            return Promise.resolve(this.getRootItems());
        }
        return Promise.resolve([]);
    }
    getRootItems() {
        if (this.suggestions.length === 0) {
            return [new SuggestionItem({
                    id: 'no_suggestions',
                    title: 'No suggestions available',
                    description: 'Analyze a file to get personalized suggestions',
                    category: 'style',
                    priority: 'low'
                }, vscode.TreeItemCollapsibleState.None)];
        }
        // Sort suggestions by priority
        const sortedSuggestions = this.suggestions.sort((a, b) => {
            const priorityOrder = { high: 3, medium: 2, low: 1 };
            return priorityOrder[b.priority] - priorityOrder[a.priority];
        });
        return sortedSuggestions.map(suggestion => new SuggestionItem(suggestion, vscode.TreeItemCollapsibleState.None));
    }
    loadDefaultSuggestions() {
        this.suggestions = this.getDefaultSuggestions();
    }
    getDefaultSuggestions() {
        return [
            {
                id: 'analyze_project',
                title: 'Analyze Project',
                description: 'Run a comprehensive analysis of your entire project to discover improvement opportunities',
                category: 'refactor',
                priority: 'medium',
                action: 'aura.analyzeProject'
            },
            {
                id: 'generate_commit',
                title: 'Generate Semantic Commit',
                description: 'Create a well-formatted commit message based on your current changes',
                category: 'style',
                priority: 'low',
                action: 'aura.generateCommit'
            },
            {
                id: 'enable_auto_analysis',
                title: 'Enable Auto-Analysis',
                description: 'Automatically analyze files when you save them for real-time feedback',
                category: 'performance',
                priority: 'medium',
                action: 'aura.toggleAutoAnalysis'
            }
        ];
    }
    extractTitle(suggestion) {
        // Extract a concise title from the suggestion text
        const sentences = suggestion.split('.').filter(s => s.trim());
        if (sentences.length > 0) {
            let title = sentences[0].trim();
            if (title.length > 50) {
                title = title.substring(0, 47) + '...';
            }
            return title;
        }
        return suggestion.length > 50 ? suggestion.substring(0, 47) + '...' : suggestion;
    }
    categorizeByContent(suggestion) {
        const lowerSuggestion = suggestion.toLowerCase();
        if (lowerSuggestion.includes('docstring') || lowerSuggestion.includes('documentation')) {
            return 'documentation';
        }
        if (lowerSuggestion.includes('test') || lowerSuggestion.includes('testing')) {
            return 'testing';
        }
        if (lowerSuggestion.includes('performance') || lowerSuggestion.includes('optimize')) {
            return 'performance';
        }
        if (lowerSuggestion.includes('refactor') || lowerSuggestion.includes('complexity')) {
            return 'refactor';
        }
        if (lowerSuggestion.includes('security') || lowerSuggestion.includes('vulnerability')) {
            return 'security';
        }
        return 'style';
    }
    prioritizeByContent(suggestion) {
        const lowerSuggestion = suggestion.toLowerCase();
        if (lowerSuggestion.includes('error') || lowerSuggestion.includes('security') || lowerSuggestion.includes('vulnerability')) {
            return 'high';
        }
        if (lowerSuggestion.includes('performance') || lowerSuggestion.includes('complexity') || lowerSuggestion.includes('refactor')) {
            return 'medium';
        }
        return 'low';
    }
    applySuggestion(suggestion) {
        if (suggestion.action) {
            vscode.commands.executeCommand(suggestion.action);
        }
        else if (suggestion.file && suggestion.line) {
            vscode.commands.executeCommand('vscode.open', vscode.Uri.file(suggestion.file), { selection: new vscode.Range(suggestion.line - 1, 0, suggestion.line - 1, 0) });
        }
    }
    dismissSuggestion(suggestion) {
        this.suggestions = this.suggestions.filter(s => s.id !== suggestion.id);
        this.refresh();
    }
}
exports.AuraSuggestionsProvider = AuraSuggestionsProvider;
//# sourceMappingURL=suggestionsProvider.js.map