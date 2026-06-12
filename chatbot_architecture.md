# Resumo das Atualizações e Arquitetura do Chatbot para o Bolão

## 1. O Que Foi Desenvolvido

Nos últimos passos, aprimoramos a interface visual das imagens de prévia e resultado dos jogos, preparando o terreno para compartilhamento em redes sociais ou WhatsApp. As principais mudanças foram:

*   **Identidade Visual Aprimorada:** O fundo foi alterado para um tom de verde escuro elegante, e os cards agora possuem um efeito translúcido (glassmorphism) que dá um aspecto mais moderno e *premium*.
*   **Bandeiras Redondas (Circle Flags):** Integramos a biblioteca de SVGs `circle-flags`, garantindo que todas as bandeiras apareçam perfeitamente redondas e em alta qualidade (SVG) preenchendo todo o espaço circular. Criamos um mapeamento completo de nomes de países para garantir que times como "Estados Unidos" e "Coréia do Sul" puxem a bandeira correta.
*   **Alinhamento e Responsividade:** Ajustamos o layout para caber inteiramente em uma tela (`100vh`), removendo qualquer necessidade de rolagem. Para resolver problemas de alinhamento no placar e nos rankings causados pelo tamanho variável dos nomes e números, implementamos larguras fixas (`inline-block` com medidas exatas) para os elementos, garantindo que colunas fiquem perfeitamente alinhadas independentemente dos caracteres.
*   **Ranking Detalhado:** A visualização de fim de jogo agora inclui a pontuação da partida em verde para quem acertou em cheio, e setas indicando quantas posições a pessoa subiu (▲) ou desceu (▼) no ranking geral.

---

## 2. Projeto: Automação via Chatbot do WhatsApp

A ideia de criar um chatbot que dispare a imagem no WhatsApp quando as apostas fecharem ou o jogo acabar é excelente e totalmente viável. 

### Visão Geral da Arquitetura
Para que o envio ocorra de forma automatizada e sem intervenção manual, precisamos dividir o problema em três partes:

1.  **Geração da Imagem:** Converter o HTML/CSS incrível que criamos em um arquivo de imagem (PNG/JPG).
2.  **Gatilho (Trigger):** Identificar **quando** as apostas fecharam (ex: 15 minutos antes do jogo iniciar) ou quando o jogo acabou.
3.  **Bot do WhatsApp:** Enviar a imagem gerada para um grupo ou contatos específicos.

### Pesquisa Profunda e Soluções Propostas

#### A. Geração da Imagem a partir do HTML
Como o Python (FastAPI) já consulta o banco e gera o HTML, a melhor forma de tirar uma "foto" desse HTML é usando o **Playwright** ou **Puppeteer** (navegadores *headless* que rodam no servidor invisíveis).
*   **Como funciona:** O script Python que fizemos hoje salva um `.html`. Em seguida, o Playwright abre esse arquivo e executa um comando `screenshot()`, salvando a imagem em disco em frações de segundo.

#### B. Soluções para o Bot do WhatsApp
Temos dois caminhos principais para integrar o WhatsApp:

**Opção 1: API Oficial do WhatsApp Cloud (Recomendada se tiver CNPJ/Meta Business)**
*   **Vantagens:** Estável, oficial, sem risco de banimento de número.
*   **Desvantagens:** Requer aprovação da Meta (Facebook), tem custos após um limite de mensagens gratuitas, e **não pode** ser adicionado facilmente a grupos normais de usuários (só envia mensagens diretas como "Empresa").

**Opção 2: APIs Não-Oficiais baseadas em WhatsApp Web (Recomendada para Projetos Pessoais/Grupos)**
Essas APIs simulam um navegador acessando o WhatsApp Web e escanear o QR Code de um celular "doador".
*   **whatsapp-web.js (Node.js):** Muito famosa e poderosa. Permite ler mensagens, responder, e enviar imagens para grupos e contatos.
*   **Evolution API:** Uma das melhores da atualidade. É uma API open-source que você roda no seu servidor, escaneia o QR Code, e ela te dá rotas HTTP fáceis. Exemplo: você manda um `POST` para a Evolution API com a imagem e o ID do Grupo, e ela envia a mensagem.

### Fluxo de Funcionamento Ideal (A Implementar)

1.  **Agendamento (Cron Job / Celery):** O backend (Python) fica monitorando a tabela de jogos. 
2.  **Fechamento de Apostas:** O horário atual fica a menos de X minutos do início de um jogo. O sistema trava as apostas desse jogo.
3.  **Captura da Tela:** O sistema roda o script de gerar a prévia (que fizemos), invoca o **Playwright**, tira o screenshot do `.html` e salva como `preview_match_X.png`.
4.  **Disparo:** O sistema Python faz uma requisição para o serviço do WhatsApp (ex: Evolution API ou whatsapp-web.js), enviando a imagem com a legenda: *"🚨 Apostas Fechadas! Confira os palpites da galera para o jogo de hoje!"*.
5.  **Fim de Jogo:** Quando a API de futebol (ou atualização manual) definir o jogo como finalizado, repete-se o processo usando a nossa tela de **Fim de Jogo**, mostrando os pontos e a imagem `resultado_match_X.png` com a legenda: *"🏁 Fim de Jogo! Veja como ficou a pontuação e o ranking!"*

### Próximos Passos
Para implementar isso na prática, nossa próxima etapa no desenvolvimento precisará ser:
1.  Instalar e configurar o Playwright no backend para automação do screenshot.
2.  Subir um serviço em Node.js com `whatsapp-web.js` (ou Evolution API).
3.  Criar a lógica no banco de dados para "avisar" o sistema que o jogo fechou ou acabou sem precisar rodar manualmente.
