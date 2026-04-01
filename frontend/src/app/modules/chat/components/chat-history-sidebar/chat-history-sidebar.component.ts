import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { ChatService, ChatSession } from '../../../../core/services/chat.service';
import { firstValueFrom } from 'rxjs';
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
  currentPage = 1;
  pageSize = 10;
  totalChats = 0;
  totalPages = 1;

  // Animation state for typewriter effect
  private animatedTitles: Map<string, { displayedTitle: string, targetTitle: string, intervalId?: any }> = new Map();

  constructor(private chatService: ChatService) {}

  /**
   * Start a typewriter animation for a chat title.
   * @param chatId The chat ID to animate
   * @param targetTitle The final title to display
   * @param speedMs Delay between characters in milliseconds (default 50)
   */
  animateChatTitle(chatId: string, targetTitle: string, speedMs: number = 50): void {
    // Stop any existing animation for this chat
    this.stopAnimation(chatId);

    // Initialize displayed title as empty
    this.animatedTitles.set(chatId, {
      displayedTitle: '',
      targetTitle,
      intervalId: undefined
    });

    let index = 0;
    const intervalId = setInterval(() => {
      const entry = this.animatedTitles.get(chatId);
      if (!entry) {
        clearInterval(intervalId);
        return;
      }
      if (index < targetTitle.length) {
        entry.displayedTitle = targetTitle.substring(0, index + 1);
        index++;
        // Update the chat title in the chats array for UI
        const chat = this.chats.find(c => c.id === chatId);
        if (chat) {
          chat.title = entry.displayedTitle;
        }
      } else {
        // Animation complete
        clearInterval(intervalId);
        entry.intervalId = undefined;
      }
    }, speedMs);

    const entry = this.animatedTitles.get(chatId);
    if (entry) {
      entry.intervalId = intervalId;
    }
  }

  /**
   * Stop animation for a chat.
   */
  private stopAnimation(chatId: string): void {
    const entry = this.animatedTitles.get(chatId);
    if (entry?.intervalId) {
      clearInterval(entry.intervalId);
    }
    this.animatedTitles.delete(chatId);
  }

  /**
   * Get the displayed title for a chat (with animation if applicable).
   */
  getDisplayedTitle(chat: ChatSession): string {
    const entry = this.animatedTitles.get(chat.id);
    if (entry) {
      return entry.displayedTitle || chat.title;
    }
    return chat.title;
  }

  /**
   * Add or update a chat in the local list (for real-time updates).
   */
  addOrUpdateChat(chat: ChatSession): void {
    const index = this.chats.findIndex(c => c.id === chat.id);
    if (index >= 0) {
      // Update existing chat
      this.chats[index] = chat;
    } else {
      // Add new chat at the beginning
      this.chats.unshift(chat);
      this.totalChats++;
      this.totalPages = Math.ceil(this.totalChats / this.pageSize);
    }
  }

  /**
   * Replace a temporary chat with a real chat session.
   * This is used when a temporary chat (created locally) is persisted to the backend.
   */
  replaceTemporaryChat(tempChatId: string, realChat: ChatSession): void {
    const tempIndex = this.chats.findIndex(c => c.id === tempChatId);
    if (tempIndex >= 0) {
      // Replace the temporary chat with the real one
      this.chats[tempIndex] = realChat;
      console.log('Replaced temporary chat', tempChatId, 'with real chat', realChat.id);
      
      // If the temporary chat was selected, update the selection
      if (this.selectedChatId === tempChatId) {
        this.selectedChatId = realChat.id;
      }
    } else {
      // If temporary chat not found, just add the real chat
      this.addOrUpdateChat(realChat);
    }
  }

  ngOnInit() {
    this.loadChats();
  }

  async loadChats() {
  this.loading = true;
  this.error = null;
  
  try {
    const response = await firstValueFrom(
      this.chatService.getChats(this.currentPage, this.pageSize)  // use currentPage, not hardcoded 1
    );
    this.chats = response.chats;
    this.totalChats = response.total;
    this.totalPages = Math.ceil(response.total / this.pageSize); // instead of response.page_size
    
    if (this.chats.length > 0 && !this.selectedChatId) {
      this.selectChat(this.chats[0].id);
    }
  } catch (error) {
    console.error('Error loading chats:', error);
    this.error = 'Failed to load chat history';
    this.loadMockChats();
  } finally {
    this.loading = false;
  }
}

goToPage(page: number) {
  if (page < 1 || page > this.totalPages) return;
  this.currentPage = page;
  this.loadChats();
}

  selectChat(chatId: string) {
    this.selectedChatId = chatId;
    this.chatSelected.emit(chatId);
  }

createNewChat() {
  // Create a temporary chat session locally without hitting the backend
  // The chat will be created on the backend only when the user sends their first message
  const tempChatId = 'temp-' + Date.now();
  const now = new Date().toISOString();
  
  const tempChat: ChatSession = {
    id: tempChatId,
    user_id: 'temp-user', // Placeholder until real user ID is available
    title: 'New Chat',
    created_at: now,
    updated_at: now,
    model_used: 'gpt-5-nano',
    metadata: {
      isTemporary: true,
      pendingCreation: true
    },
    message_count: 0
  };
  
  // Add temporary chat to the top of the list
  this.chats.unshift(tempChat);
  this.totalChats++;
  this.totalPages = Math.ceil(this.totalChats / this.pageSize);
  
  // Select the temporary chat
  this.selectChat(tempChatId);
  
  console.log('Created temporary chat session:', tempChatId, 'Backend creation deferred until first message');
}

deleteChat(chatId: string, event: Event) {
  event.stopPropagation();
  
  if (confirm('Are you sure you want to delete this chat? This action cannot be undone.')) {
    // Check if this is a temporary chat (starts with 'temp-')
    const isTemporaryChat = chatId.startsWith('temp-');
    
    if (isTemporaryChat) {
      // Temporary chats don't exist on backend, just remove from local list
      this.removeChatFromList(chatId);
      console.log('Deleted temporary chat:', chatId);
    } else {
      // Real chat - delete from backend
      this.chatService.deleteChat(chatId).subscribe({
        next: () => {
          this.removeChatFromList(chatId);
        },
        error: (error) => {
          console.error('Error deleting chat:', error);
          alert('Failed to delete chat. Please try again.');
        }
      });
    }
  }
}

/**
 * Remove a chat from the local list (common logic for both temporary and real chats)
 */
private removeChatFromList(chatId: string): void {
  this.chats = this.chats.filter(chat => chat.id !== chatId);
  this.totalChats--;
  this.totalPages = Math.ceil(this.totalChats / this.pageSize);

  if (this.selectedChatId === chatId) {
    this.selectedChatId = null;
    if (this.chats.length > 0) {
      this.selectChat(this.chats[0].id);
    }
  }

  // If current page is now empty (deleted last item on page), go back one
  if (this.chats.length === 0 && this.currentPage > 1) {
    this.goToPage(this.currentPage - 1);
  }
}

  toggleSidebar() {
    this.isOpen = !this.isOpen;
    this.isOpenChange.emit(this.isOpen);
  }

  /**
   * Refresh the chat list
   */
  refreshChats() {
    this.loadChats();
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
        model_used: 'gpt-5-nano',
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