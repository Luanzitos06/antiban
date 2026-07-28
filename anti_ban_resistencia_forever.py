#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║           🔥 ANTI BAN RESISTÊNCIA FOREVER 🔥                                  ║
║                          (Versão 2026 Ultra)                                  ║
║                                                                              ║
║  Script de proteção e monitoramento de contas Discord                         ║
║  Fingerprint avançado + Proxies rotativos com teste de anonimato             ║
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
import re
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
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
# CONFIGURAÇÕES E CONSTANTES (ATUALIZADAS 2026)
# ═══════════════════════════════════════════════════════════════════════════════

DISCORD_API = "https://discord.com/api/v10"
DISCORD_GATEWAY = "wss://gateway.discord.gg/?v=10&encoding=json"

# Headers base (serão complementados dinamicamente)
BASE_HEADERS = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Connection": "keep-alive",
    "DNT": "1",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "X-Discord-Locale": "pt-BR",
    "X-Discord-Timezone": "America/Sao_Paulo",
}

# User-Agents ultra realistas (2026)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:126.0) Gecko/20100101 Firefox/126.0",
]

# Lista de plataformas para variar
PLATFORMS = ["Windows", "macOS", "Linux"]
OS_VERSIONS = {
    "Windows": ["10.0", "11.0"],
    "macOS": ["10.15.7", "11.0", "12.0", "13.0"],
    "Linux": ["5.15.0", "6.2.0", "6.5.0"]
}

# Atividades humanas
HUMAN_ACTIVITIES = [
    {"name": "typing_indicator", "weight": 30, "delay": (3, 15)},
    {"name": "presence_update", "weight": 20, "delay": (60, 300)},
    {"name": "guild_browse", "weight": 15, "delay": (10, 60)},
    {"name": "channel_read", "weight": 20, "delay": (5, 30)},
    {"name": "friend_check", "weight": 10, "delay": (30, 120)},
    {"name": "settings_check", "weight": 5, "delay": (60, 300)},
]

# Rate limits
RATE_LIMITS = {
    "default": {"limit": 50, "window": 1},
    "messages": {"limit": 5, "window": 5},
    "guilds": {"limit": 5, "window": 60},
    "channels": {"limit": 5, "window": 5},
    "reactions": {"limit": 1, "window": 0.25},
    "typing": {"limit": 1, "window": 10},
    "presence": {"limit": 5, "window": 60},
    "profile": {"limit": 2, "window": 60},
}

# ═══════════════════════════════════════════════════════════════════════════════
# GERENCIADOR DE FINGERPRINT (ULTRA REALISTA)
# ═══════════════════════════════════════════════════════════════════════════════

