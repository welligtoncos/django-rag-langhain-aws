import { Injectable } from '@angular/core';
import { HttpClient, HttpParams, HttpHeaders } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError, map, retry } from 'rxjs/operators';
import { environment } from '../../environments/environment';

// ============================================
// INTERFACES - MODELOS DE DADOS
// ============================================

/**
 * Produto completo (detalhes)
 */
export interface Produto {
  id: number;
  nome: string;
  categoria: string;
  subcategoria?: string;
  preco: number;
  preco_promocional?: number;
  marca?: string;
  cor?: string;
  tamanho?: string;
  material?: string;
  estoque: number;
  descricao?: string;
  especificacoes?: string;
  avaliacao?: number;
  num_avaliacoes?: number;
  peso?: number;
  dimensoes?: string;
  
  // Campos de imagem
  imagem?: string;
  imagem_url?: string;
  imagem_completa?: string;
  imagem_thumbnail?: string;
  thumbnail_url?: string;
  tem_imagem?: boolean;
  
  // Metadados
  score?: number;
  score_percentual?: string;
  data_cadastro?: string;
  data_atualizacao?: string;
}

/**
 * Produto simplificado (listagens)
 */
export interface ProdutoList {
  id: number;
  nome: string;
  categoria: string;
  preco: number;
  preco_promocional?: number;
  marca?: string;
  estoque: number;
  avaliacao?: number;
  imagem_completa?: string;
  thumbnail_url?: string;
}

/**
 * Produto minimal (RAG responses)
 */
export interface ProdutoMinimal {
  id: number;
  nome: string;
  preco: number;
  preco_promocional?: number;
  marca?: string;
  avaliacao?: number;
  estoque: number;
  imagem_completa?: string;
  score?: number;              // ← ADICIONAR
  score_percentual?: string;   // ← ADICIONAR
}

/**
 * Resposta paginada de produtos
 */
export interface ProdutosResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: ProdutoList[];
}

/**
 * Consulta RAG
 */
export interface RAGQuery {
  query: string;
  limit?: number;
}

/**
 * Resposta RAG
 */
export interface RAGResponse {
  query: string;
  resposta: string;
  produtos_encontrados: number;
  produtos: ProdutoMinimal[];
  tempo_processamento: number;
}

/**
 * Busca vetorial simples
 */
export interface SearchResponse {
  query: string;
  total: number;
  produtos: ProdutoMinimal[];
  tempo_processamento: number;
}

/**
 * Estatísticas RAG
 */
export interface RAGStats {
  total_produtos: number;
  total_embeddings: number;
  dimensao_vetores: number;
  categorias: string[];
  total_categorias: number;
  marcas: string[];
  total_marcas: number;
  preco_minimo: number;
  preco_maximo: number;
  preco_medio: number;
  produtos_em_estoque: number;
  produtos_com_imagem: number;
  avaliacao_media: number;
  arquivos?: {
    catalogo: string;
    vectors: string;
  };
}

/**
 * Estatísticas de produtos
 */
export interface ProdutoStats {
  total_produtos: number;
  produtos_em_estoque: number;
  produtos_em_promocao: number;
  produtos_com_imagem: number;
  preco_medio: number;
  preco_min: number;
  preco_max: number;
  avaliacao_media: number;
  categorias: Array<{ categoria: string; total: number }>;
  marcas_top: Array<{ marca: string; total: number }>;
}

/**
 * Filtros de produtos
 */
export interface ProdutoFiltros {
  categoria?: string;
  subcategoria?: string;
  marca?: string;
  preco_min?: number;
  preco_max?: number;
  cor?: string;
  tamanho?: string;
  em_estoque?: boolean;
  promocao?: boolean;
  search?: string;
  ordenar?: 'preco_asc' | 'preco_desc' | 'nome' | 'avaliacao' | 'mais_novo' | 'mais_vendido';
  page?: number;
  page_size?: number;
}

/**
 * Health check
 */
export interface HealthCheck {
  status: string;
  message: string;
  version: string;
  services?: {
    database: string;
    rag: string;
  };
  produtos_catalogados?: number;
}

// ============================================
// SERVIÇO RAG
// ============================================

@Injectable({
  providedIn: 'root'
})
export class RagService {
  private apiUrl = environment.apiUrl;
  private readonly RETRY_COUNT = 2;
  private readonly TIMEOUT = 30000; // 30 segundos

  constructor(private http: HttpClient) {
    console.log('🔧 RAG Service inicializado');
    console.log('📡 API URL:', this.apiUrl);
  }

  // ============================================
  // CONSULTAS RAG
  // ============================================

  /**
   * Consulta RAG principal (com geração de resposta)
   */
  query(data: RAGQuery): Observable<RAGResponse> {
    console.log('🔍 RAG Query:', data);
    return this.http.post<RAGResponse>(`${this.apiUrl}/rag/query/`, data)
      .pipe(
        retry(this.RETRY_COUNT),
        catchError(this.handleError)
      );
  }

