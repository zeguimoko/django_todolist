# Observability (Logs) – Loki + Alloy + Grafana

Guia rápido para a equipa de monitorização levantar o stack de logs e detectar abusos, ataques e eventos anómalos.

---

## 0. Monitoring vs Observability
- **Monitoring**: verifica sintomas *conhecidos* com métricas e alertas (ex.: CPU > 90%, 5xx > limiar). Responde “está saudável?” mas pouco ajuda se a falha não foi prevista.
- **Observability**: responde “*por que* quebrou?” mesmo para falhas *desconhecidas*, graças a telemetria rica e explorável (alta cardinalidade e contexto).

| Aspecto              | Monitoring                           | Observability                                    |
|----------------------|--------------------------------------|--------------------------------------------------|
| Objetivo             | Detectar falhas conhecidas           | Explicar qualquer falha, conhecida ou não        |
| Sinais típicos       | Métricas + alguns logs               | Logs, Métricas, Traces (correlacionados)         |
| Pergunta principal   | “Está ok?”                           | “O que aconteceu e por quê?”                     |
| Lidando com o novo   | Fraco (regras prévias)               | Forte (exploração ad‑hoc)                        |

- **Pilares clássicos**:  
  - **Logs**: eventos detalhados, contexto rico (pilar em foco aqui).  
  - **Métricas**: valores agregados no tempo (detecção rápida).  
  - **Traces**: caminho de pedidos entre serviços (causa e latência).  
  No monitoring tradicional, logs eram quase só auditoria; em observabilidade, logs são um pilar essencial para investigação e detecção avançada.

---

## 1. Objetivo
Centralizar logs dos containers Docker, permitir consulta rápida (LogQL) e dashboards em Grafana para detecção de incidentes (ex.: brute‑force, SQLi, path traversal, falhas 5xx).

---

## 2. Componentes
- **Loki** (porta `3100`): armazenamento/consulta de logs.
- **Alloy** (porta `12345`): agente/collector; lê Docker logs via `docker.sock` e envia para Loki.
- **Grafana** (porta `3000`): visualização e alertas (admin/admin por defeito – trocar).

Configurações principais:
- `observability/docker-compose.yml`
- `observability/loki/loki-config.yaml`
- `observability/alloy/config.alloy`
- Provisioning Grafana em `observability/grafana/provisioning/` (dashboards/datasources).

---

## 3. Pré‑requisitos
- Docker + Docker Compose v2.
- Rede Docker externa `web-app-network` (usada para falar com a app e entre serviços):
  ```bash
  docker network create web-app-network || true
  ```
- Porta 3000 (Grafana) e 3100 (Loki) liberadas localmente ou via VPN.

---

## 4. Subir Aplicação e stack de Monitoramento
* Iniciar Aplicação Django atraves de Docker Compose:
  ```bash
  docker compose up -d
  ```
* Iniciar stack de Monitoramento:
  ```bash
  cd observability
  ```
  ```bash
  docker compose up -d --remove-orphans
  ```

---

## 4.1 Pré-condição: logs da app em stdout
Para o Alloy recolher logs, a aplicação precisa escrever no `stdout/stderr` do container.

Se o Django estiver sem `LOGGING` explícito, mensagens `logger.info(...)` podem não aparecer (nível efetivo costuma filtrar `INFO`).

Exemplo mínimo em `todolist_project/config/settings.py`:
```python
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "default",
        },
    },
    "root": {"handlers": ["console"], "level": "INFO"},
}
```

Após alterar, reinicie a aplicação:
```bash
docker compose restart django_todolist
```

---

## 5. Fluxo de logs
- Alloy descobre containers via Docker API (`discovery.docker`) e lê stdout/stderr.
- Os registos são enviados para Loki com o label `job="docker"` e labels nativos do container.
- Grafana está pré‑provisionado para Loki; use Explore → Loki para consultar.

---

## 5.1 Exemplo de logging na aplicação (Python/Django)
Adicionar num ponto sensível (ex.: view de login) para registrar tentativas:
```python
import logging
logger = logging.getLogger(__name__)
...
def login_view(request):
    ip = request.META.get("REMOTE_ADDR")

    if request.method == 'POST':
        ### registrar tentativa de login
        logger.warning("login_attempt ip=%s, msg=%s", ip, "tentativa de login")
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            ### registrar login bem-sucedido
            logger.info("login_success ip=%s msg=%s", ip, "login bem-sucedido")
            login(request, user)
            return redirect('task_list')
        ### registrar login falhado
        logger.error("login_fail ip=%s msg=%s", ip, "login falhado")
        messages.error(request, 'Credenciais inválidas.')

    return render(request, 'accounts/login.html')
    ...
```
Certifique-se de que o handler padrão escreve em stdout/stderr (padrão do Django em dev); Alloy captura essas saídas do container.

---

## 6. Teste rápido (push manual)
```bash
cd observability
./alloy/test-manual.md   # contém o curl; ou execute:
curl -s -X POST "http://localhost:3100/loki/api/v1/push" \
  -H "Content-Type: application/json" \
  --data-raw '{
    "streams":[{"stream":{"app":"manual-test"},"values":[["'$(date +%s%N)'","hello from manual push"]]}]
  }'
```
No Grafana → Explore (Loki): ` {app="manual-test"} `

