import { Component, OnInit, AfterViewChecked, ElementRef, ViewChild, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { ChatService, ChatMessage, ChatCompletionRequest, ChatSession } from '../../../../core/services/chat.service';
import { CommandParserService, CommandResult } from '../../../../core/services/command-parser.service';
import { AsciiEmotionService, EmotionType } from '../../../../core/services/ascii-emotion.service';
import { Subscription, Subject, timer } from 'rxjs';
import { firstValueFrom } from 'rxjs';
import { debounceTime, distinctUntilChanged, takeUntil } from 'rxjs/operators';
import { CdkVirtualScrollViewport } from '@angular/cdk/scrolling';
import { ChatHistorySidebarComponent } from '../chat-history-sidebar/chat-history-sidebar.component';
@Component({
  selector: 'app-chat',
  templateUrl: './chat.component.html',
  styleUrls: ['./chat.component.scss']
})
export class ChatComponent implements OnInit, AfterViewChecked, OnDestroy {
  @ViewChild('terminalOutput') private terminalOutput!: ElementRef;
  @ViewChild(CdkVirtualScrollViewport) viewport!: CdkVirtualScrollViewport;
  @ViewChild('chatHistorySidebar') private chatHistorySidebar?: ChatHistorySidebarComponent;

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
  
  // Sidebar properties
  sidebarOpen = true;
  private isNewChat = false;
  
  // ASCII loading animations (kept for backward compatibility)
  private asciiLoadingFrames = [
    '⠋ Loading',
    '⠙ Loading',
    '⠹ Loading',
    '⠸ Loading',
    '⠼ Loading',
    '⠴ Loading',
    '⠦ Loading',
    '⠧ Loading',
    '⠇ Loading',
    '⠏ Loading'
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
  
  // Emotion properties
  currentEmotion: EmotionType = 'neutral';
  emotionTransitionProgress = 0;
  isEmotionTransitioning = false;
  currentAsciiFrame = '';
  private emotionSubscription?: Subscription;
  
  // Animated thinking indicators
  currentThinkingFrame = 0;
  thinkingFrames: string[] = [];
  private thinkingInterval: any = null;
  
  // Particle effects
  particles: Array<{id: number, content: string, x: number, y: number, type: 'send' | 'receive'}> = [];
  private particleId = 0;
  
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
    similarityThreshold: 20,
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
    private commandParser: CommandParserService,
    private asciiEmotionService: AsciiEmotionService,
    private cdr: ChangeDetectorRef
  ) {}

  async ngOnInit() {
    
    // Initialize with some command history
    this.messageHistory = ['/help', 'Tell me about RAG', 'What is vector search?'];

    // Load saved RAG settings
    this.loadRagSettings();

    // Setup debounced input handler
    this.setupDebouncedInput();

    // Setup emotion subscriptions
    this.setupEmotionSubscriptions();

    // Initialize thinking frames
    this.thinkingFrames = this.asciiEmotionService.getThinkingIndicators();

    // Create a new chat session or load existing one
    this.createOrLoadChat();

    // Load initial messages
    this.loadMoreMessages();
  }

  ngAfterViewChecked() {
    this.scrollToBottom();
  }

  /**
   * Setup emotion subscriptions
   */
  private setupEmotionSubscriptions(): void {
    // Subscribe to emotion state changes
    this.emotionSubscription = this.asciiEmotionService.getEmotionState().subscribe(state => {
      this.currentEmotion = state.currentEmotion;
      this.emotionTransitionProgress = state.transitionProgress;
      this.isEmotionTransitioning = state.isTransitioning;
    });

    // Subscribe to current ASCII frame
    this.asciiEmotionService.getCurrentFrame().subscribe(frame => {
      this.currentAsciiFrame = frame;
    });

    // Set initial emotion
    this.asciiEmotionService.setEmotion('neutral');
  }

  /**
   * Change emotion based on chat context
   */
  changeEmotionBasedOnContext(context: string): void {
    const contextLower = context.toLowerCase();
    
    if (contextLower.includes('thinking') || contextLower.includes('processing')) {
      this.asciiEmotionService.setEmotion('thinking');
    } else if (contextLower.includes('happy') || contextLower.includes('great') || contextLower.includes('thanks')) {
      this.asciiEmotionService.setEmotion('happy');
    } else if (contextLower.includes('confused') || contextLower.includes('not sure') || contextLower.includes('don\'t know')) {
      this.asciiEmotionService.setEmotion('confused');
    } else if (contextLower.includes('error') || contextLower.includes('failed') || contextLower.includes('wrong')) {
      this.asciiEmotionService.setEmotion('error');
    } else if (contextLower.includes('success') || contextLower.includes('done') || contextLower.includes('complete')) {
      this.asciiEmotionService.setEmotion('success');
    } else if (contextLower.includes('loading') || contextLower.includes('waiting')) {
      this.asciiEmotionService.setEmotion('loading');
    } else {
      this.asciiEmotionService.setEmotion('neutral');
    }
  }

  /**
   * Set emotion directly
   */
  setEmotion(emotion: EmotionType, transitionDuration: number = 500): void {
    this.asciiEmotionService.setEmotion(emotion, transitionDuration);
  }

  /**
   * Start thinking animation
   */
  startThinkingAnimation(): void {
    this.stopThinkingAnimation();
    this.currentThinkingFrame = 0;
    
    this.thinkingInterval = setInterval(() => {
      this.currentThinkingFrame = (this.currentThinkingFrame + 1) % this.thinkingFrames.length;
    }, 100);
  }

  /**
   * Stop thinking animation
   */
  stopThinkingAnimation(): void {
    if (this.thinkingInterval) {
      clearInterval(this.thinkingInterval);
      this.thinkingInterval = null;
    }
  }

  /**
   * Get current thinking frame
   */
  getCurrentThinkingFrame(): string {
    if (this.thinkingFrames.length === 0) {
      return '⠋ Thinking...';
    }
    return this.thinkingFrames[this.currentThinkingFrame];
  }

  /**
   * Create particle effect for message send
   */
  createSendParticle(): void {
    const sendParticles = this.asciiEmotionService.getSendParticles();
    const particleContent = sendParticles[Math.floor(Math.random() * sendParticles.length)];
    
    this.particleId++;
    const particle = {
      id: this.particleId,
      content: particleContent,
      x: Math.random() * 80 + 10, // Random x position (10-90%)
      y: 90, // Start at bottom
      type: 'send' as const
    };
    
    this.particles.push(particle);
    
    // Remove particle after animation
    setTimeout(() => {
      this.particles = this.particles.filter(p => p.id !== particle.id);
    }, 2000);
  }

  /**
   * Create particle effect for message receive
   */
  createReceiveParticle(): void {
    const receiveParticles = this.asciiEmotionService.getReceiveParticles();
    const particleContent = receiveParticles[Math.floor(Math.random() * receiveParticles.length)];
    
    this.particleId++;
    const particle = {
      id: this.particleId,
      content: particleContent,
      x: Math.random() * 80 + 10, // Random x position (10-90%)
      y: 10, // Start at top
      type: 'receive' as const
    };
    
    this.particles.push(particle);
    
    // Remove particle after animation
    setTimeout(() => {
      this.particles = this.particles.filter(p => p.id !== particle.id);
    }, 2000);
  }

  /**
   * Create multiple particles for message send
   */
  createSendParticles(count: number = 3): void {
    for (let i = 0; i < count; i++) {
      setTimeout(() => this.createSendParticle(), i * 100);
    }
  }

  /**
   * Create multiple particles for message receive
   */
  createReceiveParticles(count: number = 3): void {
    for (let i = 0; i < count; i++) {
      setTimeout(() => this.createReceiveParticle(), i * 100);
    }
  }

  ngOnDestroy() {
    // Clean up subscriptions
    if (this.streamSubscription) {
      this.streamSubscription.unsubscribe();
    }
    
    // Clean up emotion subscription
    if (this.emotionSubscription) {
      this.emotionSubscription.unsubscribe();
    }
    
    // Clean up thinking animation
    this.stopThinkingAnimation();
    
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
          this.updateMessage(this.messages.length - 1, {
            ...lastMessage,
            content: lastMessage.content + '\n' + loadingFrame
          });
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

  /**
   * Helper method to add a message to the messages array with proper change detection
   */
  private addMessage(message: ChatMessage): void {
    // Create a new array reference to trigger change detection
    this.messages = [...this.messages, message];
    
    // Force change detection
    this.cdr.detectChanges();
    
    // Notify virtual scroll viewport to recalculate if available
    if (this.viewport) {
      this.viewport.checkViewportSize();
    }
    
    // Scroll to bottom after a brief delay to ensure DOM is updated
    setTimeout(() => this.scrollToBottom(), 50);
  }

  /**
   * Helper method to update a message at a specific index
   */
  private updateMessage(index: number, message: ChatMessage): void {
    const newMessages = [...this.messages];
    newMessages[index] = message;
    this.messages = newMessages;
    this.cdr.detectChanges();
    
    if (this.viewport) {
      this.viewport.checkViewportSize();
    }
  }

  /**
   * Helper method to clear all messages
   */
  private clearMessages(): void {
    this.messages = [];
    this.cdr.detectChanges();
    
    if (this.viewport) {
      this.viewport.checkViewportSize();
    }
  }

  async sendMessage() {
    if (this.newMessage.trim()) {
      // Create chat session if this is the first message and no chat exists
      // OR if we have a temporary chat ID (starts with 'temp-')
      const isTemporaryChat = this.currentChatId && this.currentChatId.startsWith('temp-');
      const tempChatId = isTemporaryChat ? this.currentChatId : null;
      
      if (!this.currentChatId || isTemporaryChat) {
        try {
          // Generate a title from the first message (truncate if too long)
          const messageContent = this.newMessage.trim();
          const chatTitle = messageContent.length > 50 
            ? messageContent.substring(0, 47) + '...' 
            : messageContent;
          
          console.log('Creating new chat session for first message');
          const chatResponse = await firstValueFrom(this.chatService.createChat(chatTitle, 'gpt-5-nano'));
          this.currentChatId = chatResponse.id;
          this.isNewChat = true;
          
          // Update the sidebar with the real chat
          if (this.chatHistorySidebar) {
            if (isTemporaryChat && tempChatId) {
              // Replace the temporary chat with the real one
              this.chatHistorySidebar.replaceTemporaryChat(tempChatId, chatResponse);
            } else {
              // Add the new chat to sidebar
              this.chatHistorySidebar.addOrUpdateChat(chatResponse);
            }
          }
          console.log('Created chat session:', chatResponse.id);
        } catch (error) {
          console.error('Failed to create chat session:', error);
          // Continue without chat ID (messages won't be persisted)
          // If we had a temporary chat, keep using it for UI purposes
          if (!this.currentChatId) {
            // Create a fallback temporary ID
            this.currentChatId = 'temp-fallback-' + Date.now();
          }
        }
      }
      
      // Add to history
      this.messageHistory.unshift(this.newMessage);
      this.historyIndex = -1;
      
      // Add user message
      const userMessage: ChatMessage = {
        role: 'user',
        content: this.newMessage,
        timestamp: new Date().toISOString()
      };
      this.addMessage(userMessage);
      const messageContent = this.newMessage;
      this.newMessage = '';

      // Update chat title if this is a new chat
      if (this.isNewChat && this.currentChatId) {
        this.updateChatTitleFromFirstMessage(this.currentChatId, messageContent);
        this.isNewChat = false;
      }
      
      // Show typing indicator
      this.isTyping = true;
      this.streamingResponse = '';
      
      // Start thinking animation
      this.startThinkingAnimation();
      this.setEmotion('thinking');
      
      // Create send particles
      this.createSendParticles(2);
      
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
            this.stopThinkingAnimation();
            this.setEmotion('success');
            
            // Create receive particles
            this.createReceiveParticles(2);
            
            // Handle special commands that modify UI state
            if (messageContent.toLowerCase() === '/clear' || messageContent.toLowerCase() === '/cls') {
              this.clearMessages();
            }
            
            // Add assistant response
            this.addMessage({
              role: 'assistant',
              content: result.message,
              timestamp: new Date().toISOString(),
              metadata: { commandResult: result }
            });
          },
          error: (error) => {
            this.isTyping = false;
            this.stopThinkingAnimation();
            this.setEmotion('error');
            this.addMessage({
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
        model: 'gpt-5-nano',
        stream: true,
        use_rag: this.ragConfig.useRag,
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
        this.addMessage({
          role: 'assistant',
          content: '',
          timestamp: new Date().toISOString(),
          metadata: { streaming: true, interruptible: true }
        });
        const streamingMessageIndex = this.messages.length - 1;
        
        // Start loading animation (disabled to avoid interfering with streaming)
        // this.startLoadingAnimation();
        
        let completionSources: any[] = [];
        let contextUsed = false;
        let tokenUsage: { prompt_tokens: number, completion_tokens: number, total_tokens: number } | null = null;

        try {

          for await (const event of stream) {
            if (event.type === 'token') {
              fullResponse += event.token;
              displayedResponse += event.token;
              this.streamingResponse = displayedResponse;
              this.cdr.detectChanges();
              const delay = Math.min(
                this.streamingConfig.maxDisplayTime,
                Math.max(this.streamingConfig.minDisplayTime, event.token.length * 5)
              );
              await new Promise(resolve => setTimeout(resolve, delay));

            } else if (event.type === 'complete') {
              completionSources = (event.data.sources || []).map((s: any) => ({
                document_title:   s.source || 'Unknown',
                similarity_score: s.relevance_score || 0,
                chunk_text:       s.content_preview || '',
                document_id:      s.document_id,
                chunk_index:      s.chunk_index,
              }));
              contextUsed = event.data.context_used || false;

              tokenUsage = {
                prompt_tokens:     event.data.usage?.prompt_tokens     ?? event.data.prompt_tokens     ?? 0,
                completion_tokens: event.data.usage?.completion_tokens ?? event.data.completion_tokens ?? 0,
                total_tokens:      event.data.usage?.total_tokens      ?? event.data.total_tokens      ?? 0,
              };
                        }
          }
        } catch (error: any) {
          if (error.name === 'AbortError') {
            // Stream was interrupted by user
            this.updateMessage(streamingMessageIndex, {
              ...this.messages[streamingMessageIndex],
              content: displayedResponse + ' [Interrupted]',
              metadata: { streaming: false, interrupted: true }
            });
            this.streamingResponse = '';
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
        this.updateMessage(streamingMessageIndex, {
          role: 'assistant',
          content: fullResponse,
          timestamp: new Date().toISOString(),
          tokens_used: tokenUsage?.total_tokens ?? undefined,
          model: request.model ?? 'Unknown',
          metadata: {
            streaming: false,
            sources: completionSources,
            context_used: contextUsed,
            token_usage: tokenUsage,  // ✅ ADD THIS
          }
        });
        
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
           this.addMessage({
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
      this.updateMessage(this.messages.length - 1, {
        ...lastMessage,
        content: response
      });
    } else {
      // Add new streaming message
      this.addMessage({
        role: 'assistant',
        content: response,
        timestamp: new Date().toISOString(),
        metadata: { streaming: true }
      });
    }
  }

  /**
   * Generate a chat title from the first message (mimics backend logic).
   */
  private generateChatTitleFromMessage(message: string): string {
    if (message.length > 50) {
      return message.substring(0, 50) + '...';
    }
    return message;
  }

  /**
   * Update the chat title in the sidebar with a typewriter effect.
   * Called when the first user message is sent.
   */
  private updateChatTitleFromFirstMessage(chatId: string, firstMessage: string): void {
    if (!this.chatHistorySidebar) {
      console.warn('Sidebar not available for title update');
      return;
    }
    const title = this.generateChatTitleFromMessage(firstMessage);
    // Ensure the chat exists in sidebar
    const chat: ChatSession = {
      id: chatId,
      user_id: '', // unknown, but not needed for UI
      title: 'New Chat', // placeholder
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      model_used: 'gpt-5-nano',
      metadata: {},
      message_count: 0
    };
    this.chatHistorySidebar.addOrUpdateChat(chat);
    // Start animation
    this.chatHistorySidebar.animateChatTitle(chatId, title, 50);
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
    // Don't create a chat session on page load
    // Chat session will be created when user sends their first message
    console.log('Chat creation deferred until first message');
    
    // We'll still try to load the most recent chat for display purposes
    try {
      const chatsResponse = await firstValueFrom(this.chatService.getChats(1, 1));
      if (chatsResponse.chats && chatsResponse.chats.length > 0) {
        // Set the most recent chat as current for display, but don't load messages yet
        // User can select a different chat from sidebar if they want
        const mostRecentChat = chatsResponse.chats[0];
        this.currentChatId = mostRecentChat.id;
        this.isNewChat = false;
        console.log('Most recent chat available:', mostRecentChat.id);
      } else {
        // No existing chats, we'll create one when user sends first message
        this.currentChatId = null;
        this.isNewChat = true;
      }
    } catch (error) {
      console.error('Error checking for existing chats:', error);
      this.currentChatId = null;
      this.isNewChat = true;
    }
  }

  /**
   * Load more messages for lazy loading
   */
  private async loadMoreMessages() {
    // Don't load messages for temporary chats (they don't exist on backend)
    const isTemporaryChat = this.currentChatId && this.currentChatId.startsWith('temp-');
    if (this.isLoadingMessages || !this.hasMoreMessages || !this.currentChatId || isTemporaryChat) {
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
      this.clearMessages();
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

  /**
   * Handle chat selection from sidebar
   */
  async onChatSelected(chatId: string): Promise<void> {
    console.log('Chat selected:', chatId);
    
    // Don't reload if it's the same chat
    if (this.currentChatId === chatId) {
      return;
    }
    
    this.currentChatId = chatId;
    
    // Reset message state for the new chat
    this.messages = [];
    this.currentPage = 1;
    this.hasMoreMessages = true;
    this.totalMessages = 0;
    
    // Check if this is a temporary chat (starts with 'temp-')
    const isTemporaryChat = chatId.startsWith('temp-');
    
    if (isTemporaryChat) {
      // Temporary chats don't have messages on the backend
      console.log('Selected temporary chat, skipping message load');
      this.isLoadingMessages = false;
      
      // Show a welcome message for new temporary chats
      this.messages.push({
        role: 'assistant',
        content: `New chat session created. Type your first message to begin.`,
        timestamp: new Date().toISOString()
      });
      
      // Scroll to bottom to show the message
      setTimeout(() => this.scrollToBottom(), 100);
      return;
    }
    
    // Show loading state for real chats
    this.isLoadingMessages = true;
    
    try {
      // Load messages for the selected chat
      const response = await firstValueFrom(
        this.chatService.getChatMessages(chatId, this.currentPage, this.pageSize)
      );
      
      this.messages = response.messages;
      this.totalMessages = response.total;
      this.hasMoreMessages = this.messages.length < this.totalMessages;
      
      if (this.hasMoreMessages) {
        this.currentPage++;
      }
      
      // Add a system message indicating chat switch
      if (this.messages.length === 0) {
        this.messages.push({
          role: 'assistant',
          content: `Started new chat session. Type your first message to begin.`,
          timestamp: new Date().toISOString()
        });
      } else {
        this.messages.unshift({
          role: 'system',
          content: `Loaded chat history with ${this.messages.length} messages.`,
          timestamp: new Date().toISOString()
        });
      }
      
      // Scroll to bottom to show latest messages
      setTimeout(() => this.scrollToBottom(), 100);
      
    } catch (error) {
      console.error('Error loading chat messages:', error);
      // Fallback to demo messages
      this.messages = [
        { 
          role: 'assistant', 
          content: `Switched to chat: ${chatId}. Unable to load chat history from server.`, 
          timestamp: new Date().toISOString() 
        }
      ];
    } finally {
      this.isLoadingMessages = false;
    }
  }
}