  /**
   * Busca vetorial simples (sem geração de resposta)
   * Mais rápido que query()
   */
  search(query: string, limit: number = 5): Observable<SearchResponse> {
    const params = new HttpParams()
      .set('q', query)
      .set('limit', limit.toString());

    return this.http.get<SearchResponse>(`${this.apiUrl}/rag/search/`, { params })
      .pipe(
        retry(this.RETRY_COUNT),
        catchError(this.handleError)
      );
  }

  /**
   * Estatísticas do sistema RAG
   */
  getRAGStats(): Observable<RAGStats> {
    return this.http.get<RAGStats>(`${this.apiUrl}/rag/stats/`)
      .pipe(catchError(this.handleError));
  }

  // ============================================
  // CRUD DE PRODUTOS
  // ============================================

  /**
   * Lista produtos com filtros e paginação
   */
  getProducts(filtros?: ProdutoFiltros): Observable<ProdutosResponse> {
    let params = new HttpParams();

    if (filtros) {
      Object.keys(filtros).forEach(key => {
        const value = (filtros as any)[key];
        if (value !== undefined && value !== null && value !== '') {
          params = params.set(key, value.toString());
        }
      });
    }

    return this.http.get<ProdutosResponse>(`${this.apiUrl}/rag/produtos/`, { params })
      .pipe(
        retry(this.RETRY_COUNT),
        catchError(this.handleError)
      );
  }

  /**
   * Lista todos os produtos (sem paginação)
   */
  getAllProducts(): Observable<ProdutoList[]> {
    return this.getProducts({ page_size: 1000 }).pipe(
      map(response => response.results)
    );
  }

  /**
   * Busca produto por ID
   */
  getProduct(id: number): Observable<Produto> {
    return this.http.get<Produto>(`${this.apiUrl}/rag/produtos/${id}/`)
      .pipe(
        retry(this.RETRY_COUNT),
        catchError(this.handleError)
      );
  }

  /**
   * Cria novo produto
   */
  createProduct(produto: Partial<Produto>): Observable<Produto> {
    return this.http.post<Produto>(`${this.apiUrl}/rag/produtos/`, produto)
      .pipe(catchError(this.handleError));
  }

  /**
   * Atualiza produto completo (PUT)
   */
  updateProduct(id: number, produto: Partial<Produto>): Observable<Produto> {
    return this.http.put<Produto>(`${this.apiUrl}/rag/produtos/${id}/`, produto)
      .pipe(catchError(this.handleError));
  }

  /**
   * Atualiza produto parcial (PATCH)
   */
  patchProduct(id: number, dados: Partial<Produto>): Observable<Produto> {
    return this.http.patch<Produto>(`${this.apiUrl}/rag/produtos/${id}/`, dados)
      .pipe(catchError(this.handleError));
  }

