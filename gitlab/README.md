# GitLab local com Docker Compose

Este diretório sobe uma instância local do **GitLab CE** com **GitLab Runner** usando Docker Compose.

## Arquivos

- `docker-compose.yml`: serviços `gitlab` e `gitlab-runner`.
- `.env.example`: variáveis de ambiente para portas, URLs e hostname.
- `config.toml`: configuração do runner (`executor = "docker"`).

## Pré-requisitos

- Docker
- Docker Compose (plugin `docker compose`)

## Configuração

1. Copie o arquivo de ambiente:

```bash
cp .env.example .env
```

2. Ajuste as variáveis em `.env` conforme seu ambiente:

- `GITLAB_HOSTNAME`
- `GITLAB_EXTERNAL_URL`
- `GITLAB_HTTP_PORT`
- `GITLAB_HTTPS_PORT`
- `GITLAB_SSH_PORT`
- `GITLAB_REGISTRY_EXTERNAL_URL`
- `GITLAB_REGISTRY_PORT`

3. Atualize o token do runner em `config.toml`:

```toml
token = "XXX"
```

Substitua por um token válido gerado no GitLab.

## Subindo o ambiente

```bash
docker compose --env-file .env up -d
```

Acompanhar logs:

```bash
docker compose logs -f gitlab
docker compose logs -f gitlab-runner
```

## Acesso

Com os valores padrão do `.env.example`:

- GitLab: `http://localhost:8080`
- SSH Git: `localhost:2222`
- Container Registry: `http://localhost:5050`

## Primeiro login (root)

Após o primeiro start, recupere a senha inicial do utilizador `root`:

```bash
docker exec -it gitlab grep 'Password:' /etc/gitlab/initial_root_password
```

Depois entre na interface web e altere a senha.

## Criar grupo, projeto e publicar o repositório

1. Crie o grupo `bca` no GitLab:
   - Menu `Groups` > `New group`.
   - `Group name`: `bca`
   - `Group URL/path`: `bca`

2. Crie o projeto `django_todolist` dentro do grupo `bca`:
   - Menu `New project` > `Create blank project`.
   - `Project name`: `django_todolist`
   - `Project URL/slug`: `django_todolist`
   - `Project namespace`: `bca`

3. Crie um token para push por HTTP:
   - No projeto `django_todolist`, vá em `Settings` > `Access Tokens`.
   - Crie o token com pelo menos `read_repository` e `write_repository`.
   - Copie o token gerado (ele só é mostrado uma vez).

4. No repositório local, adicione o remote `gitlab`:

```bash
git remote add gitlab http://root:glpat-<SEU_TOKEN>@localhost:8080/bca/django_todolist.git
```

Se o remote `gitlab` já existir:

```bash
git remote set-url gitlab http://root:glpat-<SEU_TOKEN>@localhost:8080/bca/django_todolist.git
```

5. Faça push para a branch principal:

```bash
git push gitlab main
```

Nota: evite guardar token real em ficheiros versionados.

## Runner

O serviço `gitlab-runner` já está no compose e monta:

- `./config.toml` em `/etc/gitlab-runner/config.toml`
- `/var/run/docker.sock` para executar builds Docker

Se precisar registrar o runner manualmente:

```bash
docker exec -it gitlab-runner gitlab-runner register
```

Use a URL configurada (`http://gitlab` dentro da rede Docker, conforme `config.toml`) e um token de registro válido.

## Comandos úteis

Parar os serviços:

```bash
docker compose down
```

Parar e remover volumes (apaga dados do GitLab):

```bash
docker compose down -v
```

Reiniciar apenas o GitLab:

```bash
docker compose restart gitlab
```