class FingerprintManager:
    """Gera fingerprints dinâmicos para cada sessão/request."""
    def __init__(self):
        self.device_id = str(uuid.uuid4())
        self.session_id = hashlib.sha256(os.urandom(32)).hexdigest()[:32]
        self._refresh()

    def _refresh(self):
        """Gera novo fingerprint."""
        self.platform = random.choice(PLATFORMS)
        self.os_version = random.choice(OS_VERSIONS.get(self.platform, ["10.0"]))
        self.browser_version = random.choice(["131.0.0.0", "130.0.0.0", "129.0.0.0", "128.0.0.0"])
        self.user_agent = random.choice(USER_AGENTS)
        # Ajusta o user-agent conforme a plataforma escolhida (simplificado)
        if self.platform == "Windows" and "Windows" not in self.user_agent:
            self.user_agent = self.user_agent.replace("X11; Linux", "Windows NT 10.0; Win64; x64")
        elif self.platform == "macOS" and "Mac" not in self.user_agent:
            self.user_agent = self.user_agent.replace("Windows NT 10.0; Win64; x64", "Macintosh; Intel Mac OS X 10_15_7")
        elif self.platform == "Linux" and "Linux" not in self.user_agent:
            self.user_agent = self.user_agent.replace("Windows NT 10.0; Win64; x64", "X11; Linux x86_64")

        self.sec_ch_ua = f'"Google Chrome";v="{self.browser_version.split(".")[0]}", "Chromium";v="{self.browser_version.split(".")[0]}", "Not?A_Brand";v="99"'
        self.sec_ch_ua_platform = f'"{self.platform}"'
        self.x_super_properties = self._build_super_properties()

    def _build_super_properties(self):
        """Gera o payload X-Super-Properties com campos avançados."""
        props = {
            "os": self.platform,
            "browser": "Chrome",
            "device": "",
            "system_locale": random.choice(["pt-BR", "en-US", "es-ES"]),
            "browser_user_agent": self.user_agent,
            "browser_version": self.browser_version,
            "os_version": self.os_version,
            "referrer": "",
            "referring_domain": "",
            "referrer_current": "",
            "referring_domain_current": "",
            "release_channel": "stable",
            "client_build_number": random.randint(250000, 260000),
            "client_event_source": None,
            "design_id": random.randint(0, 10),
            "device_id": self.device_id,
            "session_id": self.session_id,
        }
        import base64
        return base64.b64encode(json.dumps(props).encode()).decode()

    def get_headers(self):
        """Retorna cabeçalhos atualizados com fingerprint."""
        headers = {
            "User-Agent": self.user_agent,
            "Sec-Ch-Ua": self.sec_ch_ua,
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": self.sec_ch_ua_platform,
            "X-Super-Properties": self.x_super_properties,
        }
        return headers

    def rotate(self):
        """Rotaciona o fingerprint (gerar novo)."""
        self._refresh()
        return self

# ═══════════════════════════════════════════════════════════════════════════════
# GERENCIADOR DE PROXIES (COM TESTE DE ANONIMATO E MÚLTIPLAS FONTES)
# ═══════════════════════════════════════════════════════════════════════════════

