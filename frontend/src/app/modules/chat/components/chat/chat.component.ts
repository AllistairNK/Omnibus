import { Component, OnInit, AfterViewChecked, ElementRef, ViewChild } from '@angular/core';

@Component({
  selector: 'app-chat',
  templateUrl: './chat.component.html',
  styleUrls: ['./chat.component.scss']
})
export class ChatComponent implements OnInit, AfterViewChecked {
  @ViewChild('terminalOutput') private terminalOutput!: ElementRef;

  messages = [
    { sender: 'bot', text: 'Hello! I am your AI assistant. How can I help you today?', timestamp: new Date() },
    { sender: 'user', text: 'Tell me about RAG.', timestamp: new Date() },
    { sender: 'bot', text: 'RAG stands for Retrieval-Augmented Generation. It combines retrieval of relevant documents with generative AI to produce accurate, context-aware responses.', timestamp: new Date() }
  ];
  newMessage = '';
  isTyping = false;
  messageHistory: string[] = [];
  historyIndex = -1;

  ngOnInit() {
    // Initialize with some command history
    this.messageHistory = ['/help', 'Tell me about RAG', 'What is vector search?'];
  }

  ngAfterViewChecked() {
    this.scrollToBottom();
  }

  scrollToBottom(): void {
    try {
      if (this.terminalOutput) {
        this.terminalOutput.nativeElement.scrollTop = this.terminalOutput.nativeElement.scrollHeight;
      }
    } catch(err) { }
  }

  sendMessage() {
    if (this.newMessage.trim()) {
      // Add to history
      this.messageHistory.unshift(this.newMessage);
      this.historyIndex = -1;
      
      // Add user message
      this.messages.push({ sender: 'user', text: this.newMessage, timestamp: new Date() });
      const userMessage = this.newMessage;
      this.newMessage = '';
      
      // Show typing indicator
      this.isTyping = true;
      
      // Simulate bot response after a delay
      setTimeout(() => {
        this.isTyping = false;
        let response = '';
        
        // Handle commands
        if (userMessage.startsWith('/')) {
          response = this.handleCommand(userMessage);
        } else {
          // Generate a simulated response based on input
          response = this.generateResponse(userMessage);
        }
        
        this.messages.push({ sender: 'bot', text: response, timestamp: new Date() });
      }, 1000 + Math.random() * 1000);
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
}