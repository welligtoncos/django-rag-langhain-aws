import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms'; 
import { Produto, RAGResponse, RagService } from '../services/rag/rag.service';

interface Message {
  id: number;
  type: 'user' | 'assistant';
  content: string;
  produtos?: Produto[];
  timestamp: Date;
}

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent {
  messages: Message[] = [];
  inputMessage: string = '';
  isLoading: boolean = false;

  suggestions = [
    'Quero uma sandália confortável',
    'Produtos em promoção',
    'Tênis para corrida',
    'Produtos até 100 reais'
  ];

  constructor(private ragService: RagService) {}

  sendMessage(message?: string) {
    const text = message || this.inputMessage.trim();
    
    if (!text || this.isLoading) return;

    // Adicionar mensagem do usuário
    this.messages.push({
      id: Date.now(),
      type: 'user',
      content: text,
      timestamp: new Date()
    });

    this.inputMessage = '';
    this.isLoading = true;

    // Chamar API
    this.ragService.query({ query: text, limit: 5 }).subscribe({
      next: (response: RAGResponse) => {
        this.messages.push({
          id: Date.now() + 1,
          type: 'assistant',
          content: response.resposta,
          produtos: response.produtos,
          timestamp: new Date()
        });
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Erro:', error);
        this.messages.push({
          id: Date.now() + 1,
          type: 'assistant',
          content: '❌ Erro ao processar sua mensagem. Tente novamente.',
          timestamp: new Date()
        });
        this.isLoading = false;
      }
    });
  }

  onKeyPress(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendMessage();
    }
  }

  get showWelcome(): boolean {
    return this.messages.length === 0;
  }
}