class ProxyManager:
    """
    Gerencia proxies gratuitos com teste de anonimato (httpbin.org/ip).
    Mantém apenas proxies que realmente mascaram o IP.
    """
    def __init__(self, log, min_proxies=5, max_proxies=30, test_timeout=5):
        self.log = log
        self.min_proxies = min_proxies
        self.max_proxies = max_proxies
        self.test_timeout = test_timeout
        self.proxies = []          # proxies válidos (formato "ip:porta")
        self.lock = threading.Lock()
        self.current_index = 0
        self.failed_counts = {}
        self.last_refresh = 0
        self.refresh_interval = 900  # 15 minutos
        self.is_refreshing = False
        self.real_ip = self._get_real_ip()
        # Fontes de proxies (mais de 10 fontes)
        self.sources = [
            # ProxyScrape
            "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
            "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=https&timeout=10000&country=all&ssl=all&anonymity=all",
            # Geonode
            "https://proxylist.geonode.com/api/proxy-list?limit=100&page=1&sort_by=lastChecked&sort_type=desc&protocols=http%2Chttps",
            # Proxy-List (filtra por anonimato)
            "https://proxy-list.download/api/v1/?type=http&anon=elite",
            "https://proxy-list.download/api/v1/?type=https&anon=elite",
            # OpenProxyList
            "https://api.openproxylist.xyz/http.txt",
            "https://api.openproxylist.xyz/https.txt",
            # FreeProxyList (HTML)
            "https://free-proxy-list.net/",
            "https://www.sslproxies.org/",
            "https://www.us-proxy.org/",
            # PubProxy
            "http://pubproxy.com/api/proxy?limit=20&format=text&http=true&https=true",
        ]

    def _get_real_ip(self):
        """Obtém IP real da máquina."""
        try:
            resp = requests.get("http://httpbin.org/ip", timeout=5)
            if resp.status_code == 200:
                return resp.json().get("origin", "unknown")
        except:
            pass
        return "unknown"

    def _fetch_from_json_api(self, url):
        """Parseia APIs que retornam JSON com lista de proxies."""
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                proxies = []
                if isinstance(data, dict) and "data" in data:
                    for item in data["data"]:
                        ip = item.get("ip")
                        port = item.get("port")
                        if ip and port:
                            proxies.append(f"{ip}:{port}")
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            ip = item.get("ip") or item.get("address")
                            port = item.get("port")
                            if ip and port:
                                proxies.append(f"{ip}:{port}")
                        elif isinstance(item, str) and ":" in item:
                            proxies.append(item)
                return proxies
        except:
            pass
        return []

    def _fetch_from_source(self, url):
        """Baixa proxies de uma fonte (texto puro)."""
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                text = resp.text
                lines = text.splitlines()
                proxies = []
                for line in lines:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if ':' in line and not line.startswith('http'):
                        proxies.append(line)
                return proxies
        except:
            pass
        return []

    def _fetch_from_html(self, url):
        """Extrai proxies de páginas HTML."""
        try:
            headers = {'User-Agent': random.choice(USER_AGENTS)}
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}:\d{2,5}\b'
                proxies = re.findall(pattern, resp.text)
                return list(set(proxies))
        except:
            pass
        return []

    def fetch_free_proxies(self):
        """Busca proxies de todas as fontes."""
        all_proxies = set()
        self.log.debug("Buscando proxies gratuitos...")
        for source in self.sources:
            proxies = []
            if "geonode" in source or "proxy-list.download" in source:
                proxies = self._fetch_from_json_api(source)
            elif "proxyscrape" in source or "pubproxy" in source or "openproxylist" in source:
                proxies = self._fetch_from_source(source)
            else:
                proxies = self._fetch_from_html(source)
            if proxies:
                all_proxies.update(proxies)
                self.log.debug(f"Obtidos {len(proxies)} proxies de {source[:50]}")
        return list(all_proxies)

    def test_proxy(self, proxy):
        """Testa se o proxy é anônimo e funciona com o Discord."""
        proxy_url = f"http://{proxy}"
        proxies_dict = {"http": proxy_url, "https": proxy_url}
        # 1. Teste de anonimato via httpbin
        try:
            start = time.time()
            resp = requests.get("http://httpbin.org/ip", proxies=proxies_dict, timeout=self.test_timeout)
            if resp.status_code == 200:
                ip_data = resp.json()
                proxy_ip = ip_data.get("origin", "")
                if proxy_ip and proxy_ip != self.real_ip:
                    self.log.debug(f"Proxy {proxy} é anônimo (IP {proxy_ip} != {self.real_ip})")
                else:
                    self.log.debug(f"Proxy {proxy} é transparente ou falhou no anonimato.")
                    return False
            else:
                return False
        except Exception as e:
            self.log.debug(f"Proxy {proxy} falhou no teste de anonimato: {e}")
            return False

        # 2. Teste com Discord (endpoint leve)
        test_url = f"{DISCORD_API}/users/@me?with_analytics_token=false"
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "*/*",
            "Accept-Language": "pt-BR,pt;q=0.9",
        }
        try:
            resp = requests.get(test_url, headers=headers, proxies=proxies_dict, timeout=self.test_timeout)
            if resp.status_code in (200, 401, 403, 429):
                self.log.debug(f"Proxy {proxy} válido para Discord (status {resp.status_code})")
                return True
            else:
                self.log.debug(f"Proxy {proxy} inválido para Discord (status {resp.status_code})")
                return False
        except Exception as e:
            self.log.debug(f"Proxy {proxy} falhou no teste Discord: {e}")
            return False

    def refresh_proxies(self, force=False):
        """Atualiza a lista de proxies válidos."""
        if self.is_refreshing:
            return
        if not force and (time.time() - self.last_refresh) < self.refresh_interval:
            return

        with self.lock:
            if self.is_refreshing:
                return
            self.is_refreshing = True

        try:
            self.log.info("🔄 Atualizando lista de proxies gratuitos (testando anonimato)...")
            raw = self.fetch_free_proxies()
            if not raw:
                self.log.warn("Nenhum proxy obtido das fontes.")
                return

            random.shuffle(raw)
            valid = []
            tested = 0
            for proxy in raw:
                if tested >= self.max_proxies * 2:
                    break
                if self.test_proxy(proxy):
                    valid.append(proxy)
                    if len(valid) >= self.max_proxies:
                        break
                tested += 1

            if valid:
                with self.lock:
                    self.proxies = valid
                    self.failed_counts = {p: 0 for p in valid}
                    self.current_index = 0
                    self.last_refresh = time.time()
                self.log.info(f"✅ {len(valid)} proxies anônimos carregados.")
            else:
                self.log.warn("Nenhum proxy anônimo válido encontrado. Mantendo lista anterior.")
        except Exception as e:
            self.log.error(f"Erro ao atualizar proxies: {e}")
        finally:
            self.is_refreshing = False

    def get_proxy(self):
        """Retorna um proxy válido (round-robin) ou None."""
        with self.lock:
            if not self.proxies:
                return None
            attempts = 0
            while attempts < len(self.proxies):
                proxy = self.proxies[self.current_index]
                self.current_index = (self.current_index + 1) % len(self.proxies)
                if self.failed_counts.get(proxy, 0) < 2:
                    return proxy
                attempts += 1
            self.log.warn("Todos os proxies com muitas falhas. Recarregando...")
            self.refresh_proxies(force=True)
            if self.proxies:
                self.current_index = 0
                return self.proxies[0]
            return None

    def report_failure(self, proxy):
        """Registra falha (descarta após 2)."""
        with self.lock:
            if proxy in self.failed_counts:
                self.failed_counts[proxy] += 1
                if self.failed_counts[proxy] >= 2:
                    self.log.debug(f"Proxy {proxy} removido por muitas falhas.")
                    if proxy in self.proxies:
                        self.proxies.remove(proxy)
                    del self.failed_counts[proxy]
                    if not self.proxies:
                        self.log.warn("Lista de proxies vazia. Buscando novos...")
                        self.refresh_proxies(force=True)

    def report_success(self, proxy):
        """Reseta contagem de falhas."""
        with self.lock:
            if proxy in self.failed_counts:
                self.failed_counts[proxy] = max(0, self.failed_counts[proxy] - 1)

    def start_background_refresh(self):
        """Thread de atualização periódica."""
        def refresh_loop():
            while True:
                time.sleep(self.refresh_interval)
                if not self.is_refreshing:
                    self.refresh_proxies()
        t = threading.Thread(target=refresh_loop, daemon=True)
        t.start()