---

## 7. Queries práticas (logs registados)
- Todos os logs do container da aplicação:
  ```
  {job="docker", container="django_todolist"}
  ```
- Tentativas de login falhadas:
  ```
  {job="docker", container="django_todolist"} |= "login_fail"
  ```
- Tentativas de login:
  ```
  {job="docker", container="django_todolist"} |= "login_attempt"
  ```
- Login com sucesso:
  ```
  {job="docker", container="django_todolist"} |= "login_success"
  ```

---


## 8. Query agregada de login + dashboard
Use a query abaixo para ver, numa só visualização, os eventos `login_fail`, `login_attempt`, `login_success` e `login_view`:
```logql
sum by (login) (
  count_over_time(
    {job="docker", container="django_todolist"}
    | regexp "login_(?P<login>fail|attempt|success|view)"
  [$__interval])
)
```

Como adicionar no dashboard:
1) Abrir `http://localhost:3000` e entrar no Grafana.  
2) Ir para **Explore** e selecionar data source **Loki**.  
3) Colar a query acima e clicar em **Run query**.  
4) Clicar em **Add to dashboard** e escolher **New dashboard** (ou um existente).  
5) No painel, usar visualização **Time series** e definir legenda como `{{login}}`.  
6) Guardar o dashboard com um nome: `Login Events by Type`.

---

## 10. Ver logs no Grafana (passo-a-passo)
1) Abrir `http://localhost:3000` (login admin/admin se não alterado).  
2) Explore → selecionar data source **Loki**.  
3) Introduzir a query (ex.: `{job="docker", container="django_todolist"}`) e **Run query**.  
4) Usar *Log browser* para acrescentar labels (container, service_name).  
5) Salvar visualização em um dashboard: `Save > Add to dashboard`.

---

## 9. Consultas úteis (deteção)
- Erros HTTP 5xx:
  ```
  {job="docker"} |= " 500 " | json | status >= 500
  ```
- Paths suspeitos (path traversal, admin endpoints):
  ```
  {job="docker"} |= "../" or |= "/etc/passwd" or |= "/admin"
  ```
- SQL Injection (padrões comuns):
  ```
  {job="docker"} |= "UNION SELECT" or |= "' or 1=1" or |= "sqlmap"
  ```
- Tentativas de brute‑force (exemplo nginx/traefik-like):
  ```
  {job="docker"} |= "POST /login" | pattern `<ip> - - * * "POST /login*"` | unwrap ip | count_over_time(1m)
  ```
- Pesquisa por container específico:
  ```
  {job="docker", container="django_todolist"}
  ```

---
## 11. Dashboards e alertas
### Dashboards (queries exemplo)
- Taxa de erros 5xx por serviço:
  ```
  sum by (container) (rate({job="docker"} |= " 500 " [5m]))
  ```
- Picos de login (potencial brute-force):
  ```
  sum by (container) (count_over_time({job="docker"} |= "login_attempt" [1m]))
  ```
- Principais IPs ruidosos:
  ```
  topk(5, sum by (ip) (count_over_time({job="docker"} |= "login_attempt" | regexp "(?P<ip>\\d+\\.\\d+\\.\\d+\\.\\d+)" [5m])))
  ```
### Alertas (ponto de partida)
#### Exemplo prático: alerta por email para 10 `login_fail`
Pré-condições:
- `grafana` e `mailpit` ativos no `observability/docker-compose.yml` (SMTP em `mailpit:1025`).
- Web UI do Mailpit disponível em `http://localhost:8025`.

Fluxo alinhado ao Grafana `10.4.5`:
1. Abrir Grafana em `http://localhost:3000` e ir para **Alerting** (ou **Alerts & IRM**) -> **Alert rules** -> **New alert rule**.
2. Em **Rule type**, escolher **Grafana-managed alert**.
   - Se a regra for **Data source-managed** (Loki/Prometheus), os blocos **Set evaluation behavior** e **Configure notifications** nao aparecem.
3. Em **Define query and alert condition**, criar a **Query A** (data source Loki):
   ```logql
   sum(count_over_time({job="docker", container="django_todolist"} |= "login_fail"[5m]))
   ```
4. Configurar a condição de disparo:
   - Modo simples: `WHEN last() OF A IS ABOVE 10`.
   - Modo advanced: **Reduce(B)=Last(A)** e **Threshold(C)=B IS ABOVE 10**, com **C** como condição.
5. Em **Set evaluation behavior**:
   - usar grupo com intervalo de avaliacao `1m`
   - **For / Pending period**: `0m` (ou `1m` para reduzir ruido)
6. Em **Configure notifications**, ligar a regra a um **contact point Email** (ex.: `security-mailpit`).
7. Se **Configure notifications** nao aparecer, ir em **Alerting -> Settings -> Alertmanagers** e ativar o Grafana para receber alertas Grafana-managed.
8. Guardar a regra com nome, por exemplo: `Login fail >= 10 em 5m`.
9. Gerar falhas de login (manual ou k6) ate passar o limiar e validar o email em `http://localhost:8025`.
10. Diminuir tempos em "Notification policies" para `Group interval=20s`, `Repeat interval=30s`. Para receber alertas em menos tempo.

---
