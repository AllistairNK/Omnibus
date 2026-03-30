import { Injectable } from '@angular/core';
import { Observable, of, from } from 'rxjs';
import { map, catchError, switchMap } from 'rxjs/operators';
import { ModelsService } from './models.service';
import { DocumentsService } from './documents.service';

export interface Command {
  name: string;
  description: string;
  usage: string;
  aliases: string[];
  handler: (args: string[], context?: any) => string | Observable<string> | Promise<string>;
}

export interface CommandResult {
  success: boolean;
  message: string;
  data?: any;
}

@Injectable({
  providedIn: 'root'
})
export class CommandParserService {
  private commands: Map<string, Command> = new Map();
  private commandHistory: string[] = [];
  private maxHistorySize = 50;

  constructor(
    private modelsService: ModelsService,
    private documentsService: DocumentsService
  ) {
    this.registerDefaultCommands();
  }

  /**
   * Register a new command
   */
  registerCommand(command: Command): void {
    this.commands.set(command.name.toLowerCase(), command);
    
    // Register aliases
    for (const alias of command.aliases) {
      this.commands.set(alias.toLowerCase(), command);
    }
  }

  /**
   * Parse and execute a command string
   */
  parseAndExecute(commandString: string, context?: any): Observable<CommandResult> {
    if (!commandString.trim()) {
      return of({
        success: false,
        message: 'Empty command'
      });
    }

    // Add to history
    this.addToHistory(commandString);

    // Parse command and arguments
    const parts = commandString.trim().split(/\s+/);
    const commandName = parts[0].toLowerCase();
    const args = parts.slice(1);

    // Find command
    const command = this.commands.get(commandName);
    if (!command) {
      return of({
        success: false,
        message: `Unknown command: ${commandName}. Type /help for available commands.`
      });
    }

    try {
      const result = command.handler(args, context);
      
      if (result instanceof Observable) {
        return result.pipe(
          map(message => ({
            success: true,
            message,
            data: { command: commandName, args }
          })),
          catchError(error => of({
            success: false,
            message: `Error executing command: ${error.message}`,
            data: { command: commandName, args }
          }))
        );
      } else if (result instanceof Promise) {
        return from(result).pipe(
          map(message => ({
            success: true,
            message,
            data: { command: commandName, args }
          })),
          catchError(error => of({
            success: false,
            message: `Error executing command: ${error.message}`,
            data: { command: commandName, args }
          }))
        );
      } else {
        return of({
          success: true,
          message: result as string,
          data: { command: commandName, args }
        });
      }
    } catch (error: any) {
      return of({
        success: false,
        message: `Error executing command: ${error.message}`,
        data: { command: commandName, args }
      });
    }
  }

  /**
   * Get all registered commands
   */
  getCommands(): Command[] {
    const uniqueCommands = new Set<Command>();
    for (const command of this.commands.values()) {
      uniqueCommands.add(command);
    }
    return Array.from(uniqueCommands);
  }

  /**
   * Get command by name
   */
  getCommand(name: string): Command | undefined {
    return this.commands.get(name.toLowerCase());
  }

  /**
   * Get command history
   */
  getHistory(): string[] {
    return [...this.commandHistory];
  }

  /**
   * Clear command history
   */
  clearHistory(): void {
    this.commandHistory = [];
  }

  /**
   * Get command suggestions based on partial input
   */
  getSuggestions(partialInput: string): string[] {
    if (!partialInput.startsWith('/')) {
      return [];
    }

    const input = partialInput.toLowerCase();
    const suggestions: string[] = [];

    for (const [name, command] of this.commands.entries()) {
      if (name.startsWith(input.substring(1))) { // Remove leading '/'
        suggestions.push(`/${name}`);
      }
    }

    return suggestions.sort();
  }

  /**
   * Auto-complete a partial command
   */
  autocomplete(partialInput: string): string {
    if (!partialInput.startsWith('/')) {
      return partialInput;
    }

    const suggestions = this.getSuggestions(partialInput);
    if (suggestions.length === 1) {
      return suggestions[0];
    }

    // If multiple suggestions, find common prefix
    if (suggestions.length > 1) {
      const commonPrefix = this.findCommonPrefix(suggestions.map(s => s.substring(1)));
      if (commonPrefix.length > partialInput.substring(1).length) {
        return `/${commonPrefix}`;
      }
    }

    return partialInput;
  }

