/**
 * Aura Chat Provider
 * ==================
 *
 * Provides an interactive chat interface with Aura in VS Code.
 * Allows developers to ask questions and get intelligent responses.
 */
import * as vscode from 'vscode';
import { AuraConnection } from '../connection';
export declare class AuraChatProvider implements vscode.WebviewViewProvider {
    private readonly _extensionUri;
    private connection;
    static readonly viewType = "aura.chat";
    private _view?;
    constructor(_extensionUri: vscode.Uri, connection: AuraConnection);
    resolveWebviewView(webviewView: vscode.WebviewView, context: vscode.WebviewViewResolveContext, _token: vscode.CancellationToken): void;
    askQuestion(question: string): Promise<void>;
    private handleQuestion;
    private clearChat;
    private _getHtmlForWebview;
}
//# sourceMappingURL=chatProvider.d.ts.map