/**
 * Aura Status Bar Manager
 * =======================
 * 
 * Manages the VS Code status bar integration for Aura.
 * Shows connection status, activity indicators, and quick actions.
 */

import * as vscode from 'vscode';
import { ConnectionStatus } from '../connection';

export class AuraStatusBar {
    private statusBarItem: vscode.StatusBarItem;
    private activityItem: vscode.StatusBarItem;

    constructor() {
        // Main status item
        this.statusBarItem = vscode.window.createStatusBarItem(
            vscode.StatusBarAlignment.Left,
            100
        );
        this.statusBarItem.text = '$(robot) Aura';
        this.statusBarItem.tooltip = 'Aura - Autonomous AI Coding Assistant';
        this.statusBarItem.command = 'aura.showDashboard';

        // Activity indicator
        this.activityItem = vscode.window.createStatusBarItem(
            vscode.StatusBarAlignment.Left,
            99
        );
    }

    public show(): void {
        this.statusBarItem.show();
    }

    public hide(): void {
        this.statusBarItem.hide();
        this.activityItem.hide();
    }

    public updateConnectionStatus(status: ConnectionStatus): void {
        switch (status) {
            case 'connected':
                this.statusBarItem.text = '$(robot) Aura';
                this.statusBarItem.color = new vscode.ThemeColor('aura.primary');
                this.statusBarItem.tooltip = 'Aura - Connected and Ready';
                break;
            case 'connecting':
                this.statusBarItem.text = '$(sync~spin) Aura';
                this.statusBarItem.color = new vscode.ThemeColor('editorWarning.foreground');
                this.statusBarItem.tooltip = 'Aura - Connecting...';
                break;
            case 'disconnected':
                this.statusBarItem.text = '$(robot) Aura';
                this.statusBarItem.color = new vscode.ThemeColor('editorError.foreground');
                this.statusBarItem.tooltip = 'Aura - Disconnected';
                break;
            case 'error':
                this.statusBarItem.text = '$(error) Aura';
                this.statusBarItem.color = new vscode.ThemeColor('editorError.foreground');
                this.statusBarItem.tooltip = 'Aura - Connection Error';
                break;
        }
    }

    public showActivity(message: string): void {
        this.activityItem.text = `$(sync~spin) ${message}`;
        this.activityItem.color = new vscode.ThemeColor('aura.primary');
        this.activityItem.show();
    }

    public hideActivity(): void {
        this.activityItem.hide();
    }

    public dispose(): void {
        this.statusBarItem.dispose();
        this.activityItem.dispose();
    }
}