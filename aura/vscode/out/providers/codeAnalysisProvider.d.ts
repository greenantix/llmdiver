/**
 * Aura Code Analysis Provider
 * ===========================
 *
 * Provides code analysis view in VS Code sidebar.
 * Shows analysis results, code metrics, and detected issues.
 */
import * as vscode from 'vscode';
import { AuraConnection, FileAnalysis } from '../connection';
export declare class CodeAnalysisItem extends vscode.TreeItem {
    readonly label: string;
    readonly collapsibleState: vscode.TreeItemCollapsibleState;
    readonly command?: vscode.Command | undefined;
    readonly iconPath?: vscode.ThemeIcon | undefined;
    readonly description?: string | undefined;
    readonly tooltip?: string | undefined;
    readonly contextValue?: string | undefined;
    constructor(label: string, collapsibleState: vscode.TreeItemCollapsibleState, command?: vscode.Command | undefined, iconPath?: vscode.ThemeIcon | undefined, description?: string | undefined, tooltip?: string | undefined, contextValue?: string | undefined);
}
export declare class AuraCodeAnalysisProvider implements vscode.TreeDataProvider<CodeAnalysisItem> {
    private connection;
    private _onDidChangeTreeData;
    readonly onDidChangeTreeData: vscode.Event<CodeAnalysisItem | undefined | null | void>;
    private currentFile;
    private fileAnalysis;
    constructor(connection: AuraConnection);
    refresh(): void;
    setActiveFile(filePath: string): void;
    updateAnalysis(filePath: string, analysis: FileAnalysis): void;
    getTreeItem(element: CodeAnalysisItem): vscode.TreeItem;
    getChildren(element?: CodeAnalysisItem): Thenable<CodeAnalysisItem[]>;
    private getRootItems;
    private getFileInfoItems;
    private getCodeElementItems;
    private getIssueItems;
    private getMetricItems;
    private getIconForElementType;
    private getIconForSeverity;
}
//# sourceMappingURL=codeAnalysisProvider.d.ts.map