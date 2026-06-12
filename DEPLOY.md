# 🚀 Deploy do Bolão da Copa — Fly.io + Neon

Banco no **Neon** (PostgreSQL grátis e persistente) e app no **Fly.io** (deploy pelo
terminal, sem GitHub). Tudo pelo PowerShell.

---

## 1) Banco no Neon (grátis)
1. Acesse **https://neon.tech** e crie uma conta (Google/e-mail).
2. Crie um **projeto**. Região: prefira **AWS South America (São Paulo)** se aparecer.
3. Clique em **Connect** e copie a **Connection string**. Fica assim:
   ```
   postgresql://usuario:senha@ep-xxxx.sa-east-1.aws.neon.tech/neondb?sslmode=require
   ```
4. Guarde essa string — é o seu `DATABASE_URL`.

---

## 2) Instalar o Fly e entrar
No **PowerShell**:
```powershell
iwr https://fly.io/install.ps1 -useb | iex
```
**Feche e reabra o PowerShell** (pra reconhecer o comando `fly`). Depois:
```powershell
fly auth signup     # já tem conta? use: fly auth login
```
> O Fly pede um cartão no cadastro (anti-abuso). Não cobra dentro do uso pequeno.

---

## 3) Criar o app no Fly
Na pasta do projeto:
```powershell
cd "C:\Users\lucor\Music\bolão"
fly launch --no-deploy
```
Responda aos avisos:
- **Usar o `fly.toml` existente?** → **Sim**.
- Se o nome `bolao-da-copa` estiver em uso, escolha outro (ex.: `bolao-do-luiz`).
- Região: **gru (São Paulo)**.
- **Criar Postgres/Redis pelo Fly?** → **Não** (usamos o Neon).
- **Fazer deploy agora?** → **Não** (faltam os segredos).

---

## 4) Configurar os segredos
Gere uma chave secreta forte:
```powershell
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
```
Copie o resultado e rode (troque os valores entre aspas):
```powershell
fly secrets set `
  DATABASE_URL="postgresql://...SUA_STRING_DO_NEON...?sslmode=require" `
  SECRET_KEY="cole_a_chave_gerada_acima" `
  FOOTBALL_DATA_TOKEN="c81d3147810f43c592f981e845d95cdb" `
  BOOTSTRAP_ADMIN_USER="Admin" `
  BOOTSTRAP_ADMIN_PASSWORD="escolha_uma_senha_forte"
```
> Os segredos ficam só no Fly, nunca no código. O **admin é criado sozinho** no 1º deploy.

---

## 5) Subir 🎉
```powershell
fly deploy
```
Aguarde o build (~2-4 min). No fim:
```powershell
fly open
```
Abre o site. Entre com **Admin** + a senha que você definiu no passo 4.

---

## Primeiros passos no ar
1. Entre como **Admin**.
2. **Painel Admin → 🔄 Atualizar dados** (puxa os jogos da Copa pra dentro).
3. Cadastre os participantes e lance os palpites.

## Atualizar o app depois
Mudou algo no código? Só rodar de novo:
```powershell
fly deploy
```

## Comandos úteis
| Ação | Comando |
|------|---------|
| Ver logs em tempo real | `fly logs` |
| Status do app | `fly status` |
| Trocar um segredo | `fly secrets set CHAVE="valor"` (faz redeploy) |
| Abrir no navegador | `fly open` |
| Reiniciar | `fly apps restart` |

## Observações
- O app **desliga quando ocioso** e **liga sozinho** no próximo acesso (~poucos segundos).
  Isso mantém o uso dentro do gratuito. Pra deixar sempre ligado, mude
  `min_machines_running = 1` no `fly.toml` e `fly deploy`.
- O banco do Neon também "hiberna" quando parado e acorda na primeira conexão.
- Trocar a senha do admin depois: faça login e use o painel, **ou**
  `fly secrets set BOOTSTRAP_ADMIN_PASSWORD="nova"` só funciona se o admin ainda não existir;
  com o admin já criado, troque pela aplicação.