  /**
   * Deleta produto
   */
  deleteProduct(id: number): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/rag/produtos/${id}/`)
      .pipe(catchError(this.handleError));
  }

  // ============================================
  // UPLOAD DE IMAGENS
  // ============================================

  /**
   * Upload de imagem do produto
   */
  uploadImagem(produtoId: number, arquivo: File): Observable<any> {
    const formData = new FormData();
    formData.append('imagem', arquivo);

    return this.http.post(
      `${this.apiUrl}/rag/produtos/${produtoId}/imagem/`,
      formData
    ).pipe(catchError(this.handleError));
  }

  /**
   * Atualiza URL externa da imagem
   */
  updateImagemUrl(produtoId: number, imageUrl: string): Observable<any> {
    return this.http.patch(
      `${this.apiUrl}/rag/produtos/${produtoId}/imagem/`,
      { imagem_url: imageUrl }
    ).pipe(catchError(this.handleError));
  }

  // ============================================
  // ESTATÍSTICAS E FILTROS
  // ============================================

  /**
   * Estatísticas dos produtos
   */
  getProdutoStats(): Observable<ProdutoStats> {
    return this.http.get<ProdutoStats>(`${this.apiUrl}/rag/produtos/estatisticas/`)
      .pipe(catchError(this.handleError));
  }

  /**
   * Lista categorias únicas
   */
  getCategorias(): Observable<string[]> {
    return this.getProdutoStats().pipe(
      map(stats => stats.categorias.map(c => c.categoria))
    );
  }

  /**
   * Lista marcas únicas
   */
  getMarcas(): Observable<string[]> {
    return this.getProdutoStats().pipe(
      map(stats => stats.marcas_top.map(m => m.marca))
    );
  }

  /**
   * Produtos por categoria
   */
  getProductsByCategory(categoria: string, limit?: number): Observable<ProdutosResponse> {
    return this.getProducts({
      categoria,
      page_size: limit
    });
  }

  /**
   * Produtos em promoção
   */
  getPromocoes(limit?: number): Observable<ProdutosResponse> {
    return this.getProducts({
      promocao: true,
      page_size: limit,
      ordenar: 'preco_desc'
    });
  }

  /**
   * Produtos mais bem avaliados
   */
  getMaisAvaliados(limit: number = 10): Observable<ProdutosResponse> {
    return this.getProducts({
      page_size: limit,
      ordenar: 'avaliacao'
    });
  }

  /**
   * Produtos mais recentes
   */
  getMaisRecentes(limit: number = 10): Observable<ProdutosResponse> {
    return this.getProducts({
      page_size: limit,
      ordenar: 'mais_novo'
    });
  }

  /**
   * Produtos por faixa de preço
   */
  getProductsByPriceRange(min: number, max: number): Observable<ProdutosResponse> {
    return this.getProducts({
      preco_min: min,
      preco_max: max,
      ordenar: 'preco_asc'
    });
  }

  // ============================================
  // BUSCA E PESQUISA
  // ============================================

  /**
   * Busca textual (nome, descrição)
   */
  searchProducts(termo: string, limit?: number): Observable<ProdutosResponse> {
    return this.getProducts({
      search: termo,
      page_size: limit
    });
  }

  /**
   * Busca avançada com múltiplos filtros
   */
  advancedSearch(filtros: ProdutoFiltros): Observable<ProdutosResponse> {
    return this.getProducts(filtros);
  }

  // ============================================
  // COMPARAÇÃO E RECOMENDAÇÕES
  // ============================================

  /**
   * Compara produtos específicos (envia IDs para o backend)
   */
  compareProducts(ids: number[]): Observable<Produto[]> {
    // Busca cada produto individualmente
    const requests = ids.map(id => this.getProduct(id));
    
    // Combina todas as requisições
    return new Observable(observer => {
      Promise.all(requests.map(req => req.toPromise()))
        .then(produtos => {
          observer.next(produtos as Produto[]);
          observer.complete();
        })
        .catch(error => observer.error(error));
    });
  }

  /**
   * Recomendações baseadas em um produto (similar)
   */
  getSimilarProducts(produtoId: number, limit: number = 5): Observable<ProdutoList[]> {
    // Implementar quando o backend tiver endpoint de similaridade
    // Por enquanto, busca produtos da mesma categoria
    return this.getProduct(produtoId).pipe(
      switchMap(produto => 
        this.getProductsByCategory(produto.categoria, limit).pipe(
          map(response => response.results.filter(p => p.id !== produtoId))
        )
      )
    );
  }

  // ============================================
  // UTILIDADES
  // ============================================

  /**
   * Health check da API
   */
  healthCheck(): Observable<HealthCheck> {
    return this.http.get<HealthCheck>(`${this.apiUrl}/health/`)
      .pipe(catchError(this.handleError));
  }

  /**
   * Formata preço em Real brasileiro
   */
  formatarPreco(valor: number): string {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(valor);
  }

  /**
   * Calcula desconto percentual
   */
  calcularDesconto(preco: number, precoPromocional: number): number {
    if (!precoPromocional || precoPromocional >= preco) {
      return 0;
    }
    return Math.round(((preco - precoPromocional) / preco) * 100);
  }

  /**
   * Verifica se produto está em promoção
   */
  temPromocao(produto: Produto | ProdutoList | ProdutoMinimal): boolean {
  return !!(produto.preco_promocional && produto.preco_promocional < produto.preco);
  }

  /**
   * Verifica se produto tem estoque
   */
  temEstoque(produto: Produto | ProdutoList | ProdutoMinimal): boolean {
    return produto.estoque > 0;
  }

  /**
   * Verifica se estoque está baixo
   */
  estoqueBaixo(produto: Produto | ProdutoList | ProdutoMinimal): boolean {
    return produto.estoque > 0 && produto.estoque < 10;
  }

  /**
   * Get da URL da imagem (com fallback)
   */
  getImagemUrl(produto: Produto | ProdutoList): string | null {
    return produto.imagem_completa || 
           (produto as any).imagem_url || 
           null;
  }

  /**
   * Get da URL do thumbnail
   */
  getThumbnailUrl(produto: Produto | ProdutoList): string | null {
    return (produto as any).thumbnail_url || 
           produto.imagem_completa || 
           null;
  }

  // ============================================
  // TRATAMENTO DE ERROS
  // ============================================

  private handleError(error: any) {
    let errorMessage = 'Erro desconhecido';

    if (error.error instanceof ErrorEvent) {
      // Erro do lado do cliente
      errorMessage = `Erro: ${error.error.message}`;
    } else {
      // Erro do lado do servidor
      errorMessage = `Código: ${error.status}\nMensagem: ${error.message}`;
      
      if (error.error?.detail) {
        errorMessage += `\nDetalhe: ${error.error.detail}`;
      }
      
      if (error.error?.error) {
        errorMessage += `\nErro: ${error.error.error}`;
      }
    }

    console.error('❌ Erro na requisição:', errorMessage);
    console.error('📋 Detalhes completos:', error);

    return throwError(() => new Error(errorMessage));
  }
}

// Adicione ao final do arquivo (fora da classe)
import { switchMap } from 'rxjs/operators';