# ═══════════════════════════════════════════════════════════════════════════════
# LOGGER (sem alterações)
# ═══════════════════════════════════════════════════════════════════════════════

class ResistenciaLogger:
    def __init__(self, name="Resistencia"):
        self.name = name
        self.setup_logger()

    def setup_logger(self):
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.DEBUG)
        if not self.logger.handlers:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_format = logging.Formatter(
                f"{Fore.CYAN}[%(asctime)s]{Style.RESET_ALL} %(levelname)s %(message)s",
                datefmt="%H:%M:%S"
            )
            console_handler.setFormatter(console_format)
            self.logger.addHandler(console_handler)
            file_handler = logging.FileHandler("resistencia_forever.log", encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)
            file_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            file_handler.setFormatter(file_format)
            self.logger.addHandler(file_handler)

    def info(self, msg): self.logger.info(f"{Fore.GREEN}✓{Style.RESET_ALL} {msg}")
    def warn(self, msg): self.logger.warning(f"{Fore.YELLOW}⚠{Style.RESET_ALL} {msg}")
    def error(self, msg): self.logger.error(f"{Fore.RED}✗{Style.RESET_ALL} {msg}")
    def debug(self, msg): self.logger.debug(f"{Fore.MAGENTA}◆{Style.RESET_ALL} {msg}")
    def banner(self, msg):
        self.logger.info(f"{Fore.CYAN}╔{'═' * 58}╗{Style.RESET_ALL}")
        self.logger.info(f"{Fore.CYAN}║{Style.RESET_ALL} {msg:^56} {Fore.CYAN}║{Style.RESET_ALL}")
        self.logger.info(f"{Fore.CYAN}╚{'═' * 58}╝{Style.RESET_ALL}")

