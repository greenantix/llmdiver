/**
 * Aura Notification Manager
 * =========================
 *
 * Manages notifications and user feedback in VS Code.
 * Provides contextual alerts, progress indicators, and status updates.
 */
import * as vscode from 'vscode';
export declare class AuraNotificationManager {
    private enabled;
    constructor(enabled?: boolean);
    setEnabled(enabled: boolean): void;
    showInfo(message: string, ...actions: string[]): Thenable<string | undefined>;
    showWarning(message: string, ...actions: string[]): Thenable<string | undefined>;
    showError(message: string, ...actions: string[]): Thenable<string | undefined>;
    showProgress<T>(title: string, task: (progress: vscode.Progress<{
        message?: string;
        increment?: number;
    }>, token: vscode.CancellationToken) => Thenable<T>): Thenable<T>;
    showAnalysisComplete(fileName: string, elementsFound: number, issuesFound: number): Promise<void>;
    showCommitGenerated(commitMessage: string): Promise<boolean>;
    private executeCommit;
    showConnectionStatus(status: 'connected' | 'disconnected' | 'error'): Promise<void>;
    showFirstTimeWelcome(): Promise<void>;
    showQuickSuggestion(message: string, primaryAction: string, command: string): Promise<void>;
    showStatusBarMessage(message: string, timeout?: number): vscode.Disposable;
}
//# sourceMappingURL=notifications.d.ts.map