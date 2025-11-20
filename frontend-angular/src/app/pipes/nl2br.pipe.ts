import { Pipe, PipeTransform } from '@angular/core';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';

@Pipe({
  name: 'nl2br',
  standalone: true
})
export class Nl2brPipe implements PipeTransform {
  
  constructor(private sanitizer: DomSanitizer) {}

  transform(value: string): SafeHtml {
    if (!value) return '';
    
    // Converte quebras de linha em <br>
    const text = value.replace(/\n/g, '<br>');
    
    // Sanitiza o HTML
    return this.sanitizer.sanitize(1, text) || '';
  }
}