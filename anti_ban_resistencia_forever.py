#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║           🔥 ANTI BAN RESISTÊNCIA FOREVER 🔥                                  ║
║                                                                              ║
║  Script de proteção e monitoramento de contas Discord                         ║
║  Desenvolvido para a Resistência                                              ║
║                                                                              ║
║  ⚠️  AVISO: O uso de self-bots viola os Termos de Serviço do Discord.          ║
║      Use por sua conta e risco. Este script é para fins educacionais.         ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import requests
import threading
import time
import random
import json
import logging
import os
import sys
import argparse
import uuid
import hashlib
import platform
import subprocess
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

# Tentativa de importar websocket para Gateway
try:
    import websocket
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False
    print("[!] websocket-client não instalado. Gateway não estará disponível.")
    print("    Instale com: pip install websocket-client")

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False
    class DummyFore:
        def __getattr__(self, name): return ''
    class DummyStyle:
        def __getattr__(self, name): return ''
    Fore = DummyFore()
    Style = DummyStyle()

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÕES E CONSTANTES
# ═══════════════════════════════════════════════════════════════════════════════

DISCORD_API = "https://discord.com/api/v10"
DISCORD_GATEWAY = "wss://gateway.discord.gg/?v=10&encoding=json"

# Headers base REALISTAS da API Discord (não inventados)
BASE_HEADERS = {
    "Accept": "*/*",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "X-Discord-Locale": "pt-BR",
    "X-Discord-Timezone": "America/Sao_Paulo",
}

# User-Agents realistas
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

# Atividades humanas realistas com delays
HUMAN_ACTIVITIES = [
    {"name": "typing_indicator", "weight": 30, "delay": (3, 15)},
    {"name": "presence_update", "weight": 20, "delay": (60, 300)},
    {"name": "guild_browse", "weight": 15, "delay": (10, 60)},
    {"name": "channel_read", "weight": 20, "delay": (5, 30)},
    {"name": "friend_check", "weight": 10, "delay": (30, 120)},
    {"name": "settings_check", "weight": 5, "delay": (60, 300)},
]

# Rate limits conhecidos da API Discord (requests por segundo)
RATE_LIMITS = {
    "default": {"limit": 50, "window": 1},           # 50/s global
    "messages": {"limit": 5, "window": 5},            # 5/5s por canal
    "guilds": {"limit": 5, "window": 60},             # 5/min
    "channels": {"limit": 5, "window": 5},            # 5/5s
    "reactions": {"limit": 1, "window": 0.25},        # 1/0.25s
    "typing": {"limit": 1, "window": 10},             # 1/10s por canal
    "presence": {"limit": 5, "window": 60},           # 5/min
    "profile": {"limit": 2, "window": 60},           # 2/min
}

# ═══════════════════════════════════════════════════════════════════════════════
# LOGGER CUSTOMIZADO
# ═══════════════════════════════════════════════════════════════════════════════

class ResistenciaLogger:
    """Logger com identidade visual da Resistência"""

    def __init__(self, name="Resistencia"):
        self.name = name
        self.setup_logger()

    def setup_logger(self):
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.DEBUG)

        if not self.logger.handlers:
            # Handler para console
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_format = logging.Formatter(
                f"{Fore.CYAN}[%(asctime)s]{Style.RESET_ALL} %(levelname)s %(message)s",
                datefmt="%H:%M:%S"
            )
            console_handler.setFormatter(console_format)
            self.logger.addHandler(console_handler)

            # Handler para arquivo
            file_handler = logging.FileHandler("resistencia_forever.log", encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)
            file_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            file_handler.setFormatter(file_format)
            self.logger.addHandler(file_handler)

    def info(self, msg):
        self.logger.info(f"{Fore.GREEN}✓{Style.RESET_ALL} {msg}")

    def warn(self, msg):
        self.logger.warning(f"{Fore.YELLOW}⚠{Style.RESET_ALL} {msg}")

    def error(self, msg):
        self.logger.error(f"{Fore.RED}✗{Style.RESET_ALL} {msg}")

    def debug(self, msg):
        self.logger.debug(f"{Fore.MAGENTA}◆{Style.RESET_ALL} {msg}")

    def banner(self, msg):
        self.logger.info(f"{Fore.CYAN}╔{'═' * 58}╗{Style.RESET_ALL}")
        self.logger.info(f"{Fore.CYAN}║{Style.RESET_ALL} {msg:^56} {Fore.CYAN}║{Style.RESET_ALL}")
        self.logger.info(f"{Fore.CYAN}╚{'═' * 58}╝{Style.RESET_ALL}")


