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
export declare class SuggestionItem extends vscode.TreeItem {
    readonly suggestion: Suggestion;
    readonly collapsibleState: vscode.TreeItemCollapsibleState;
    constructor(suggestion: Suggestion, collapsibleState: vscode.TreeItemCollapsibleState);
    private getPriorityLabel;
    private getIconForCategory;
}
export declare class AuraSuggestionsProvider implements vscode.TreeDataProvider<SuggestionItem> {
    private connection;
    private _onDidChangeTreeData;
    readonly onDidChangeTreeData: vscode.Event<SuggestionItem | undefined | null | void>;
    private suggestions;
    constructor(connection: AuraConnection);
    refresh(): void;
    updateSuggestions(suggestions: string[]): void;
    getTreeItem(element: SuggestionItem): vscode.TreeItem;
    getChildren(element?: SuggestionItem): Thenable<SuggestionItem[]>;
    private getRootItems;
    private loadDefaultSuggestions;
    private getDefaultSuggestions;
    private extractTitle;
    private categorizeByContent;
    private prioritizeByContent;
    applySuggestion(suggestion: Suggestion): void;
    dismissSuggestion(suggestion: Suggestion): void;
}
//# sourceMappingURL=suggestionsProvider.d.ts.map