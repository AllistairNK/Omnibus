import { Component, OnInit, AfterViewChecked, ElementRef, ViewChild, OnDestroy } from '@angular/core';
import { ChatService, ChatMessage, ChatCompletionRequest } from '../../../../core/services/chat.service';
import { CommandParserService, CommandResult } from '../../../../core/services/command-parser.service';
import { Subscription, Subject, timer } from 'rxjs';
import { firstValueFrom } from 'rxjs';
import { debounceTime, distinctUntilChanged, takeUntil } from 'rxjs/operators';
import { CdkVirtualScrollViewport } from '@angular/cdk/scrolling';
@Component({
  selector: 'app-chat',
  templateUrl: './chat.component.html',
  styleUrls: ['./chat.component.scss']
})
export class ChatComponent implements OnInit, AfterViewChecked, OnDestroy {
  @ViewChild('terminalOutput') private terminalOutput!: ElementRef;
  @ViewChild(CdkVirtualScrollViewport) viewport!: CdkVirtualScrollViewport;

  messages: ChatMessage[] = [
    { role: 'assistant', content: 'Hello! I am your AI assistant. How can I help you today?', timestamp: new Date().toISOString() },
    { role: 'user', content: 'Tell me about RAG.', timestamp: new Date().toISOString() },
    { role: 'assistant', content: 'RAG stands for Retrieval-Augmented Generation. It combines retrieval of relevant documents with generative AI to produce accurate, context-aware responses.', timestamp: new Date().toISOString(), metadata: { sources: [
      { document_id: 'doc1', document_title: 'RAG Overview.pdf', chunk_text: 'Retrieval-Augmented Generation (RAG) enhances large language models by retrieving relevant documents from a knowledge base.', similarity_score: 0.95 },
      { document_id: 'doc2', document_title: 'AI Research Paper.docx', chunk_text: 'RAG models outperform standard LLMs on knowledge-intensive tasks by incorporating external knowledge.', similarity_score: 0.87 }
    ]} }
  ];
  
  // Lazy loading properties
  protected isLoadingMessages = false;
  private hasMoreMessages = true;
  private currentPage = 1;
  private pageSize = 20;
  private totalMessages = 0;
  
  // Debouncing properties
  private inputSubject = new Subject<string>();
  private destroy$ = new Subject<void>();
  private debounceTimeMs = 300; // 300ms debounce time
  newMessage = '';
  isTyping = false;
  messageHistory: string[] = [];
  historyIndex = -1;
  currentChatId: string | null = null;
  streamingResponse = '';
  private streamSubscription?: Subscription;
  private currentStreamAbortController?: AbortController;
  protected isStreaming = false;
  
  // ASCII loading animations
  private asciiLoadingFrames = [
    `
    ⠋ Loading
    `,
    `
    ⠙ Loading
    `,
    `
    ⠹ Loading
    `,
    `
    ⠸ Loading
    `,
    `
    ⠼ Loading
    `,
    `
    ⠴ Loading
    `,
    `
    ⠦ Loading
    `,
    `
    ⠧ Loading
    `,
    `
    ⠇ Loading
    `,
    `
    ⠏ Loading
    `
  ];
  
  private asciiThinkingFrames = [
    `
    ( •_•)
    ( •_•)>⌐■-■
    (⌐■_■)
    `,
    `
    ( •_•)
    ( •_•)>⌐■-■
    (⌐■_■) 
    `,
    `
    ( •_•)
    ( •_•)>⌐■-■
    (⌐■_■)  
    `
  ];
  
  private currentLoadingInterval: any = null;
  
  // Command suggestions
  commandSuggestions: string[] = [];
  showSuggestions = false;
  selectedSuggestionIndex = -1;
  
  // RAG Configuration
  showRagSettings = false;
  ragConfig = {
    useRag: true,
    ragMethod: 'auto',
    sourceCount: 5,
    similarityThreshold: 70,
    includeSources: true,
    highlightMatches: true
  };

