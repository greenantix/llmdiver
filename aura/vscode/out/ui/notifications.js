"use strict";
/**
 * Aura Notification Manager
 * =========================
 *
 * Manages notifications and user feedback in VS Code.
 * Provides contextual alerts, progress indicators, and status updates.
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
exports.AuraNotificationManager = void 0;
const vscode = __importStar(require("vscode"));
class AuraNotificationManager {
    constructor(enabled = true) {
        this.enabled = enabled;
    }
    setEnabled(enabled) {
        this.enabled = enabled;
    }
    showInfo(message, ...actions) {
        if (!this.enabled)
            return Promise.resolve(undefined);
        return vscode.window.showInformationMessage(`🤖 Aura: ${message}`, ...actions);
    }
    showWarning(message, ...actions) {
        if (!this.enabled)
            return Promise.resolve(undefined);
        return vscode.window.showWarningMessage(`⚠️ Aura: ${message}`, ...actions);
    }
    showError(message, ...actions) {
        return vscode.window.showErrorMessage(`❌ Aura: ${message}`, ...actions);
    }
    showProgress(title, task) {
        return vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: `🤖 Aura: ${title}`,
            cancellable: true
        }, task);
    }
    async showAnalysisComplete(fileName, elementsFound, issuesFound) {
        if (!this.enabled)
            return;
        const message = `Analysis complete for ${fileName}: ${elementsFound} elements, ${issuesFound} issues found`;
        if (issuesFound > 0) {
            const action = await this.showWarning(message, 'View Issues', 'Dismiss');
            if (action === 'View Issues') {
                vscode.commands.executeCommand('aura.codeAnalysis.focus');
            }
        }
        else {
            this.showInfo(message);
        }
    }
    async showCommitGenerated(commitMessage) {
        const action = await this.showInfo('Semantic commit message generated', 'View & Edit', 'Auto-Commit', 'Dismiss');
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
    async executeCommit(message) {
        const terminal = vscode.window.createTerminal('Aura Git');
        terminal.sendText(`git commit -m "${message}"`);
        terminal.show();
        this.showInfo('Commit executed successfully');
    }
    async showConnectionStatus(status) {
        switch (status) {
            case 'connected':
                if (this.enabled) {
                    this.showInfo('Connected and ready to assist');
                }
                break;
            case 'disconnected':
                const reconnectAction = await this.showWarning('Disconnected from Aura system', 'Reconnect', 'Check Settings');
                if (reconnectAction === 'Reconnect') {
                    vscode.commands.executeCommand('aura.reconnect');
                }
                else if (reconnectAction === 'Check Settings') {
                    vscode.commands.executeCommand('workbench.action.openSettings', 'aura');
                }
                break;
            case 'error':
                const troubleshootAction = await this.showError('Connection error - please check Aura system status', 'Troubleshoot', 'Settings');
                if (troubleshootAction === 'Troubleshoot') {
                    vscode.commands.executeCommand('aura.showTroubleshooting');
                }
                else if (troubleshootAction === 'Settings') {
                    vscode.commands.executeCommand('workbench.action.openSettings', 'aura');
                }
                break;
        }
    }
    async showFirstTimeWelcome() {
        const action = await vscode.window.showInformationMessage('🤖 Welcome to Aura - Level 9 Autonomous AI Coding Assistant! ' +
            'I\'m here to help you write better code faster.', 'Take Tour', 'Open Dashboard', 'Settings');
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
    async showQuickSuggestion(message, primaryAction, command) {
        if (!this.enabled)
            return;
        const action = await vscode.window.showInformationMessage(`💡 Aura suggests: ${message}`, primaryAction, 'Later');
        if (action === primaryAction) {
            vscode.commands.executeCommand(command);
        }
    }
    showStatusBarMessage(message, timeout = 5000) {
        return vscode.window.setStatusBarMessage(`🤖 ${message}`, timeout);
    }
}
exports.AuraNotificationManager = AuraNotificationManager;
//# sourceMappingURL=notifications.js.map