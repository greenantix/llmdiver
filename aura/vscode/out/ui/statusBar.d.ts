/**
 * Aura Status Bar Manager
 * =======================
 *
 * Manages the VS Code status bar integration for Aura.
 * Shows connection status, activity indicators, and quick actions.
 */
import { ConnectionStatus } from '../connection';
export declare class AuraStatusBar {
    private statusBarItem;
    private activityItem;
    constructor();
    show(): void;
    hide(): void;
    updateConnectionStatus(status: ConnectionStatus): void;
    showActivity(message: string): void;
    hideActivity(): void;
    dispose(): void;
}
//# sourceMappingURL=statusBar.d.ts.map