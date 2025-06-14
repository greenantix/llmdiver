/**
 * Aura Dashboard Provider
 * =======================
 *
 * Provides the main dashboard view in VS Code sidebar.
 * Shows system status, project metrics, and quick actions.
 */
import * as vscode from 'vscode';
import { AuraConnection, ProjectAnalysis } from '../connection';
export declare class AuraDashboardItem extends vscode.TreeItem {
    readonly label: string;
    readonly collapsibleState: vscode.TreeItemCollapsibleState;
    readonly command?: vscode.Command | undefined;
    readonly iconPath?: vscode.ThemeIcon | undefined;
    readonly description?: string | undefined;
    readonly tooltip?: string | undefined;
    readonly contextValue?: string | undefined;
    constructor(label: string, collapsibleState: vscode.TreeItemCollapsibleState, command?: vscode.Command | undefined, iconPath?: vscode.ThemeIcon | undefined, description?: string | undefined, tooltip?: string | undefined, contextValue?: string | undefined);
}
export declare class AuraDashboardProvider implements vscode.TreeDataProvider<AuraDashboardItem> {
    private connection;
    private _onDidChangeTreeData;
    readonly onDidChangeTreeData: vscode.Event<AuraDashboardItem | undefined | null | void>;
    private projectAnalysis;
    constructor(connection: AuraConnection);
    refresh(): void;
    updateProjectAnalysis(analysis: ProjectAnalysis): void;
    getTreeItem(element: AuraDashboardItem): vscode.TreeItem;
    getChildren(element?: AuraDashboardItem): Thenable<AuraDashboardItem[]>;
    private getRootItems;
    private getSystemStatusItems;
    private getProjectMetricsItems;
    private getQuickActionItems;
}
//# sourceMappingURL=dashboardProvider.d.ts.map