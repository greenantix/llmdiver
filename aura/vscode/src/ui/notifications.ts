/**
 * Aura Notification Manager
 * =========================
 * 
 * Manages notifications and user feedback in VS Code.
 * Provides contextual alerts, progress indicators, and status updates.
 */

import * as vscode from 'vscode';

export class AuraNotificationManager {
    private enabled: boolean;

    constructor(enabled: boolean = true) {
        this.enabled = enabled;
    }

    public setEnabled(enabled: boolean): void {
        this.enabled = enabled;
    }

    public showInfo(message: string, ...actions: string[]): Thenable<string | undefined> {
        if (!this.enabled) return Promise.resolve(undefined);
        return vscode.window.showInformationMessage(`🤖 Aura: ${message}`, ...actions);
    }

    public showWarning(message: string, ...actions: string[]): Thenable<string | undefined> {
        if (!this.enabled) return Promise.resolve(undefined);
        return vscode.window.showWarningMessage(`⚠️ Aura: ${message}`, ...actions);
    }

    public showError(message: string, ...actions: string[]): Thenable<string | undefined> {
        return vscode.window.showErrorMessage(`❌ Aura: ${message}`, ...actions);
    }

    public showProgress<T>(
        title: string,
        task: (progress: vscode.Progress<{ message?: string; increment?: number }>, token: vscode.CancellationToken) => Thenable<T>
    ): Thenable<T> {
        return vscode.window.withProgress(
            {
                location: vscode.ProgressLocation.Notification,
                title: `🤖 Aura: ${title}`,
                cancellable: true
            },
            task
        );
    }

    public async showAnalysisComplete(
        fileName: string,
        elementsFound: number,
        issuesFound: number
    ): Promise<void> {
        if (!this.enabled) return;

        const message = `Analysis complete for ${fileName}: ${elementsFound} elements, ${issuesFound} issues found`;
        
        if (issuesFound > 0) {
            const action = await this.showWarning(message, 'View Issues', 'Dismiss');
            if (action === 'View Issues') {
                vscode.commands.executeCommand('aura.codeAnalysis.focus');
            }
        } else {
            this.showInfo(message);
        }
    }

    public async showCommitGenerated(commitMessage: string): Promise<boolean> {
        const action = await this.showInfo(
            'Semantic commit message generated',
            'View & Edit',
            'Auto-Commit',
            'Dismiss'
        );

        switch (action) {
            case 'View & Edit':
                const edited = await vscode.window.showInputBox({
                    prompt: 'Review and edit commit message',
                    value: commitMessage,
                    placeHolder: 'Commit message'
                });
                if (edited) {
                    await this.executeCommit(edited);
                    return true;
                }
                break;
            case 'Auto-Commit':
                await this.executeCommit(commitMessage);
                return true;
        }

        return false;
    }

    private async executeCommit(message: string): Promise<void> {
        const terminal = vscode.window.createTerminal('Aura Git');
        terminal.sendText(`git commit -m "${message}"`);
        terminal.show();
        this.showInfo('Commit executed successfully');
    }

    public async showConnectionStatus(status: 'connected' | 'disconnected' | 'error'): Promise<void> {
        switch (status) {
            case 'connected':
                if (this.enabled) {
                    this.showInfo('Connected and ready to assist');
                }
                break;
            case 'disconnected':
                const reconnectAction = await this.showWarning(
                    'Disconnected from Aura system',
                    'Reconnect',
                    'Check Settings'
                );
                if (reconnectAction === 'Reconnect') {
                    vscode.commands.executeCommand('aura.reconnect');
                } else if (reconnectAction === 'Check Settings') {
                    vscode.commands.executeCommand('workbench.action.openSettings', 'aura');
                }
                break;
            case 'error':
                const troubleshootAction = await this.showError(
                    'Connection error - please check Aura system status',
                    'Troubleshoot',
                    'Settings'
                );
                if (troubleshootAction === 'Troubleshoot') {
                    vscode.commands.executeCommand('aura.showTroubleshooting');
                } else if (troubleshootAction === 'Settings') {
                    vscode.commands.executeCommand('workbench.action.openSettings', 'aura');
                }
                break;
        }
    }

    public async showFirstTimeWelcome(): Promise<void> {
        const action = await vscode.window.showInformationMessage(
            '🤖 Welcome to Aura - Level 9 Autonomous AI Coding Assistant! ' +
            'I\'m here to help you write better code faster.',
            'Take Tour',
            'Open Dashboard',
            'Settings'
        );

        switch (action) {
            case 'Take Tour':
                vscode.commands.executeCommand('aura.showTour');
                break;
            case 'Open Dashboard':
                vscode.commands.executeCommand('aura.showDashboard');
                break;
            case 'Settings':
                vscode.commands.executeCommand('workbench.action.openSettings', 'aura');
                break;
        }
    }

    public async showQuickSuggestion(
        message: string,
        primaryAction: string,
        command: string
    ): Promise<void> {
        if (!this.enabled) return;

        const action = await vscode.window.showInformationMessage(
            `💡 Aura suggests: ${message}`,
            primaryAction,
            'Later'
        );

        if (action === primaryAction) {
            vscode.commands.executeCommand(command);
        }
    }

    public showStatusBarMessage(message: string, timeout: number = 5000): vscode.Disposable {
        return vscode.window.setStatusBarMessage(`🤖 ${message}`, timeout);
    }
}