"use strict";
/**
 * Aura Status Bar Manager
 * =======================
 *
 * Manages the VS Code status bar integration for Aura.
 * Shows connection status, activity indicators, and quick actions.
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
exports.AuraStatusBar = void 0;
const vscode = __importStar(require("vscode"));
class AuraStatusBar {
    constructor() {
        // Main status item
        this.statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
        this.statusBarItem.text = '$(robot) Aura';
        this.statusBarItem.tooltip = 'Aura - Autonomous AI Coding Assistant';
        this.statusBarItem.command = 'aura.showDashboard';
        // Activity indicator
        this.activityItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 99);
    }
    show() {
        this.statusBarItem.show();
    }
    hide() {
        this.statusBarItem.hide();
        this.activityItem.hide();
    }
    updateConnectionStatus(status) {
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
    showActivity(message) {
        this.activityItem.text = `$(sync~spin) ${message}`;
        this.activityItem.color = new vscode.ThemeColor('aura.primary');
        this.activityItem.show();
    }
    hideActivity() {
        this.activityItem.hide();
    }
    dispose() {
        this.statusBarItem.dispose();
        this.activityItem.dispose();
    }
}
exports.AuraStatusBar = AuraStatusBar;
//# sourceMappingURL=statusBar.js.map