# ═══════════════════════════════════════════════════════════════════════════════
# CLASSE PRINCIPAL (com fingerprint e proxy manager atualizados)
# ═══════════════════════════════════════════════════════════════════════════════

class AntiBanResistenciaForever:
    def __init__(self, token, config_path="config.json"):
        self.token = token.strip()
        self.config_path = config_path
        self.log = ResistenciaLogger("ResistenciaForever")

        self.running = False
        self.user_data = None
        self.guilds = []
        self.channels = []
        self.dms = []

        self.rate_buckets = {}
        self.request_history = []
        self.global_rate_limit = {"remaining": 50, "reset_after": 1, "reset_time": time.time()}

        # Proxy Manager (agora com teste de anonimato)
        self.proxy_manager = ProxyManager(self.log)
        self.proxy_manager.refresh_proxies(force=True)

        # Fingerprint Manager (última geração)
        self.fingerprint = FingerprintManager()
        self.fingerprint_rotate_counter = 0
        self.fingerprint_rotate_interval = 50   # a cada 50 requests

        # Threads
        self.threads = []
        self.executor = ThreadPoolExecutor(max_workers=5)

        # Gateway
        self.ws = None
        self.heartbeat_interval = None
        self.sequence_number = None
        self.session_id = None

        self.last_typing = {}
        self.last_presence = 0
        self.activity_stats = {
            "requests_sent": 0,
            "rate_limits_hit": 0,
            "proxies_used": 0,
            "activities_performed": 0,
            "start_time": None,
        }

        self.load_config()
        self.proxy_manager.start_background_refresh()

    def load_config(self):
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
            "proxy_auto_refresh": True,
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

    def get_headers(self, extra=None):
        """Retorna cabeçalhos com fingerprint atualizado."""
        headers = BASE_HEADERS.copy()
        fp_headers = self.fingerprint.get_headers()
        headers.update(fp_headers)
        headers["Authorization"] = self.token
        if extra:
            headers.update(extra)
        return headers

    def get_proxy_dict(self):
        if not self.config.get("proxy_enabled", True):
            return None
        proxy_str = self.proxy_manager.get_proxy()
        if proxy_str:
            return {"http": f"http://{proxy_str}", "https": f"http://{proxy_str}"}
        return None

    def _rotate_fingerprint_if_needed(self):
        """Rotaciona fingerprint periodicamente."""
        self.fingerprint_rotate_counter += 1
        if self.fingerprint_rotate_counter >= self.fingerprint_rotate_interval:
            self.fingerprint.rotate()
            self.fingerprint_rotate_counter = 0
            self.log.debug("🔄 Fingerprint rotacionado.")

    # ------------------------------------------------------------
    # Os métodos check_rate_limit, update_rate_limit, request, 
    # validate_token, load_guilds, load_channels, load_dms,
    # activity_*, gateway_*, monitor_*, stats_*, run, stop
    # permanecem IGUAIS aos que você já tem, apenas ajuste no
    # método request para chamar _rotate_fingerprint_if_needed()
    # e usar o novo get_headers().
    # ------------------------------------------------------------

    def request(self, method, endpoint, bucket="default", data=None, headers=None, retries=0):
        self._rotate_fingerprint_if_needed()
        max_retries = self.config.get("max_retries", 3)
        if retries > max_retries:
            self.log.error(f"Máximo de retries atingido para {endpoint}")
            return None

        self.check_rate_limit(bucket)
        if self.config.get("safe_mode", True):
            delay = random.uniform(self.config.get("delay_min", 1.0), self.config.get("delay_max", 5.0))
            time.sleep(delay)

        url = f"{DISCORD_API}{endpoint}" if not endpoint.startswith("http") else endpoint
        req_headers = self.get_headers()
        if headers:
            req_headers.update(headers)

        proxies = self.get_proxy_dict()
        proxy_str = None
        if proxies:
            proxy_str = proxies.get("http", "").replace("http://", "")

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

            if not self.update_rate_limit(response):
                if proxy_str:
                    self.proxy_manager.report_success(proxy_str)
                return self.request(method, endpoint, bucket, data, headers, retries + 1)

            if response.status_code in [200, 201, 204]:
                self.log.debug(f"{method} {endpoint} → {response.status_code}")
                if proxy_str:
                    self.proxy_manager.report_success(proxy_str)
                return response
            elif response.status_code == 401:
                self.log.error("Token inválido ou expirado!")
                self.running = False
                return None
            elif response.status_code == 403:
                self.log.warn(f"Forbidden: {endpoint}")
                if proxy_str:
                    self.proxy_manager.report_failure(proxy_str)
                return response
            else:
                self.log.warn(f"{method} {endpoint} → {response.status_code}")
                if proxy_str and response.status_code >= 500:
                    self.proxy_manager.report_failure(proxy_str)
                return response

        except requests.exceptions.ProxyError as e:
            self.log.warn(f"Erro de proxy: {e}")
            if proxy_str:
                self.proxy_manager.report_failure(proxy_str)
            try:
                self.log.info("Tentando sem proxy...")
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
            if proxy_str:
                self.proxy_manager.report_failure(proxy_str)
            time.sleep(2)
            return self.request(method, endpoint, bucket, data, headers, retries + 1)

    # Os demais métodos (validate_token, load_guilds, etc.) permanecem idênticos
    # ao seu código original, apenas certifique-se de que usam self.request()
    # e self.get_headers() quando necessário.

    # Para economizar espaço, não repetirei todo o resto, mas você deve manter
    # todos os métodos que já existem (activity_*, gateway_*, monitor_*, run, stop).
    # Apenas substitua os métodos acima (request e get_headers) e adicione
    # o FingerprintManager e o ProxyManager melhorado.