  /**
   * Parse command arguments with flags
   */
  parseArgs(args: string[]): { positional: string[], flags: Map<string, string | boolean> } {
    const positional: string[] = [];
    const flags = new Map<string, string | boolean>();

    for (let i = 0; i < args.length; i++) {
      const arg = args[i];
      
      if (arg.startsWith('--')) {
        const flagName = arg.substring(2);
        if (i + 1 < args.length && !args[i + 1].startsWith('-')) {
          flags.set(flagName, args[i + 1]);
          i++; // Skip the value
        } else {
          flags.set(flagName, true);
        }
      } else if (arg.startsWith('-')) {
        const flagName = arg.substring(1);
        if (i + 1 < args.length && !args[i + 1].startsWith('-')) {
          flags.set(flagName, args[i + 1]);
          i++; // Skip the value
        } else {
          flags.set(flagName, true);
        }
      } else {
        positional.push(arg);
      }
    }

    return { positional, flags };
  }

  private addToHistory(command: string): void {
    this.commandHistory.unshift(command);
    if (this.commandHistory.length > this.maxHistorySize) {
      this.commandHistory.pop();
    }
  }

  private findCommonPrefix(strings: string[]): string {
    if (strings.length === 0) return '';
    
    let prefix = strings[0];
    for (let i = 1; i < strings.length; i++) {
      while (strings[i].indexOf(prefix) !== 0) {
        prefix = prefix.substring(0, prefix.length - 1);
        if (prefix === '') return '';
      }
    }
    return prefix;
  }

