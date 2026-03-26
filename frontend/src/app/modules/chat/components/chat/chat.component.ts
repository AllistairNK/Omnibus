import { Component } from '@angular/core';

@Component({
  selector: 'app-chat',
  templateUrl: './chat.component.html',
  styleUrls: ['./chat.component.scss']
})
export class ChatComponent {
  messages = [
    { sender: 'bot', text: 'Hello! I am your AI assistant. How can I help you today?', timestamp: new Date() },
    { sender: 'user', text: 'Tell me about RAG.', timestamp: new Date() },
    { sender: 'bot', text: 'RAG stands for Retrieval-Augmented Generation. It combines retrieval of relevant documents with generative AI to produce accurate, context-aware responses.', timestamp: new Date() }
  ];
  newMessage = '';

  sendMessage() {
    if (this.newMessage.trim()) {
      this.messages.push({ sender: 'user', text: this.newMessage, timestamp: new Date() });
      this.newMessage = '';
      // Simulate bot response after a delay
      setTimeout(() => {
        this.messages.push({ sender: 'bot', text: 'I received your message: ' + this.newMessage, timestamp: new Date() });
      }, 1000);
    }
  }
}