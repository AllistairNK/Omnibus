import { Component, OnInit, AfterViewChecked, ElementRef, ViewChild, OnDestroy } from '@angular/core';
import { ChatService, ChatMessage, ChatCompletionRequest } from '../../../../core/services/chat.service';
import { Subscription } from 'rxjs';
import { firstValueFrom } from 'rxjs';
@Component({
  selector: 'app-chat',
  templateUrl: './chat.component.html',
  styleUrls: ['./chat.component.scss']
})
export class ChatComponent implements OnInit, AfterViewChecked, OnDestroy {
  @ViewChild('terminalOutput') private terminalOutput!: ElementRef;

  messages: ChatMessage[] = [
    { role: 'assistant', content: 'Hello! I am your AI assistant. How can I help you today?', timestamp: new Date().toISOString() },
    { role: 'user', content: 'Tell me about RAG.', timestamp: new Date().toISOString() },
    { role: 'assistant', content: 'RAG stands for Retrieval-Augmented Generation. It combines retrieval of relevant documents with generative AI to produce accurate, context-aware responses.', timestamp: new Date().toISOString(), metadata: { sources: [
      { document_id: 'doc1', document_title: 'RAG Overview.pdf', chunk_text: 'Retrieval-Augmented Generation (RAG) enhances large language models by retrieving relevant documents from a knowledge base.', similarity_score: 0.95 },
      { document_id: 'doc2', document_title: 'AI Research Paper.docx', chunk_text: 'RAG models outperform standard LLMs on knowledge-intensive tasks by incorporating external knowledge.', similarity_score: 0.87 }
    ]} }
  ];
  newMessage = '';
  isTyping = false;
  messageHistory: string[] = [];
  historyIndex = -1;
  currentChatId: string | null = null;
  streamingResponse = '';
  private streamSubscription?: Subscription;
  
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

  constructor(private chatService: ChatService) {}

  ngOnInit() {
    // Initialize with some command history
    this.messageHistory = ['/help', 'Tell me about RAG', 'What is vector search?'];
    
    // Create a new chat session or load existing one
    this.createOrLoadChat();
    
    // Load saved RAG settings
    this.loadRagSettings();
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
      
      // Handle commands locally
      if (messageContent.startsWith('/')) {
        setTimeout(() => {
          this.isTyping = false;
          const response = this.handleCommand(messageContent);
          this.messages.push({
            role: 'assistant',
            content: response,
            timestamp: new Date().toISOString()
          });
        }, 500);
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
        // Use the async generator for streaming
        const stream = this.chatService.streamMessage(request);
        let fullResponse = '';
        
        for await (const token of stream) {
          this.streamingResponse += token;
          fullResponse += token;
          
          // Update the UI with the streaming response
          this.updateStreamingResponse(fullResponse);
        }
        
        // Streaming complete
        this.isTyping = false;
        this.streamingResponse = '';
        this.messages.push({
          role: 'assistant',
          content: fullResponse,
          timestamp: new Date().toISOString()
        });
        
      } catch (error) {
        console.error('Error in chat completion:', error);
        this.isTyping = false;
        this.streamingResponse = '';
        
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

  private async createOrLoadChat() {
    try {
      const response = await firstValueFrom(this.chatService.createChat('New Chat', 'gpt-4'));
      this.currentChatId = response.id;
    } catch (error) {
      console.error('Error creating chat session:', error);
      // Continue without chat ID (messages won't be persisted)
    }
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
      // Simple autocomplete for commands
      if (this.newMessage.startsWith('/')) {
        const commands = ['/help', '/clear', '/model', '/documents', '/about'];
        const matching = commands.find(cmd => cmd.startsWith(this.newMessage));
        if (matching) {
          this.newMessage = matching;
        }
      }
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
}