/**
 * Aura Suggestions Provider
 * =========================
 * 
 * Provides intelligent suggestions and recommendations in VS Code sidebar.
 * Shows code improvements, refactoring opportunities, and best practices.
 */

import * as vscode from 'vscode';
import { AuraConnection } from '../connection';

export interface Suggestion {
    id: string;
    title: string;
    description: string;
    category: 'refactor' | 'performance' | 'style' | 'documentation' | 'testing' | 'security';
    priority: 'low' | 'medium' | 'high';
    file?: string;
    line?: number;
    action?: string;
}

export class SuggestionItem extends vscode.TreeItem {
    constructor(
        public readonly suggestion: Suggestion,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState
    ) {
        super(suggestion.title, collapsibleState);
        
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

    private getPriorityLabel(priority: string): string {
        switch (priority) {
            case 'high': return '🔴 High';
            case 'medium': return '🟡 Medium';
            case 'low': return '🟢 Low';
            default: return '';
        }
    }

    private getIconForCategory(category: string): vscode.ThemeIcon {
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

export class AuraSuggestionsProvider implements vscode.TreeDataProvider<SuggestionItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<SuggestionItem | undefined | null | void> = new vscode.EventEmitter<SuggestionItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<SuggestionItem | undefined | null | void> = this._onDidChangeTreeData.event;

    private suggestions: Suggestion[] = [];

    constructor(private connection: AuraConnection) {
        this.loadDefaultSuggestions();
    }

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    updateSuggestions(suggestions: string[]): void {
        // Convert string suggestions to Suggestion objects
        const newSuggestions: Suggestion[] = suggestions.map((suggestion, index) => ({
            id: `suggestion_${index}`,
            title: this.extractTitle(suggestion),
            description: suggestion,
            category: this.categorizeByContent(suggestion),
            priority: this.prioritizeByContent(suggestion)
        }));

        this.suggestions = [...this.getDefaultSuggestions(), ...newSuggestions];
        this.refresh();
    }

    getTreeItem(element: SuggestionItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: SuggestionItem): Thenable<SuggestionItem[]> {
        if (!element) {
            return Promise.resolve(this.getRootItems());
        }
        return Promise.resolve([]);
    }

    private getRootItems(): SuggestionItem[] {
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

        return sortedSuggestions.map(suggestion => 
            new SuggestionItem(suggestion, vscode.TreeItemCollapsibleState.None)
        );
    }

    private loadDefaultSuggestions(): void {
        this.suggestions = this.getDefaultSuggestions();
    }

    private getDefaultSuggestions(): Suggestion[] {
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

    private extractTitle(suggestion: string): string {
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

    private categorizeByContent(suggestion: string): Suggestion['category'] {
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

    private prioritizeByContent(suggestion: string): Suggestion['priority'] {
        const lowerSuggestion = suggestion.toLowerCase();
        
        if (lowerSuggestion.includes('error') || lowerSuggestion.includes('security') || lowerSuggestion.includes('vulnerability')) {
            return 'high';
        }
        if (lowerSuggestion.includes('performance') || lowerSuggestion.includes('complexity') || lowerSuggestion.includes('refactor')) {
            return 'medium';
        }
        
        return 'low';
    }

    public applySuggestion(suggestion: Suggestion): void {
        if (suggestion.action) {
            vscode.commands.executeCommand(suggestion.action);
        } else if (suggestion.file && suggestion.line) {
            vscode.commands.executeCommand('vscode.open', 
                vscode.Uri.file(suggestion.file),
                { selection: new vscode.Range(suggestion.line - 1, 0, suggestion.line - 1, 0) }
            );
        }
    }

    public dismissSuggestion(suggestion: Suggestion): void {
        this.suggestions = this.suggestions.filter(s => s.id !== suggestion.id);
        this.refresh();
    }
}