# ═══════════════════════════════════════════════════════════════════════════════
# CLASSE PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

class AntiBanResistenciaForever:
    """
    Sistema Anti-Ban da Resistência Forever
    Monitora, protege e simula atividade humana em contas Discord.
    """

    def __init__(self, token, config_path="config.json"):
        self.token = token.strip()
        self.config_path = config_path
        self.log = ResistenciaLogger("ResistenciaForever")

        # Estado
        self.running = False
        self.user_data = None
        self.guilds = []
        self.channels = []
        self.dms = []

        # Rate limiting
        self.rate_buckets = {}
        self.request_history = []
        self.global_rate_limit = {"remaining": 50, "reset_after": 1, "reset_time": time.time()}

        # Proxies
        self.proxies = []
        self.proxy_index = 0
        self.proxy_lock = threading.Lock()

        # Threads
        self.threads = []
        self.executor = ThreadPoolExecutor(max_workers=5)

        # Gateway
        self.ws = None
        self.heartbeat_interval = None
        self.sequence_number = None
        self.session_id = None

        # Atividade
        self.last_typing = {}
        self.last_presence = 0
        self.activity_stats = {
            "requests_sent": 0,
            "rate_limits_hit": 0,
            "proxies_used": 0,
            "activities_performed": 0,
            "start_time": None,
        }

        # Inicialização
        self.load_config()
        self.load_proxies()
        self.generate_fingerprint()

    def load_config(self):
        """Carrega ou cria configuração"""
        default_config = {
            "delay_min": 1.0,
            "delay_max": 5.0,
            "typing_enabled": True,
            "presence_enabled": True,
            "proxy_enabled": True,
            "gateway_enabled": True,
            "activity_interval": 30,
            "monitor_interval": 60,
            "max_retries": 3,
            "safe_mode": True,
        }

        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    default_config.update(loaded)
                self.log.info(f"Configuração carregada de {self.config_path}")
            except Exception as e:
                self.log.warn(f"Erro ao carregar config: {e}. Usando padrão.")
        else:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=4)
            self.log.info(f"Configuração padrão criada em {self.config_path}")

        self.config = default_config

    def load_proxies(self):
        """Carrega proxies do arquivo proxies.txt"""
        proxy_file = "proxies.txt"
        if os.path.exists(proxy_file):
            try:
                with open(proxy_file, "r", encoding="utf-8") as f:
                    self.proxies = [line.strip() for line in f if line.strip() and not line.startswith("#")]
                self.log.info(f"Carregados {len(self.proxies)} proxies")
            except Exception as e:
                self.log.warn(f"Erro ao carregar proxies: {e}")
        else:
            self.log.warn("Arquivo proxies.txt não encontrado. Rodando sem proxies.")
            # Cria arquivo vazio
            with open(proxy_file, "w", encoding="utf-8") as f:
                f.write("# Formato: ip:porta ou usuario:senha@ip:porta\n")

    def generate_fingerprint(self):
        """Gera fingerprint de sessão consistente"""
        self.device_id = str(uuid.uuid4())
        self.session_id = hashlib.sha256(os.urandom(32)).hexdigest()[:32]
        self.browser_version = random.choice(["120.0.0.0", "119.0.0.0", "121.0.0.0"])
        self.user_agent = random.choice(USER_AGENTS)

        self.log.debug(f"Device ID: {self.device_id}")
        self.log.debug(f"Session ID: {self.session_id}")

    def get_headers(self, extra=None):
        """Retorna headers HTTP realistas e válidos para a API Discord"""
        headers = BASE_HEADERS.copy()
        headers.update({
            "Authorization": self.token,
            "User-Agent": self.user_agent,
            "X-Super-Properties": self._encode_super_properties(),
        })
        if extra:
            headers.update(extra)
        return headers

    def _encode_super_properties(self):
        """Gera e codifica super_properties realistas (base64)"""
        props = {
            "os": platform.system(),
            "browser": "Chrome",
            "device": "",
            "system_locale": "pt-BR",
            "browser_user_agent": self.user_agent,
            "browser_version": self.browser_version,
            "os_version": platform.version() if hasattr(platform, "version") else "10.0",
            "referrer": "",
            "referring_domain": "",
            "referrer_current": "",
            "referring_domain_current": "",
            "release_channel": "stable",
            "client_build_number": 252462,
            "client_event_source": None,
            "design_id": 0,
        }
        import base64
        return base64.b64encode(json.dumps(props).encode()).decode()

    def get_proxy(self):
        """Retorna próximo proxy da lista em round-robin"""
        if not self.proxies or not self.config.get("proxy_enabled", True):
            return None

        with self.proxy_lock:
            proxy = self.proxies[self.proxy_index]
            self.proxy_index = (self.proxy_index + 1) % len(self.proxies)

        # Formato: http://ip:porta ou http://user:pass@ip:porta
        if "@" in proxy or ":" in proxy:
            return {"http": f"http://{proxy}", "https": f"http://{proxy}"}
        return None

    def check_rate_limit(self, bucket_name="default"):
        """Verifica se pode fazer request no bucket especificado"""
        now = time.time()

        # Limpa histórico antigo
        self.request_history = [t for t in self.request_history if now - t < 60]

        # Verifica rate limit global
        if now < self.global_rate_limit["reset_time"]:
            if self.global_rate_limit["remaining"] <= 0:
                wait = self.global_rate_limit["reset_time"] - now
                self.log.warn(f"Rate limit global atingido. Aguardando {wait:.1f}s")
                time.sleep(max(wait, 0.1))
                return self.check_rate_limit(bucket_name)

        # Verifica bucket específico
        bucket = RATE_LIMITS.get(bucket_name, RATE_LIMITS["default"])
        bucket_key = f"{bucket_name}:{int(now / bucket['window'])}"

        if bucket_key not in self.rate_buckets:
            self.rate_buckets[bucket_key] = {"count": 0, "reset": now + bucket["window"]}

        bucket_data = self.rate_buckets[bucket_key]

        if now > bucket_data["reset"]:
            bucket_data["count"] = 0
            bucket_data["reset"] = now + bucket["window"]

        if bucket_data["count"] >= bucket["limit"]:
            wait = bucket_data["reset"] - now
            self.log.warn(f"Rate limit bucket '{bucket_name}' atingido. Aguardando {wait:.1f}s")
            time.sleep(max(wait, 0.1))
            return self.check_rate_limit(bucket_name)

        bucket_data["count"] += 1
        self.request_history.append(now)
        return True

    def update_rate_limit(self, response):
        """Atualiza rate limits baseado nos headers de resposta do Discord"""
        remaining = response.headers.get("X-RateLimit-Remaining")
        reset_after = response.headers.get("X-RateLimit-Reset-After")
        limit = response.headers.get("X-RateLimit-Limit")

        if remaining is not None and reset_after is not None:
            self.global_rate_limit["remaining"] = int(remaining)
            self.global_rate_limit["reset_after"] = float(reset_after)
            self.global_rate_limit["reset_time"] = time.time() + float(reset_after)
            self.log.debug(f"Rate limit atualizado: {remaining}/{limit} restantes")

        if response.status_code == 429:
            self.activity_stats["rate_limits_hit"] += 1
            retry_after = float(response.headers.get("Retry-After", 5))
            is_global = response.headers.get("X-RateLimit-Global", "false").lower() == "true"

            if is_global:
                self.log.error(f"Rate limit GLOBAL atingido! Aguardando {retry_after}s")
                self.global_rate_limit["reset_time"] = time.time() + retry_after
            else:
                self.log.warn(f"Rate limit atingido. Aguardando {retry_after}s")

            time.sleep(retry_after)
            return False

        return True

    def request(self, method, endpoint, bucket="default", data=None, headers=None, retries=0):
        """Faz request HTTP com rate limiting, proxies e retry"""
        max_retries = self.config.get("max_retries", 3)

        if retries > max_retries:
            self.log.error(f"Máximo de retries atingido para {endpoint}")
            return None

        # Rate limit check
        self.check_rate_limit(bucket)

        # Delay humano
        if self.config.get("safe_mode", True):
            delay = random.uniform(self.config.get("delay_min", 1.0), self.config.get("delay_max", 5.0))
            time.sleep(delay)

        url = f"{DISCORD_API}{endpoint}" if not endpoint.startswith("http") else endpoint
        req_headers = self.get_headers()
        if headers:
            req_headers.update(headers)

        proxies = self.get_proxy()

        try:
            self.activity_stats["requests_sent"] += 1
            if proxies:
                self.activity_stats["proxies_used"] += 1

            if method == "GET":
                response = requests.get(url, headers=req_headers, proxies=proxies, timeout=15)
            elif method == "POST":
                response = requests.post(url, headers=req_headers, json=data, proxies=proxies, timeout=15)
            elif method == "PUT":
                response = requests.put(url, headers=req_headers, json=data, proxies=proxies, timeout=15)
            elif method == "PATCH":
                response = requests.patch(url, headers=req_headers, json=data, proxies=proxies, timeout=15)
            elif method == "DELETE":
                response = requests.delete(url, headers=req_headers, proxies=proxies, timeout=15)
            else:
                return None

            # Atualiza rate limits
            if not self.update_rate_limit(response):
                return self.request(method, endpoint, bucket, data, headers, retries + 1)

            if response.status_code in [200, 201, 204]:
                self.log.debug(f"{method} {endpoint} → {response.status_code}")
                return response
            elif response.status_code == 401:
                self.log.error("Token inválido ou expirado!")
                self.running = False
                return None
            elif response.status_code == 403:
                self.log.warn(f"Forbidden: {endpoint}")
                return response
            else:
                self.log.warn(f"{method} {endpoint} → {response.status_code}")
                return response

        except requests.exceptions.ProxyError as e:
            self.log.warn(f"Erro de proxy: {e}. Tentando sem proxy...")
            # Tenta sem proxy
            try:
                if method == "GET":
                    response = requests.get(url, headers=req_headers, timeout=15)
                elif method == "POST":
                    response = requests.post(url, headers=req_headers, json=data, timeout=15)
                elif method == "PUT":
                    response = requests.put(url, headers=req_headers, json=data, timeout=15)
                elif method == "PATCH":
                    response = requests.patch(url, headers=req_headers, json=data, timeout=15)
                elif method == "DELETE":
                    response = requests.delete(url, headers=req_headers, timeout=15)
                else:
                    return None

                if not self.update_rate_limit(response):
                    return self.request(method, endpoint, bucket, data, headers, retries + 1)
                return response
            except Exception as e2:
                self.log.error(f"Erro sem proxy: {e2}")
                return None

        except Exception as e:
            self.log.error(f"Erro na requisição: {e}")
            time.sleep(2)
            return self.request(method, endpoint, bucket, data, headers, retries + 1)

    def validate_token(self):
        """Valida o token e obtém dados do usuário"""
        self.log.info("Validando token...")
        response = self.request("GET", "/users/@me", bucket="profile")

        if response and response.status_code == 200:
            self.user_data = response.json()
            username = self.user_data.get("username", "unknown")
            discriminator = self.user_data.get("discriminator", "0")
            user_id = self.user_data.get("id", "unknown")

            self.log.banner(f"🛡️  BEM-VINDO, {username}#{discriminator}  🛡️")
            self.log.info(f"User ID: {user_id}")
            self.log.info(f"Email verificado: {self.user_data.get('verified', False)}")
            self.log.info(f"MFA ativado: {self.user_data.get('mfa_enabled', False)}")
            self.log.info(f"Nitro: {self.user_data.get('premium_type', 0)}")
            return True
        else:
            self.log.error("Falha na validação do token!")
            return False

    def load_guilds(self):
        """Carrega lista de servidores do usuário"""
        self.log.info("Carregando servidores...")
        response = self.request("GET", "/users/@me/guilds", bucket="guilds")

        if response and response.status_code == 200:
            self.guilds = response.json()
            self.log.info(f"Carregados {len(self.guilds)} servidores")

            # Carrega canais do primeiro servidor (se houver)
            if self.guilds:
                guild_id = self.guilds[0]["id"]
                self.load_channels(guild_id)
        else:
            self.log.warn("Não foi possível carregar servidores")

    def load_channels(self, guild_id):
        """Carrega canais de um servidor"""
        response = self.request("GET", f"/guilds/{guild_id}/channels", bucket="channels")
        if response and response.status_code == 200:
            channels = response.json()
            # Filtra apenas canais de texto
            self.channels = [c for c in channels if c.get("type") in [0, 5]]  # 0 = text, 5 = announcement
            self.log.info(f"Carregados {len(self.channels)} canais de texto")

    def load_dms(self):
        """Carrega DMs do usuário"""
        response = self.request("GET", "/users/@me/channels", bucket="default")
        if response and response.status_code == 200:
            self.dms = response.json()
            self.log.info(f"Carregados {len(self.dms)} canais DM")

    # ═══════════════════════════════════════════════════════════════════════════
    # SIMULAÇÃO DE ATIVIDADE HUMANA
    # ═══════════════════════════════════════════════════════════════════════════

    def activity_typing(self):
        """Simula digitação em canal aleatório"""
        if not self.channels:
            return

        channel = random.choice(self.channels)
        channel_id = channel["id"]

        # Verifica cooldown de typing (10s por canal)
        now = time.time()
        if channel_id in self.last_typing and now - self.last_typing[channel_id] < 10:
            return

        self.last_typing[channel_id] = now
        response = self.request("POST", f"/channels/{channel_id}/typing", bucket="typing")

        if response and response.status_code == 204:
            self.log.info(f"Typing em #{channel.get('name', 'unknown')}")
            self.activity_stats["activities_performed"] += 1

    def activity_presence(self, status="online", activity_type=0, activity_name=None):
        """Atualiza presença via Gateway (se conectado) ou simula"""
        if not activity_name:
            activities = [
                "Spotify", "Visual Studio Code", "League of Legends", 
                "Fortnite", "VALORANT", "YouTube", "Netflix",
                "Resistência Forever", "Protegendo a Resistência"
            ]
            activity_name = random.choice(activities)

        # Se Gateway estiver conectado, envia via WS
        if self.ws and self.ws.sock and self.ws.sock.connected:
            payload = {
                "op": 3,
                "d": {
                    "since": int(time.time() * 1000) if status != "online" else None,
                    "activities": [{
                        "name": activity_name,
                        "type": activity_type,
                        "created_at": int(time.time() * 1000)
                    }],
                    "status": status,
                    "afk": False
                }
            }
            try:
                self.ws.send(json.dumps(payload))
                self.log.info(f"Presença atualizada: {status} | {activity_name}")
                self.activity_stats["activities_performed"] += 1
            except Exception as e:
                self.log.debug(f"Erro ao enviar presença via Gateway: {e}")
        else:
            # Fallback: simula via PATCH settings
            settings = {"status": status}
            self.request("PATCH", "/users/@me/settings", bucket="profile", data=settings)

    def activity_browse_guild(self):
        """Simula navegação em servidor"""
        if not self.guilds:
            return
        guild = random.choice(self.guilds)
        guild_id = guild["id"]

        # Lê canais do servidor
        response = self.request("GET", f"/guilds/{guild_id}/channels", bucket="channels")
        if response and response.status_code == 200:
            channels = response.json()
            text_channels = [c for c in channels if c.get("type") == 0]
            if text_channels:
                channel = random.choice(text_channels)
                # Lê últimas mensagens
                self.request("GET", f"/channels/{channel['id']}/messages?limit=10", bucket="messages")
                self.log.info(f"Navegando em {guild.get('name', 'unknown')} > #{channel.get('name', 'unknown')}")
                self.activity_stats["activities_performed"] += 1

    def activity_check_friends(self):
        """Verifica lista de amigos"""
        response = self.request("GET", "/users/@me/relationships", bucket="default")
        if response and response.status_code == 200:
            friends = response.json()
            self.log.info(f"Verificando amigos: {len(friends)} encontrados")
            self.activity_stats["activities_performed"] += 1

    def activity_check_settings(self):
        """Verifica configurações"""
        response = self.request("GET", "/users/@me/settings", bucket="profile")
        if response and response.status_code == 200:
            self.log.info("Verificando configurações da conta")
            self.activity_stats["activities_performed"] += 1

    def perform_random_activity(self):
        """Seleciona e executa uma atividade aleatória baseada em pesos"""
        if not self.running:
            return

        activities = []
        weights = []

        for act in HUMAN_ACTIVITIES:
            if act["name"] == "typing_indicator" and not self.config.get("typing_enabled", True):
                continue
            if act["name"] == "presence_update" and not self.config.get("presence_enabled", True):
                continue
            activities.append(act["name"])
            weights.append(act["weight"])

        if not activities:
            return

        activity = random.choices(activities, weights=weights, k=1)[0]

        try:
            if activity == "typing_indicator":
                self.activity_typing()
            elif activity == "presence_update":
                statuses = ["online", "idle", "dnd"]
                status = random.choice(statuses)
                self.activity_presence(status=status)
            elif activity == "guild_browse":
                self.activity_browse_guild()
            elif activity == "channel_read":
                if self.channels:
                    ch = random.choice(self.channels)
                    self.request("GET", f"/channels/{ch['id']}/messages?limit=5", bucket="messages")
                    self.log.info(f"Lendo mensagens em #{ch.get('name', 'unknown')}")
                    self.activity_stats["activities_performed"] += 1
            elif activity == "friend_check":
                self.activity_check_friends()
            elif activity == "settings_check":
                self.activity_check_settings()
        except Exception as e:
            self.log.debug(f"Erro na atividade {activity}: {e}")

    # ═══════════════════════════════════════════════════════════════════════════
    # GATEWAY WEBSOCKET
    # ═══════════════════════════════════════════════════════════════════════════

    def gateway_connect(self):
        """Conecta ao Gateway do Discord via WebSocket"""
        if not WEBSOCKET_AVAILABLE:
            self.log.warn("websocket-client não instalado. Gateway desabilitado.")
            return

        if not self.config.get("gateway_enabled", True):
            self.log.info("Gateway desabilitado nas configurações.")
            return

        self.log.info("Conectando ao Gateway Discord...")

        def on_open(ws):
            self.log.info("Gateway conectado! Enviando IDENTIFY...")
            identify_payload = {
                "op": 2,
                "d": {
                    "token": self.token,
                    "properties": {
                        "os": platform.system(),
                        "browser": "Chrome",
                        "device": "",
                    },
                    "compress": False,
                    "large_threshold": 250,
                }
            }
            ws.send(json.dumps(identify_payload))

        def on_message(ws, message):
            try:
                data = json.loads(message)
                op = data.get("op")

                if op == 10:  # Hello
                    self.heartbeat_interval = data["d"]["heartbeat_interval"] / 1000
                    self.log.info(f"Heartbeat interval: {self.heartbeat_interval}s")
                    # Inicia heartbeat thread
                    hb_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
                    hb_thread.start()
                    self.threads.append(hb_thread)

                elif op == 0:  # Dispatch
                    self.sequence_number = data.get("s")
                    event_type = data.get("t")

                    if event_type == "READY":
                        self.session_id = data["d"].get("session_id")
                        self.log.info(f"Sessão pronta! Session ID: {self.session_id}")

                    elif event_type == "GUILD_CREATE":
                        guild = data["d"]
                        self.log.debug(f"Entrou no servidor: {guild.get('name')}")

                elif op == 11:  # Heartbeat ACK
                    self.log.debug("Heartbeat ACK recebido")

                elif op == 1:  # Heartbeat request
                    ws.send(json.dumps({"op": 1, "d": self.sequence_number}))

                elif op == 7:  # Reconnect
                    self.log.warn("Gateway pediu reconexão")
                    ws.close()

                elif op == 9:  # Invalid session
                    self.log.error("Sessão inválida! Reconectando...")
                    ws.close()

            except Exception as e:
                self.log.debug(f"Erro ao processar mensagem Gateway: {e}")

        def on_error(ws, error):
            self.log.error(f"Erro no Gateway: {error}")

        def on_close(ws, close_status_code, close_msg):
            self.log.warn(f"Gateway fechado: {close_status_code} - {close_msg}")
            if self.running:
                self.log.info("Reconectando em 5s...")
                time.sleep(5)
                self.gateway_connect()

        try:
            self.ws = websocket.WebSocketApp(
                DISCORD_GATEWAY,
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
                header=[f"Origin: https://discord.com"]
            )

            ws_thread = threading.Thread(target=self.ws.run_forever, kwargs={"ping_interval": 20}, daemon=True)
            ws_thread.start()
            self.threads.append(ws_thread)

        except Exception as e:
            self.log.error(f"Falha ao conectar Gateway: {e}")

    def _heartbeat_loop(self):
        """Loop de heartbeat para manter conexão Gateway"""
        while self.running and self.ws and self.heartbeat_interval:
            try:
                if self.ws.sock and self.ws.sock.connected:
                    self.ws.send(json.dumps({"op": 1, "d": self.sequence_number}))
                    self.log.debug("Heartbeat enviado")
                time.sleep(self.heartbeat_interval)
            except Exception as e:
                self.log.debug(f"Erro no heartbeat: {e}")
                break

    # ═══════════════════════════════════════════════════════════════════════════
    # MONITORAMENTO E PROTEÇÃO
    # ═══════════════════════════════════════════════════════════════════════════

    def monitor_account(self):
        """Thread de monitoramento contínuo da conta"""
        self.log.info("Iniciando monitoramento de conta...")

        while self.running:
            try:
                # Verifica dados do usuário
                response = self.request("GET", "/users/@me", bucket="profile")
                if response and response.status_code == 200:
                    data = response.json()

                    # Verifica flags de ban
                    flags = data.get("flags", 0)
                    public_flags = data.get("public_flags", 0)

                    # Verifica se há sinais de restrição
                    if data.get("discriminator") == "0" and not data.get("global_name"):
                        self.log.warn("Possível sinal de conta comprometida detectado!")

                    # Verifica verificação de email
                    if not data.get("verified", False):
                        self.log.warn("Email não verificado! Verifique sua conta.")

                    # Verifica MFA
                    if not data.get("mfa_enabled", False):
                        self.log.warn("MFA não está ativado! Recomendado para segurança.")

                # Verifica conexões
                response = self.request("GET", "/users/@me/connections", bucket="default")
                if response and response.status_code == 200:
                    connections = response.json()
                    self.log.debug(f"Conexões verificadas: {len(connections)}")

                # Verifica guilds
                response = self.request("GET", "/users/@me/guilds", bucket="guilds")
                if response and response.status_code == 200:
                    guilds = response.json()
                    if len(guilds) != len(self.guilds):
                        self.log.info(f"Mudança detectada: {len(guilds)} servidores (era {len(self.guilds)})")
                        self.guilds = guilds

                interval = self.config.get("monitor_interval", 60)
                time.sleep(interval)

            except Exception as e:
                self.log.debug(f"Erro no monitoramento: {e}")
                time.sleep(10)

    def activity_loop(self):
        """Loop principal de atividades humanas"""
        self.log.info("Iniciando simulação de atividade humana...")

        while self.running:
            try:
                self.perform_random_activity()
                interval = self.config.get("activity_interval", 30)
                # Adiciona variação aleatória
                sleep_time = interval + random.uniform(-5, 10)
                time.sleep(max(sleep_time, 5))
            except Exception as e:
                self.log.debug(f"Erro no loop de atividade: {e}")
                time.sleep(5)

    def stats_reporter(self):
        """Thread que reporta estatísticas periodicamente"""
        while self.running:
            time.sleep(300)  # A cada 5 minutos
            if not self.running:
                break

            uptime = time.time() - self.activity_stats["start_time"] if self.activity_stats["start_time"] else 0
            hours = int(uptime // 3600)
            minutes = int((uptime % 3600) // 60)

            self.log.banner(f"📊 ESTATÍSTICAS - {hours}h {minutes}m")
            self.log.info(f"Requests enviados: {self.activity_stats['requests_sent']}")
            self.log.info(f"Rate limits atingidos: {self.activity_stats['rate_limits_hit']}")
            self.log.info(f"Proxies utilizados: {self.activity_stats['proxies_used']}")
            self.log.info(f"Atividades realizadas: {self.activity_stats['activities_performed']}")
            self.log.info(f"Servidores: {len(self.guilds)} | Canais: {len(self.channels)} | DMs: {len(self.dms)}")

    # ═══════════════════════════════════════════════════════════════════════════
    # EXECUÇÃO PRINCIPAL
    # ═══════════════════════════════════════════════════════════════════════════

    def run(self):
        """Inicia o sistema Anti-Ban Resistência Forever"""
        self.running = True
        self.activity_stats["start_time"] = time.time()

        self.log.banner("🔥 ANTI BAN RESISTÊNCIA FOREVER 🔥")
        self.log.info("Inicializando sistema de proteção...")

        # Valida token
        if not self.validate_token():
            self.log.error("Não foi possível validar o token. Encerrando.")
            return

        # Carrega dados
        self.load_guilds()
        self.load_dms()

        # Conecta Gateway
        if self.config.get("gateway_enabled", True):
            self.gateway_connect()
            time.sleep(3)  # Aguarda conexão

        # Inicia threads
        threads_to_start = [
            ("Activity Loop", self.activity_loop),
            ("Monitor", self.monitor_account),
            ("Stats", self.stats_reporter),
        ]

        for name, target in threads_to_start:
            t = threading.Thread(target=target, daemon=True, name=name)
            t.start()
            self.threads.append(t)
            self.log.info(f"Thread '{name}' iniciada")

        self.log.banner("✅ SISTEMA ATIVO - RESISTÊNCIA FOREVER ✅")
        self.log.info("Pressione Ctrl+C para encerrar")

        # Loop principal
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.log.warn("Interrupção detectada. Encerrando...")
            self.stop()

    def stop(self):
        """Para o sistema de forma segura"""
        self.running = False
        self.log.info("Encerrando threads...")

        if self.ws:
            try:
                self.ws.close()
            except:
                pass

        self.executor.shutdown(wait=False)

        uptime = time.time() - self.activity_stats["start_time"] if self.activity_stats["start_time"] else 0
        self.log.banner(f"🛑 SISTEMA ENCERRADO - Uptime: {int(uptime)}s 🛑")


# ═══════════════════════════════════════════════════════════════════════════════
# CLI E MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def print_banner():
    """Banner ASCII da Resistência"""
    banner = f"""
{Fore.RED}    █████╗ ███╗   ██╗████████╗██╗██████╗  ██████╗ ███████╗███╗   ██╗
   ██╔══██╗████╗  ██║╚══██╔══╝██║██╔══██╗██╔═══██╗██╔════╝████╗  ██║
   ███████║██╔██╗ ██║   ██║   ██║██████╔╝██║   ██║█████╗  ██╔██╗ ██║
   ██╔══██║██║╚██╗██║   ██║   ██║██╔══██╗██║   ██║██╔══╝  ██║╚██╗██║
   ██║  ██║██║ ╚████║   ██║   ██║██║  ██║╚██████╔╝███████╗██║ ╚████║
   ╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝{Style.RESET_ALL}
{Fore.YELLOW}              🔥  RESISTÊNCIA FOREVER - ANTI BAN SYSTEM  🔥{Style.RESET_ALL}
{Fore.CYAN}    ═══════════════════════════════════════════════════════════════{Style.RESET_ALL}
    """
    print(banner)

def main():
    parser = argparse.ArgumentParser(
        description="Anti Ban Resistência Forever - Sistema de proteção Discord",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python anti_ban_resistencia_forever.py -t SEU_TOKEN_AQUI
  python anti_ban_resistencia_forever.py -t TOKEN --no-gateway
  python anti_ban_resistencia_forever.py -t TOKEN --delay-min 2 --delay-max 8
        """
    )

    parser.add_argument("-t", "--token", required=True, help="Token do Discord")
    parser.add_argument("--config", default="config.json", help="Caminho do arquivo de configuração")
    parser.add_argument("--no-gateway", action="store_true", help="Desabilitar conexão Gateway")
    parser.add_argument("--no-proxy", action="store_true", help="Desabilitar proxies")
    parser.add_argument("--no-typing", action="store_true", help="Desabilitar simulação de digitação")
    parser.add_argument("--no-presence", action="store_true", help="Desabilitar atualização de presença")
    parser.add_argument("--delay-min", type=float, default=1.0, help="Delay mínimo entre requests (segundos)")
    parser.add_argument("--delay-max", type=float, default=5.0, help="Delay máximo entre requests (segundos)")
    parser.add_argument("--activity-interval", type=int, default=30, help="Intervalo entre atividades (segundos)")
    parser.add_argument("--monitor-interval", type=int, default=60, help="Intervalo de monitoramento (segundos)")
    parser.add_argument("--unsafe", action="store_true", help="Modo inseguro (sem delays adicionais)")

    args = parser.parse_args()

    print_banner()

    # Cria instância
    bot = AntiBanResistenciaForever(token=args.token, config_path=args.config)

    # Sobrescreve config com argumentos CLI
    bot.config.update({
        "gateway_enabled": not args.no_gateway,
        "proxy_enabled": not args.no_proxy,
        "typing_enabled": not args.no_typing,
        "presence_enabled": not args.no_presence,
        "delay_min": args.delay_min,
        "delay_max": args.delay_max,
        "activity_interval": args.activity_interval,
        "monitor_interval": args.monitor_interval,
        "safe_mode": not args.unsafe,
    })

    # Salva config atualizada
    with open(args.config, "w", encoding="utf-8") as f:
        json.dump(bot.config, f, indent=4)

    # Executa
    try:
        bot.run()
    except Exception as e:
        print(f"{Fore.RED}Erro fatal: {e}{Style.RESET_ALL}")
        sys.exit(1)

if __name__ == "__main__":
    main()
