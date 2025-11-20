import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface RAGQuery {
  query: string;
  limit?: number;
}

export interface Produto {
  id: number;
  nome: string;
  categoria: string;
  preco: number;
  preco_promocional?: number;
  marca?: string;
  cor?: string;
  estoque: number;
  avaliacao?: number;
  score: number;
}

export interface RAGResponse {
  query: string;
  resposta: string;
  produtos_encontrados: number;
  produtos: Produto[];
  tempo_processamento: number;
}

@Injectable({
  providedIn: 'root'
})
export class RagService {
  private apiUrl = environment.apiUrl; // Usa a variável do environment

  constructor(private http: HttpClient) {
    console.log('API URL:', this.apiUrl); // Para debug
  }

  query(data: RAGQuery): Observable<RAGResponse> {
    return this.http.post<RAGResponse>(`${this.apiUrl}/rag/query/`, data);
  }

  getProducts(): Observable<Produto[]> {
    return this.http.get<Produto[]>(`${this.apiUrl}/produtos/`);
  }

  getStats(): Observable<any> {
    return this.http.get(`${this.apiUrl}/rag/stats/`);
  }
}