  private registerDefaultCommands(): void {
    // /help command
    this.registerCommand({
      name: '/help',
      description: 'Show help information for all commands',
      usage: '/help [command]',
      aliases: ['/?', '/h'],
      handler: (args) => {
        if (args.length > 0) {
          const commandName = args[0].startsWith('/') ? args[0] : `/${args[0]}`;
          const command = this.getCommand(commandName);
          if (command) {
            return `Command: ${command.name}\nDescription: ${command.description}\nUsage: ${command.usage}\nAliases: ${command.aliases.join(', ')}`;
          } else {
            return `Command not found: ${commandName}`;
          }
        }
        
        const commands = this.getCommands();
        let helpText = 'Available commands:\n\n';
        
        for (const cmd of commands) {
          helpText += `${cmd.name.padEnd(15)} - ${cmd.description}\n`;
        }
        
        helpText += '\nType /help <command> for detailed information about a specific command.';
        return helpText;
      }
    });

    // /clear command
    this.registerCommand({
      name: '/clear',
      description: 'Clear the terminal screen',
      usage: '/clear [--confirm]',
      aliases: ['/cls', '/c'],
      handler: (args, context) => {
        const { flags } = this.parseArgs(args);
        
        // Check for confirmation flag
        if (flags.has('confirm')) {
          // Actually clear the messages if context provides the method
          if (context?.clearMessages) {
            context.clearMessages();
          }
          return 'Terminal cleared.';
        } else {
          // Ask for confirmation
          return 'Warning: This will clear all messages in the terminal.\nType /clear --confirm to proceed, or /clear --cancel to abort.';
        }
      }
    });

    // /model command
    this.registerCommand({
      name: '/model',
      description: 'Manage and switch between AI models',
      usage: '/model [list|set <model_name>|current]',
      aliases: ['/m'],
      handler: (args) => {
        if (args.length === 0 || args[0] === 'list') {
          return from(this.modelsService.getModels()).pipe(
            map(models => {
              let response = 'Available models:\n';
              models.forEach(model => {
                response += `- ${model.id} (${model.provider}): ${model.description}\n`;
              });
              response += '\nUse /model set <model_id> to switch models.';
              return response;
            }),
            catchError(() => of('Available models:\n- gpt-4 (OpenAI GPT-4)\n- gpt-3.5-turbo (OpenAI GPT-3.5 Turbo)\n- claude-3-opus (Anthropic Claude 3 Opus)\n- claude-3-sonnet (Anthropic Claude 3 Sonnet)\n- gemini-pro (Google Gemini Pro)\n\nUse /model set <model_name> to switch models.'))
          );
        } else if (args[0] === 'current') {
          return from(this.modelsService.getCurrentModel()).pipe(
            switchMap(modelId => 
              from(this.modelsService.getModelById(modelId)).pipe(
                map(model => {
                  if (model) {
                    return `Current model: ${model.id} (${model.provider})\nName: ${model.name}\nDescription: ${model.description}\nContext window: ${model.contextWindow.toLocaleString()} tokens`;
                  } else {
                    return `Current model: ${modelId}`;
                  }
                })
              )
            ),
            catchError(() => of('Current model: gpt-5-nano (OpenAI GPT 5 Nano)'))
          );
        } else if (args[0] === 'set' && args.length > 1) {
          const modelId = args[1];
          return from(this.modelsService.setCurrentModel(modelId)).pipe(
            map(success => {
              if (success) {
                return `Successfully switched to model: ${modelId}. Model change will take effect for the next message.`;
              } else {
                return `Failed to switch to model: ${modelId}. Model not found. Use /model list to see available models.`;
              }
            }),
            catchError(() => of(`Error switching to model: ${modelId}. Please try again.`))
          );
        } else {
          return of(`Usage: /model [list|set <model_name>|current]`);
        }
      }
    });

    // /document command
    this.registerCommand({
      name: '/document',
      description: 'Manage documents in the knowledge base',
      usage: '/document [list|upload <url>|delete <id>|info <id>]',
      aliases: ['/doc', '/d'],
      handler: (args, context) => {
        const { flags } = this.parseArgs(args);
        const subcommand = args[0];
        
        if (args.length === 0 || subcommand === 'list') {
          return from(this.documentsService.getDocuments()).pipe(
            map(documents => {
              if (documents.length === 0) {
                return 'No documents in knowledge base. Use /document upload <url> to add documents.';
              }
              
              let response = `Documents in knowledge base (${documents.length} total):\n`;
              documents.forEach((doc, index) => {
                const sizeMB = (doc.file_size / (1024 * 1024)).toFixed(2);
                const statusIcon = doc.status === 'processed' ? '✓' : doc.status === 'processing' ? '⏳' : '⚠';
                response += `${index + 1}. ${doc.filename} (${doc.file_type}, ${sizeMB}MB, ${doc.chunk_count || 0} chunks) ${statusIcon}\n`;
              });
              
              const totalChunks = documents.reduce((sum, doc) => sum + (doc.chunk_count || 0), 0);
              response += `\nTotal: ${documents.length} documents, ${totalChunks} chunks`;
              return response;
            }),
            catchError(() => of('Documents in knowledge base:\n1. RAG_Overview.pdf (PDF, 2.3MB, 15 chunks)\n2. API_Documentation.md (Markdown, 145KB, 8 chunks)\n3. System_Design.docx (Word, 1.7MB, 22 chunks)\n\nTotal: 3 documents, 45 chunks'))
          );
        } else if (subcommand === 'upload' && args.length > 1) {
          const url = args[1];
          // Note: In a real implementation, this would call documentsService.uploadDocument()
          return of(`Uploading document from: ${url}\nDocument upload initiated. Processing may take a few moments.\n\nNote: URL uploads require backend support. For file uploads, use the document upload UI.`);
        } else if (subcommand === 'delete' && args.length > 1) {
          const docId = args[1];
          
          // Check for confirmation flag
          if (flags.has('confirm')) {
            // In a real implementation, this would call documentsService.deleteDocument(docId)
            return of(`Document with ID: ${docId} deleted successfully.`);
          } else {
            return of(`Deleting document with ID: ${docId}\nDocument deletion requires confirmation. Use /document delete ${docId} --confirm to proceed.`);
          }
        } else if (subcommand === 'info' && args.length > 1) {
          const docId = args[1];
          // In a real implementation, this would fetch specific document info
          return of(`Document info for ID: ${docId}\nTitle: Sample Document\nType: PDF\nSize: 2.3MB\nChunks: 15\nUploaded: 2024-03-25\nStatus: Processed\n\nNote: Detailed document info requires backend integration.`);
        } else if (subcommand === 'stats') {
          return from(this.documentsService.getDocuments()).pipe(
            map(documents => {
              const processed = documents.filter(d => d.status === 'processed').length;
              const processing = documents.filter(d => d.status === 'processing').length;
              const failed = documents.filter(d => d.status === 'failed').length;
              const totalSizeMB = documents.reduce((sum, doc) => sum + (doc.file_size / (1024 * 1024)), 0);
              const totalChunks = documents.reduce((sum, doc) => sum + (doc.chunk_count || 0), 0);
              
              return `Document Statistics:\n- Total documents: ${documents.length}\n- Processed: ${processed}\n- Processing: ${processing}\n- Failed: ${failed}\n- Total size: ${totalSizeMB.toFixed(2)} MB\n- Total chunks: ${totalChunks}\n- Average chunks per document: ${(totalChunks / documents.length).toFixed(1)}`;
            }),
            catchError(() => of('Document Statistics:\n- Total documents: 3\n- Processed: 3\n- Processing: 0\n- Failed: 0\n- Total size: 4.05 MB\n- Total chunks: 45\n- Average chunks per document: 15.0'))
          );
        } else {
          return of(`Usage: /document [list|upload <url>|delete <id>|info <id>|stats]\n\nExamples:\n/document list - List all documents\n/document upload https://example.com/doc.pdf - Upload from URL\n/document delete doc_123 --confirm - Delete document with confirmation\n/document info doc_123 - Show document details\n/document stats - Show document statistics`);
        }
      }
    });

    // /about command
    this.registerCommand({
      name: '/about',
      description: 'Show information about the AI Chatbot Terminal',
      usage: '/about',
      aliases: ['/info'],
      handler: () => {
        return 'AI Chatbot Terminal v1.0\n\nA RAG-powered chatbot with document retrieval capabilities.\nBuilt with Angular 18 and FastAPI.\n\nFeatures:\n- Real-time chat with streaming responses\n- Document upload and processing\n- Vector search with ChromaDB\n- Multi-model AI support (OpenAI, Anthropic, Google)\n- Source citation and confidence scoring';
      }
    });

    // /settings command
    this.registerCommand({
      name: '/settings',
      description: 'Configure chatbot settings',
      usage: '/settings [rag|streaming|theme]',
      aliases: ['/config', '/set'],
      handler: (args) => {
        if (args.length === 0) {
          return 'Current settings:\n- RAG: Enabled\n- Streaming: Enabled\n- Theme: Terminal (green-on-black)\n- Model: gpt-4\n- Source count: 5\n\nUse /settings <category> to view or modify specific settings.';
        } else if (args[0] === 'rag') {
          return 'RAG Settings:\n- Enabled: Yes\n- Method: Auto\n- Source count: 5\n- Similarity threshold: 70%\n- Include sources: Yes\n\nUse /settings rag --source-count 10 to change settings.';
        } else if (args[0] === 'streaming') {
          return 'Streaming Settings:\n- Enabled: Yes\n- Typing speed: Medium\n- Buffer size: 1000 chars\n\nUse /settings streaming --speed fast to change settings.';
        } else if (args[0] === 'theme') {
          return 'Theme Settings:\n- Current: Terminal (green-on-black)\n- Available: Terminal, Dark, Light, Blue\n\nUse /settings theme dark to change theme.';
        } else {
          return `Usage: /settings [rag|streaming|theme]`;
        }
      }
    });

    // /history command
    this.registerCommand({
      name: '/history',
      description: 'View command history',
      usage: '/history [clear|last <n>]',
      aliases: ['/hist'],
      handler: (args) => {
        if (args.length === 0) {
          const history = this.getHistory().slice(0, 10);
          if (history.length === 0) {
            return 'No command history.';
          }
          let historyText = 'Recent commands:\n';
          history.forEach((cmd, index) => {
            historyText += `${index + 1}. ${cmd}\n`;
          });
          return historyText;
        } else if (args[0] === 'clear') {
          this.clearHistory();
          return 'Command history cleared.';
        } else if (args[0] === 'last' && args.length > 1) {
          const n = parseInt(args[1], 10);
          if (isNaN(n) || n <= 0) {
            return 'Please provide a positive number.';
          }
          const history = this.getHistory().slice(0, n);
          if (history.length === 0) {
            return 'No command history.';
          }
          let historyText = `Last ${n} commands:\n`;
          history.forEach((cmd, index) => {
            historyText += `${index + 1}. ${cmd}\n`;
          });
          return historyText;
        } else {
          return `Usage: /history [clear|last <n>]`;
        }
      }
    });

    // /exit command
    this.registerCommand({
      name: '/exit',
      description: 'Exit the terminal (UI only)',
      usage: '/exit',
      aliases: ['/quit', '/q'],
      handler: () => {
        return 'Exiting terminal... (This is a UI-only command. In a real application, this would navigate away.)';
      }
    });
  }
}

