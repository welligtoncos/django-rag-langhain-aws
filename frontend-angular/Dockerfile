# Stage 1: Build da aplicação Angular
FROM node:18-alpine AS build

# Define o diretório de trabalho
WORKDIR /app

# Copia os arquivos de dependências
COPY package*.json ./

# Instala as dependências com mais memória
ENV NODE_OPTIONS="--max-old-space-size=4096"
RUN npm ci

# Copia o código fonte
COPY . .

# Build da aplicação para produção
RUN npm run build -- --configuration production

# Stage 2: Servir com Nginx
FROM nginx:alpine

# Copia os arquivos buildados do stage anterior
COPY --from=build /app/dist/frontend_ia_rag_aws/browser /usr/share/nginx/html

# Copia configuração customizada do Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expõe a porta 80
EXPOSE 80

# Comando para iniciar o Nginx
CMD ["nginx", "-g", "daemon off;"]