# O restante do código (print_banner, main, CLI) permanece inalterado.

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN (sem alterações)
# ═══════════════════════════════════════════════════════════════════════════════

def print_banner():
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
        description="Anti Ban Resistência Forever - Sistema de proteção Discord (2026 Ultra)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python anti_ban_resistencia_forever.py -t SEU_TOKEN_AQUI
  python anti_ban_resistencia_forever.py -t TOKEN --no-gateway --no-proxy
  python anti_ban_resistencia_forever.py -t TOKEN --delay-min 2 --delay-max 8
        """
    )
    parser.add_argument("-t", "--token", required=True, help="Token do Discord")
    parser.add_argument("--config", default="config.json", help="Caminho do arquivo de configuração")
    parser.add_argument("--no-gateway", action="store_true", help="Desabilitar conexão Gateway")
    parser.add_argument("--no-proxy", action="store_true", help="Desabilitar uso de proxies")
    parser.add_argument("--no-typing", action="store_true", help="Desabilitar simulação de digitação")
    parser.add_argument("--no-presence", action="store_true", help="Desabilitar atualização de presença")
    parser.add_argument("--delay-min", type=float, default=1.0, help="Delay mínimo entre requests (segundos)")
    parser.add_argument("--delay-max", type=float, default=5.0, help="Delay máximo entre requests (segundos)")
    parser.add_argument("--activity-interval", type=int, default=30, help="Intervalo entre atividades (segundos)")
    parser.add_argument("--monitor-interval", type=int, default=60, help="Intervalo de monitoramento (segundos)")
    parser.add_argument("--unsafe", action="store_true", help="Modo inseguro (sem delays adicionais)")

    args = parser.parse_args()
    print_banner()

    bot = AntiBanResistenciaForever(token=args.token, config_path=args.config)

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

    with open(args.config, "w", encoding="utf-8") as f:
        json.dump(bot.config, f, indent=4)

    try:
        bot.run()
    except Exception as e:
        print(f"{Fore.RED}Erro fatal: {e}{Style.RESET_ALL}")
        sys.exit(1)

if __name__ == "__main__":
    main()
