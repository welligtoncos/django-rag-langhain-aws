import { Component, ElementRef, ViewChild, AfterViewChecked, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Nl2brPipe } from './pipes/nl2br.pipe'; // ← ADICIONAR
import { 
  RagService, 
  RAGResponse, 
  ProdutoMinimal,
  RAGStats,
  HealthCheck
} from '../services/rag/rag.service';

// ============================================
// INTERFACES
// ============================================

interface Message {
  id: number;
  type: 'user' | 'assistant' | 'system';
  content: string;
  produtos?: ProdutoMinimal[];
  timestamp: Date;
  loading?: boolean;
  error?: boolean;
  tempo_processamento?: number;
}

interface Suggestion {
  text: string;
  icon: string;
  category?: string;
}

// ============================================
// COMPONENT
// ============================================

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule, Nl2brPipe], // ← ADICIONAR Nl2brPipe
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent implements OnInit, AfterViewChecked {
  
  // ============================================
  // PROPRIEDADES
  // ============================================
  
  messages: Message[] = [];
  inputMessage: string = '';
  isLoading: boolean = false;
  apiConnected: boolean = false;
  stats: RAGStats | null = null;
  
  // Scroll automático
  @ViewChild('messagesContainer') 
  private messagesContainer!: ElementRef;
  private shouldScrollToBottom = false;

  // Sugestões inteligentes
  suggestions: Suggestion[] = [
    { text: 'Quero uma camiseta branca', icon: '👕', category: 'Roupas' },
    { text: 'Produtos em promoção', icon: '🔥', category: 'Promoções' },
    { text: 'Perfume masculino amadeirado', icon: '🌸', category: 'Beleza' },
    { text: 'Tênis até 200 reais', icon: '👟', category: 'Calçados' },
    { text: 'Eletrônicos para fitness', icon: '⌚', category: 'Eletrônicos' },
    { text: 'Moletom confortável', icon: '🧥', category: 'Roupas' }
  ];

  private readonly MAX_HISTORY = 50;

  constructor(public ragService: RagService) {}

  // ============================================
  // LIFECYCLE HOOKS
  // ============================================

  ngOnInit() {
    this.checkAPIConnection();
    this.loadStats();
    this.loadMessagesFromLocalStorage();
  }

  ngAfterViewChecked() {
    if (this.shouldScrollToBottom) {
      this.scrollToBottom();
      this.shouldScrollToBottom = false;
    }
  }

  // ============================================
  // INICIALIZAÇÃO
  // ============================================

  checkAPIConnection() {
    this.ragService.healthCheck().subscribe({
      next: (health: HealthCheck) => {
        this.apiConnected = health.status === 'ok';
        console.log('✅ API conectada:', health);
      },
      error: (error) => {
        this.apiConnected = false;
        console.error('❌ API desconectada:', error);
        this.showSystemMessage(
          '⚠️ Não foi possível conectar com o servidor. Verifique sua conexão.',
          true
        );
      }
    });
  }

  loadStats() {
    this.ragService.getRAGStats().subscribe({
      next: (stats: RAGStats) => {
        this.stats = stats;
        console.log('📊 Stats carregadas:', stats);
      },
      error: (error) => console.error('Erro ao carregar stats:', error)
    });
  }

  // ============================================
  // ENVIO DE MENSAGENS
  // ============================================

  sendMessage(message?: string) {
    const text = message || this.inputMessage.trim();
    
    if (!text || this.isLoading) return;

    if (text.length < 3) {
      this.showSystemMessage('⚠️ Por favor, digite uma mensagem mais descritiva.', true);
      return;
    }

    if (text.length > 500) {
      this.showSystemMessage('⚠️ Mensagem muito longa. Máximo: 500 caracteres.', true);
      return;
    }

    this.addMessage({
      id: this.generateId(),
      type: 'user',
      content: text,
      timestamp: new Date()
    });

    this.inputMessage = '';
    this.isLoading = true;

    this.ragService.query({ query: text, limit: 6 }).subscribe({
      next: (response: RAGResponse) => {
        this.addMessage({
          id: this.generateId(),
          type: 'assistant',
          content: response.resposta,
          produtos: response.produtos,
          timestamp: new Date(),
          tempo_processamento: response.tempo_processamento
        });
        this.isLoading = false;
      },
      error: (error) => {
        console.error('❌ Erro na consulta RAG:', error);
        
        let errorMessage = '❌ Desculpe, ocorreu um erro ao processar sua solicitação.';
        
        if (error.message.includes('503')) {
          errorMessage = '⚠️ Serviço RAG temporariamente indisponível. Tente novamente.';
        } else if (error.message.includes('timeout')) {
          errorMessage = '⏱️ Tempo limite excedido. Tente uma consulta mais simples.';
        }

        this.addMessage({
          id: this.generateId(),
          type: 'assistant',
          content: errorMessage,
          timestamp: new Date(),
          error: true
        });
        
        this.isLoading = false;
      }
    });
  }

  private addMessage(message: Message) {
    this.messages.push(message);
    
    if (this.messages.length > this.MAX_HISTORY) {
      this.messages = this.messages.slice(-this.MAX_HISTORY);
    }
    
    this.shouldScrollToBottom = true;
    this.saveMessagesToLocalStorage();
  }

  private showSystemMessage(content: string, error: boolean = false) {
    this.addMessage({
      id: this.generateId(),
      type: 'system',
      content,
      timestamp: new Date(),
      error
    });
  }

  // ============================================
  // EVENTOS DE INPUT
  // ============================================

  onKeyPress(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendMessage();
    }
  }

  sendSuggestion(suggestion: string) {
    this.inputMessage = suggestion;
    this.sendMessage();
  }

  // ============================================
  // AÇÕES DE PRODUTOS
  // ============================================

  verDetalhes(produtoId: number) {
    console.log('Ver detalhes:', produtoId);
    this.ragService.getProduct(produtoId).subscribe({
      next: (produto) => {
        console.log('Produto completo:', produto);
        // Implementar modal ou navegação
      },
      error: (error) => console.error('Erro ao buscar produto:', error)
    });
  }

  buscarSimilares(produtoId: number, produtoNome: string) {
    const query = `Produtos similares a ${produtoNome}`;
    this.inputMessage = query;
    this.sendMessage();
  }

  adicionarAoCarrinho(produto: ProdutoMinimal) {
    console.log('Adicionar ao carrinho:', produto);
    this.showSystemMessage(`✅ "${produto.nome}" adicionado ao carrinho!`);
  }

  // ============================================
  // TRATAMENTO DE IMAGEM
  // ============================================

  onImageError(event: Event) {
    const img = event.target as HTMLImageElement;
    img.src = 'assets/no-image.png';
  }

  // ============================================
  // UTILIDADES
  // ============================================

  formatarPreco(valor: number): string {
    return this.ragService.formatarPreco(valor);
  }

  calcularDesconto(preco: number, precoPromocional?: number): number {
    if (!precoPromocional) return 0;
    return this.ragService.calcularDesconto(preco, precoPromocional);
  }

  temPromocao(produto: ProdutoMinimal): boolean {
    return this.ragService.temPromocao(produto);
  }

  temImagem(produto: ProdutoMinimal): boolean {
    return !!produto.imagem_completa;
  }

  getImagemUrl(produto: ProdutoMinimal): string {
    return produto.imagem_completa || 'assets/no-image.png';
  }

  estoqueBaixo(produto: ProdutoMinimal): boolean {
    return this.ragService.estoqueBaixo(produto);
  }

  getAvaliacaoClass(avaliacao?: number): string {
    if (!avaliacao) return 'no-rating';
    if (avaliacao >= 4.5) return 'excellent';
    if (avaliacao >= 4.0) return 'good';
    if (avaliacao >= 3.0) return 'average';
    return 'poor';
  }

  formatarTempo(segundos?: number): string {
    if (!segundos) return '';
    if (segundos < 1) return `${(segundos * 1000).toFixed(0)}ms`;
    return `${segundos.toFixed(2)}s`;
  }

  private scrollToBottom(): void {
    try {
      if (this.messagesContainer) {
        const element = this.messagesContainer.nativeElement;
        element.scrollTop = element.scrollHeight;
      }
    } catch (err) {
      console.error('Erro ao fazer scroll:', err);
    }
  }

  private generateId(): number {
    return Date.now() + Math.random();
  }

  limparChat() {
    if (confirm('Deseja limpar todo o histórico de conversas?')) {
      this.messages = [];
      localStorage.removeItem('chat-messages');
    }
  }

  private saveMessagesToLocalStorage() {
    try {
      const messagesToSave = this.messages.slice(-20);
      localStorage.setItem('chat-messages', JSON.stringify(messagesToSave));
    } catch (error) {
      console.error('Erro ao salvar mensagens:', error);
    }
  }

  private loadMessagesFromLocalStorage() {
    try {
      const saved = localStorage.getItem('chat-messages');
      if (saved) {
        this.messages = JSON.parse(saved);
        this.shouldScrollToBottom = true;
      }
    } catch (error) {
      console.error('Erro ao carregar mensagens:', error);
    }
  }

  exportarConversa() {
    const conversaTexto = this.messages.map(m => 
      `[${m.timestamp.toLocaleString()}] ${m.type.toUpperCase()}: ${m.content}`
    ).join('\n\n');

    const blob = new Blob([conversaTexto], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `conversa-${Date.now()}.txt`;
    link.click();
    window.URL.revokeObjectURL(url);
  }

  // ============================================
  // GETTERS
  // ============================================

  get showWelcome(): boolean {
    return this.messages.length === 0 && !this.isLoading;
  }

  get hasMessages(): boolean {
    return this.messages.length > 0;
  }

  get canSend(): boolean {
    return !this.isLoading && this.inputMessage.trim().length > 0;
  }

  get totalProdutos(): number {
    return this.stats?.total_produtos || 0;
  }

  get categorias(): string[] {
    return this.stats?.categorias || [];
  }

  /**
   * Formata avaliação (garante que é número)
   */
  formatarAvaliacao(avaliacao?: number | string): string {
    if (!avaliacao) return 'N/A';
    const nota = typeof avaliacao === 'string' ? parseFloat(avaliacao) : avaliacao;
    if (isNaN(nota)) return 'N/A';
    return nota.toFixed(1);
  }
}