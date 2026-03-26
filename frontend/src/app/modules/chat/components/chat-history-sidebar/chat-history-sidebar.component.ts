import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { ChatService, ChatSession } from '../../../../core/services/chat.service';

@Component({
  selector: 'app-chat-history-sidebar',
  templateUrl: './chat-history-sidebar.component.html',
  styleUrls: ['./chat-history-sidebar.component.scss']
})
export class ChatHistorySidebarComponent implements OnInit {
  @Input() isOpen = true;
  @Output() isOpenChange = new EventEmitter<boolean>();
  @Output() chatSelected = new EventEmitter<string>();
  
  chats: ChatSession[] = [];
  loading = false;
  error: string | null = null;
  selectedChatId: string | null = null;

  constructor(private chatService: ChatService) {}

  ngOnInit() {
    this.loadChats();
  }

  async loadChats() {
    this.loading = true;
    this.error = null;
    
    try {
      const response = await this.chatService.getChats(1, 20).toPromise();
      this.chats = response.chats;
      
      // Select the most recent chat if none selected
      if (this.chats.length > 0 && !this.selectedChatId) {
        this.selectChat(this.chats[0].id);
      }
    } catch (error) {
      console.error('Error loading chats:', error);
      this.error = 'Failed to load chat history';
      // Load mock data for demonstration
      this.loadMockChats();
    } finally {
      this.loading = false;
    }
  }

  selectChat(chatId: string) {
    this.selectedChatId = chatId;
    this.chatSelected.emit(chatId);
  }

  createNewChat() {
    this.chatService.createChat('New Chat', 'gpt-4').subscribe({
      next: (chat) => {
        this.chats.unshift(chat);
        this.selectChat(chat.id);
      },
      error: (error) => {
        console.error('Error creating chat:', error);
        // Create mock chat for demonstration
        const mockChat: ChatSession = {
          id: 'mock-' + Date.now(),
          user_id: 'user-1',
          title: 'New Chat',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          model_used: 'gpt-4',
          metadata: {},
          message_count: 0
        };
        this.chats.unshift(mockChat);
        this.selectChat(mockChat.id);
      }
    });
  }

  deleteChat(chatId: string, event: Event) {
    event.stopPropagation();
    
    if (confirm('Are you sure you want to delete this chat? This action cannot be undone.')) {
      this.chatService.deleteChat(chatId).subscribe({
        next: () => {
          this.chats = this.chats.filter(chat => chat.id !== chatId);
          if (this.selectedChatId === chatId && this.chats.length > 0) {
            this.selectChat(this.chats[0].id);
          } else if (this.chats.length === 0) {
            this.selectedChatId = null;
          }
        },
        error: (error) => {
          console.error('Error deleting chat:', error);
          alert('Failed to delete chat. Please try again.');
        }
      });
    }
  }

  toggleSidebar() {
    this.isOpen = !this.isOpen;
    this.isOpenChange.emit(this.isOpen);
  }

  formatDate(dateString: string): string {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) {
      return 'Today';
    } else if (diffDays === 1) {
      return 'Yesterday';
    } else if (diffDays < 7) {
      return `${diffDays} days ago`;
    } else {
      return date.toLocaleDateString();
    }
  }

  private loadMockChats() {
    this.chats = [
      {
        id: 'chat-1',
        user_id: 'user-1',
        title: 'RAG System Discussion',
        created_at: new Date(Date.now() - 3600000).toISOString(),
        updated_at: new Date(Date.now() - 1800000).toISOString(),
        model_used: 'gpt-4',
        metadata: {},
        message_count: 12
      },
      {
        id: 'chat-2',
        user_id: 'user-1',
        title: 'Document Processing Questions',
        created_at: new Date(Date.now() - 86400000).toISOString(),
        updated_at: new Date(Date.now() - 43200000).toISOString(),
        model_used: 'claude-3',
        metadata: {},
        message_count: 8
      },
      {
        id: 'chat-3',
        user_id: 'user-1',
        title: 'API Integration Help',
        created_at: new Date(Date.now() - 172800000).toISOString(),
        updated_at: new Date(Date.now() - 86400000).toISOString(),
        model_used: 'gemini-pro',
        metadata: {},
        message_count: 5
      }
    ];
  }
}