  // Streaming Configuration
  streamingConfig = {
    bufferSize: 3, // Number of tokens to buffer before display
    minDisplayTime: 10, // Minimum ms per token
    maxDisplayTime: 50, // Maximum ms per token
    smoothScrolling: true
  };

  constructor(
    private chatService: ChatService,
    private commandParser: CommandParserService
  ) {}

  ngOnInit() {
    // Initialize with some command history
    this.messageHistory = ['/help', 'Tell me about RAG', 'What is vector search?'];
    
    // Create a new chat session or load existing one
    this.createOrLoadChat();
    
    // Load saved RAG settings
    this.loadRagSettings();
    
    // Load initial messages
    this.loadMoreMessages();
    
    // Setup debounced input handler
    this.setupDebouncedInput();
  }

  ngAfterViewChecked() {
    this.scrollToBottom();
  }

  ngOnDestroy() {
    // Clean up subscriptions
    if (this.streamSubscription) {
      this.streamSubscription.unsubscribe();
    }
    this.chatService.closeStream();
    // Abort any ongoing stream
    if (this.currentStreamAbortController) {
      this.currentStreamAbortController.abort();
    }
    
    // Clean up debouncing subjects
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * Stop the current streaming response
   */
  stopStreaming() {
    if (this.currentStreamAbortController && this.isStreaming) {
      this.currentStreamAbortController.abort();
      this.isStreaming = false;
      this.isTyping = false;
      this.stopLoadingAnimation();
    }
  }

  /**
   * Start ASCII loading animation
   */
  private startLoadingAnimation() {
    let frameIndex = 0;
    this.stopLoadingAnimation();
    
    this.currentLoadingInterval = setInterval(() => {
      // Update the last message with loading animation
      if (this.messages.length > 0) {
        const lastMessage = this.messages[this.messages.length - 1];
        if (lastMessage.role === 'assistant' && lastMessage.metadata?.streaming) {
          const loadingFrame = this.asciiLoadingFrames[frameIndex % this.asciiLoadingFrames.length];
          this.messages[this.messages.length - 1] = {
            ...lastMessage,
            content: lastMessage.content + '\n' + loadingFrame
          };
          frameIndex++;
        }
      }
    }, 150);
  }

  /**
   * Stop ASCII loading animation
   */
  private stopLoadingAnimation() {
    if (this.currentLoadingInterval) {
      clearInterval(this.currentLoadingInterval);
      this.currentLoadingInterval = null;
    }
  }

  scrollToBottom(): void {
    try {
      if (this.terminalOutput) {
        this.terminalOutput.nativeElement.scrollTop = this.terminalOutput.nativeElement.scrollHeight;
      }
    } catch(err) { }
  }

  async sendMessage() {
    if (this.newMessage.trim()) {
      // Add to history
      this.messageHistory.unshift(this.newMessage);
      this.historyIndex = -1;
      
      // Add user message
      const userMessage: ChatMessage = {
        role: 'user',
        content: this.newMessage,
        timestamp: new Date().toISOString()
      };
      this.messages.push(userMessage);
      const messageContent = this.newMessage;
      this.newMessage = '';
      
      // Show typing indicator
      this.isTyping = true;
      this.streamingResponse = '';
      
      // Handle commands locally using command parser
      if (messageContent.startsWith('/')) {
        this.isTyping = true;
        
        this.commandParser.parseAndExecute(messageContent, {
          component: this,
          messages: this.messages,
          clearMessages: () => this.messages = []
        }).subscribe({
          next: (result: CommandResult) => {
            this.isTyping = false;
            
            // Handle special commands that modify UI state
            if (messageContent.toLowerCase() === '/clear' || messageContent.toLowerCase() === '/cls') {
              this.messages = [];
            }
            
            // Add assistant response
            this.messages.push({
              role: 'assistant',
              content: result.message,
              timestamp: new Date().toISOString(),
              metadata: { commandResult: result }
            });
          },
          error: (error) => {
            this.isTyping = false;
            this.messages.push({
              role: 'assistant',
              content: `Error executing command: ${error.message}`,
              timestamp: new Date().toISOString()
            });
          }
        });
        return;
      }
      
      // Send to backend with streaming
      const request: ChatCompletionRequest = {
        message: messageContent,
        chat_id: this.currentChatId || undefined,
        model: 'gpt-4',
        stream: true,
        use_rag: true,
        include_sources: true
      };
      
      try {
        // Create abort controller for this stream
        this.currentStreamAbortController = new AbortController();
        this.isStreaming = true;
        
        // Use the async generator for streaming with abort signal
        const stream = this.chatService.streamMessage(request, this.currentStreamAbortController.signal);
        let fullResponse = '';
        let displayedResponse = '';
        
        // Create initial streaming message
        this.messages.push({
          role: 'assistant',
          content: '',
          timestamp: new Date().toISOString(),
          metadata: { streaming: true, interruptible: true }
        });
        const streamingMessageIndex = this.messages.length - 1;
        
        // Start loading animation
        this.startLoadingAnimation();
        
        try {
          for await (const token of stream) {
            fullResponse += token;
            
            // Add token to display buffer
            displayedResponse += token;
            
            // Update the UI with typing simulation
            // Instead of simulating character by character (which could be slow for long responses),
            // we'll update in chunks but with a slight delay to simulate thinking
            this.messages[streamingMessageIndex] = {
              ...this.messages[streamingMessageIndex],
              content: displayedResponse
            };
            
            // Add a small delay for typing effect (faster for short tokens, slower for longer ones)
            const delay = Math.min(
              this.streamingConfig.maxDisplayTime, 
              Math.max(this.streamingConfig.minDisplayTime, token.length * 5)
            );
            await new Promise(resolve => setTimeout(resolve, delay));
          }
        } catch (error: any) {
          if (error.name === 'AbortError') {
            // Stream was interrupted by user
            this.messages[streamingMessageIndex] = {
              ...this.messages[streamingMessageIndex],
              content: displayedResponse + ' [Interrupted]',
              metadata: { streaming: false, interrupted: true }
            };
            this.isTyping = false;
            this.isStreaming = false;
            this.currentStreamAbortController = undefined;
            return;
          }
          throw error;
        }
        
        // Streaming complete
        this.isTyping = false;
        this.isStreaming = false;
        this.streamingResponse = '';
        this.currentStreamAbortController = undefined;
        this.stopLoadingAnimation();
        
        // Update final message (remove streaming metadata)
        this.messages[streamingMessageIndex] = {
          role: 'assistant',
          content: fullResponse,
          timestamp: new Date().toISOString(),
          metadata: { streaming: false }
        };
        
      } catch (error) {
        console.error('Error in chat completion:', error);
        this.isTyping = false;
        this.isStreaming = false;
        this.streamingResponse = '';
        this.stopLoadingAnimation();
        this.currentStreamAbortController = undefined;
        
        // Fallback to simulated response
        setTimeout(() => {
          const response = this.generateResponse(messageContent);
          this.messages.push({
            role: 'assistant',
            content: response,
            timestamp: new Date().toISOString()
          });
        }, 1000);
      }
    }
  }

  private updateStreamingResponse(response: string) {
    // Remove any existing streaming message
    const lastMessage = this.messages[this.messages.length - 1];
    if (lastMessage.role === 'assistant' && lastMessage.metadata?.streaming) {
      this.messages[this.messages.length - 1] = {
        ...lastMessage,
        content: response
      };
    } else {
      // Add new streaming message
      this.messages.push({
        role: 'assistant',
        content: response,
        timestamp: new Date().toISOString(),
        metadata: { streaming: true }
      });
    }
  }

  /**
   * Simulate typing with variable speed based on character type
   * Faster for common characters (letters, spaces), slower for punctuation and complex characters
   */
  private async simulateTyping(text: string, onProgress: (displayText: string) => void): Promise<void> {
    let displayText = '';
    const baseDelay = 20; // Base delay in ms per character
    const fastDelay = 10; // Faster for common characters
    const slowDelay = 50; // Slower for punctuation/complex
    
    for (let i = 0; i < text.length; i++) {
      const char = text[i];
      
      // Determine delay based on character type
      let delay = baseDelay;
      if (/[a-zA-Z0-9\s]/.test(char)) {
        delay = fastDelay;
      } else if (/[.,;:!?]/.test(char)) {
        delay = slowDelay;
      } else if (/[{}[\]()<>]/.test(char)) {
        delay = slowDelay * 1.5;
      }
      
      // Add some randomness (±30%)
      delay = delay * (0.7 + Math.random() * 0.6);
      
      // Wait before adding character
      await new Promise(resolve => setTimeout(resolve, delay));
      
      displayText += char;
      onProgress(displayText);
    }
  }

  private async createOrLoadChat() {
    try {
      const response = await firstValueFrom(this.chatService.createChat('New Chat', 'gpt-4'));
      this.currentChatId = response.id;
    } catch (error) {
      console.error('Error creating chat session:', error);
      // Continue without chat ID (messages won't be persisted)
    }
  }

  /**
   * Load more messages for lazy loading
   */
  private async loadMoreMessages() {
    if (this.isLoadingMessages || !this.hasMoreMessages || !this.currentChatId) {
      return;
    }

    this.isLoadingMessages = true;
    
    try {
      const response = await firstValueFrom(
        this.chatService.getChatMessages(this.currentChatId, this.currentPage, this.pageSize)
      );
      
      // Add new messages to the beginning (since we're loading older messages)
      this.messages = [...response.messages, ...this.messages];
      this.totalMessages = response.total;
      
      // Check if we have more messages to load
      this.hasMoreMessages = this.messages.length < this.totalMessages;
      if (this.hasMoreMessages) {
        this.currentPage++;
      }
    } catch (error) {
      console.error('Error loading messages:', error);
    } finally {
      this.isLoadingMessages = false;
    }
  }

  /**
   * Handle virtual scroll index change
   */
  onScrollIndexChanged() {
    if (!this.viewport) return;
    
    const scrollOffset = this.viewport.measureScrollOffset('top');
    const viewportSize = this.viewport.getViewportSize();
    const totalSize = this.viewport.getDataLength() * 50; // Approximate item height
    
    // Load more when scrolled near the top (for loading older messages)
    if (scrollOffset < 100 && this.hasMoreMessages && !this.isLoadingMessages) {
      this.loadMoreMessages();
    }
  }

  /**
   * Setup debounced input handler for typing
   */
  private setupDebouncedInput() {
    this.inputSubject.pipe(
      debounceTime(this.debounceTimeMs),
      distinctUntilChanged(),
      takeUntil(this.destroy$)
    ).subscribe((value: string) => {
      this.onDebouncedInput(value);
    });
  }

  /**
   * Handle debounced input changes
   */
  private onDebouncedInput(value: string) {
    // Update command suggestions based on debounced input
    if (value.startsWith('/')) {
      this.updateCommandSuggestions();
    }
    
    // You can add more debounced operations here, such as:
    // - Auto-save draft messages
    // - Real-time spell checking
    // - Search-as-you-type in document references
    // - Typing indicator to other users (in multi-user scenarios)
    
    // Log for debugging (remove in production)
    if (value.length > 0) {
      console.debug(`Debounced input: "${value}" (after ${this.debounceTimeMs}ms)`);
    }
  }

  /**
   * Handle input changes with debouncing
   */
  onInputChange(value: string) {
    this.inputSubject.next(value);
  }

  handleCommand(command: string): string {
    const cmd = command.toLowerCase().trim();
    
    if (cmd === '/help' || cmd === '/?') {
      return 'Available commands: /help - Show this help, /clear - Clear terminal, /model - Switch model, /documents - List documents, /about - About this terminal';
    } else if (cmd === '/clear') {
      this.messages = [];
      return 'Terminal cleared.';
    } else if (cmd === '/about') {
      return 'AI Chatbot Terminal v1.0 - RAG-powered chatbot with document retrieval. Built with Angular 18 and FastAPI.';
    } else if (cmd === '/model') {
      return 'Current model: GPT-4. Available models: GPT-4, Claude-3, Gemini-Pro. Use /model <name> to switch.';
    } else if (cmd === '/documents') {
      return '3 documents indexed: 1) RAG_Overview.pdf, 2) API_Documentation.md, 3) System_Design.docx';
    } else {
      return `Unknown command: ${command}. Type /help for available commands.`;
    }
  }

  generateResponse(input: string): string {
    const responses = [
      `I understand you're asking about "${input}". Based on my knowledge, this relates to retrieval-augmented generation systems.`,
      `Interesting question about "${input}". Let me retrieve relevant documents to provide a comprehensive answer.`,
      `Processing your query: "${input}". I've found 3 relevant documents in the knowledge base.`,
      `Regarding "${input}", the RAG system has identified key information from indexed documents.`,
      `Your question about "${input}" has been processed. Here's what I found in the knowledge base.`
    ];
    
    return responses[Math.floor(Math.random() * responses.length)];
  }

  onKeyDown(event: KeyboardEvent) {
    // Handle up/down arrows for message history
    if (event.key === 'ArrowUp') {
      event.preventDefault();
      if (this.historyIndex < this.messageHistory.length - 1) {
        this.historyIndex++;
        this.newMessage = this.messageHistory[this.historyIndex];
      }
    } else if (event.key === 'ArrowDown') {
      event.preventDefault();
      if (this.historyIndex > 0) {
        this.historyIndex--;
        this.newMessage = this.messageHistory[this.historyIndex];
      } else if (this.historyIndex === 0) {
        this.historyIndex = -1;
        this.newMessage = '';
      }
    } else if (event.key === 'Tab') {
      event.preventDefault();
      // Enhanced autocomplete using command parser
      if (this.newMessage.startsWith('/')) {
        const completed = this.commandParser.autocomplete(this.newMessage);
        if (completed !== this.newMessage) {
          this.newMessage = completed;
          this.updateCommandSuggestions();
        } else {
          // Show suggestions if multiple matches
          this.updateCommandSuggestions();
          if (this.commandSuggestions.length > 0) {
            this.showSuggestions = true;
            this.selectedSuggestionIndex = 0;
          }
        }
      }
    } else if (event.key === 'Escape') {
      // Hide suggestions
      this.showSuggestions = false;
      this.selectedSuggestionIndex = -1;
    } else if (event.key === 'Enter' && this.showSuggestions && this.selectedSuggestionIndex >= 0) {
      // Apply selected suggestion
      event.preventDefault();
      this.applySuggestion(this.selectedSuggestionIndex);
    } else if (event.key === 'ArrowRight' && this.showSuggestions && this.selectedSuggestionIndex >= 0) {
      // Apply selected suggestion
      event.preventDefault();
      this.applySuggestion(this.selectedSuggestionIndex);
    } else if (event.key === 'ArrowUp' && this.showSuggestions) {
      // Navigate suggestions
      event.preventDefault();
      this.selectPreviousSuggestion();
    } else if (event.key === 'ArrowDown' && this.showSuggestions) {
      // Navigate suggestions
      event.preventDefault();
      this.selectNextSuggestion();
    } else {
      // Update suggestions as user types
      this.updateCommandSuggestions();
    }
  }

  // Source citation helper methods
  getSourceCount(msg: ChatMessage): number {
    if (msg.sources && msg.sources.length > 0) {
      return msg.sources.length;
    }
    if (msg.metadata?.sources && Array.isArray(msg.metadata.sources)) {
      return msg.metadata.sources.length;
    }
    return 0;
  }

  getSources(msg: ChatMessage): any[] {
    if (msg.sources && msg.sources.length > 0) {
      return msg.sources;
    }
    if (msg.metadata?.sources && Array.isArray(msg.metadata.sources)) {
      return msg.metadata.sources;
    }
    return [];
  }

  toggleSources(msg: ChatMessage): void {
    if (!msg.hasOwnProperty('showSources')) {
      msg.showSources = false;
    }
    msg.showSources = !msg.showSources;
  }

  getConfidenceClass(score: number): string {
    if (score >= 0.9) return 'confidence-high';
    if (score >= 0.7) return 'confidence-medium';
    return 'confidence-low';
  }

  viewDocument(documentId: string): void {
    console.log('View document:', documentId);
    // TODO: Implement document viewing
    alert(`View document ${documentId} - Feature coming soon!`);
  }

  highlightInDocument(source: any): void {
    console.log('Highlight in document:', source);
    // TODO: Implement document highlighting
    alert(`Highlighting text in ${source.document_title} - Feature coming soon!`);
  }

  truncateText(text: string, maxLength: number): string {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  }

  // RAG Configuration methods
  toggleRagSettings(): void {
    this.showRagSettings = !this.showRagSettings;
  }

  saveRagSettings(): void {
    console.log('Saving RAG settings:', this.ragConfig);
    // TODO: Save to backend or local storage
    localStorage.setItem('ragConfig', JSON.stringify(this.ragConfig));
    alert('RAG settings saved!');
    this.showRagSettings = false;
  }

  resetRagSettings(): void {
    this.ragConfig = {
      useRag: true,
      ragMethod: 'auto',
      sourceCount: 5,
      similarityThreshold: 70,
      includeSources: true,
      highlightMatches: true
    };
    console.log('RAG settings reset to defaults');
  }

  loadRagSettings(): void {
    const saved = localStorage.getItem('ragConfig');
    if (saved) {
      try {
        this.ragConfig = { ...this.ragConfig, ...JSON.parse(saved) };
        console.log('Loaded RAG settings:', this.ragConfig);
      } catch (e) {
        console.error('Failed to parse saved RAG settings:', e);
      }
    }
  }

  /**
   * Update command suggestions based on current input
   */
  updateCommandSuggestions(): void {
    if (this.newMessage.startsWith('/')) {
      this.commandSuggestions = this.commandParser.getSuggestions(this.newMessage);
      this.showSuggestions = this.commandSuggestions.length > 0;
    } else {
      this.commandSuggestions = [];
      this.showSuggestions = false;
    }
    this.selectedSuggestionIndex = -1;
  }

  /**
   * Apply a command suggestion
   */
  applySuggestion(index: number): void {
    if (index >= 0 && index < this.commandSuggestions.length) {
      this.newMessage = this.commandSuggestions[index];
      this.showSuggestions = false;
      this.selectedSuggestionIndex = -1;
    }
  }

  /**
   * Select next suggestion
   */
  selectNextSuggestion(): void {
    if (this.commandSuggestions.length > 0) {
      this.selectedSuggestionIndex = 
        (this.selectedSuggestionIndex + 1) % this.commandSuggestions.length;
    }
  }

  /**
   * Select previous suggestion
   */
  selectPreviousSuggestion(): void {
    if (this.commandSuggestions.length > 0) {
      this.selectedSuggestionIndex = 
        this.selectedSuggestionIndex <= 0 
          ? this.commandSuggestions.length - 1 
          : this.selectedSuggestionIndex - 1;
    }
  }
}