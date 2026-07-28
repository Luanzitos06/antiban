#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║           🔥 ANTI BAN RESISTÊNCIA FOREVER 2026 ULTRA 🔥                      ║
║                                                                              ║
║  Sistema de proteção com proxy rotativo anônimo e fingerprint de última      ║
║  geração. O Discord enxerga sempre um novo dispositivo e IP.                ║
║                                                                              ║
║  ⚠️  USO EDUCACIONAL – self-bots violam os Termos de Serviço do Discord.     ║
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
import base64
import re
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

# Cores opcionais
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    class Fore: pass
    class Style: pass

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTES 2026
# ═══════════════════════════════════════════════════════════════════════════════

DISCORD_API = "https://discord.com/api/v10"
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:126.0) Gecko/20100101 Firefox/126.0",
]

# Build numbers recentes do Discord (canary/stable) – extraídos de versões públicas
DISCORD_BUILD_NUMBERS = [261450, 261200, 260950, 260800, 260600, 260350]

# Fontes de proxies gratuitos – atualizadas e com alta disponibilidade
PROXY_SOURCES = [
    # ProxyScrape v2
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=elite",
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=https&timeout=10000&country=all&ssl=all&anonymity=elite",
    # Geonode
    "https://proxylist.geonode.com/api/proxy-list?limit=100&page=1&sort_by=lastChecked&sort_type=desc&protocols=http%2Chttps",
    # Proxy-List.download
    "https://proxy-list.download/api/v1/?type=http&anon=elite",
    "https://proxy-list.download/api/v1/?type=https&anon=elite",
    # OpenProxyList
    "https://api.openproxylist.xyz/http.txt",
    "https://api.openproxylist.xyz/https.txt",
    # PubProxy
    "http://pubproxy.com/api/proxy?limit=20&format=text&http=true&https=true",
    # Free-Proxy-List.net (HTML)
    "https://free-proxy-list.net/",
    "https://www.sslproxies.org/",
    "https://www.us-proxy.org/",
]

CACHE_FILE = "proxies_cache.json"  # persistência de proxies bons

# ═══════════════════════════════════════════════════════════════════════════════
# LOGGER
# ═══════════════════════════════════════════════════════════════════════════════

class Logger:
    def __init__(self, name="Resistencia"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        if not self.logger.handlers:
            ch = logging.StreamHandler(sys.stdout)
            ch.setLevel(logging.INFO)
            formatter = logging.Formatter(
                f"{Fore.CYAN}[%(asctime)s]{Style.RESET_ALL} %(levelname)s %(message)s",
                datefmt="%H:%M:%S"
            )
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)
            fh = logging.FileHandler("resistencia.log", encoding="utf-8")
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
            self.logger.addHandler(fh)

    def info(self, msg): self.logger.info(f"{Fore.GREEN}✓{Style.RESET_ALL} {msg}")
    def warn(self, msg): self.logger.warning(f"{Fore.YELLOW}⚠{Style.RESET_ALL} {msg}")
    def error(self, msg): self.logger.error(f"{Fore.RED}✗{Style.RESET_ALL} {msg}")
    def debug(self, msg): self.logger.debug(f"{Fore.MAGENTA}◆{Style.RESET_ALL} {msg}")

# ═══════════════════════════════════════════════════════════════════════════════
# FINGERPRINT AVANÇADO (chrome 131+)
# ═══════════════════════════════════════════════════════════════════════════════

class Fingerprint:
    def __init__(self):
        self.device_id = str(uuid.uuid4())
        self.session_id = hashlib.sha256(os.urandom(32)).hexdigest()[:32]
        self._refresh()

    def _refresh(self):
        self.platform = random.choice(["Windows", "macOS", "Linux"])
        if self.platform == "Windows":
            self.os_version = random.choice(["10.0", "11.0"])
            self.user_agent = random.choice([ua for ua in USER_AGENTS if "Windows" in ua])
        elif self.platform == "macOS":
            self.os_version = random.choice(["10.15.7", "11.6.2", "12.4", "13.2"])
            self.user_agent = random.choice([ua for ua in USER_AGENTS if "Mac" in ua])
        else:
            self.os_version = random.choice(["5.15.0", "6.2.0", "6.5.0"])
            self.user_agent = random.choice([ua for ua in USER_AGENTS if "Linux" in ua])

        # Build number real do Discord (algum cliente recente)
        self.build_number = random.choice(DISCORD_BUILD_NUMBERS)
        self.chrome_version = "131.0.0.0"  # fixo, mas pode variar
        self.locale = random.choice(["pt-BR", "en-US", "es-ES"])
        self.timezone = random.choice(["America/Sao_Paulo", "America/New_York", "Europe/London"])

        # Super properties
        props = {
            "os": self.platform,
            "browser": "Chrome",
            "device": "",
            "system_locale": self.locale,
            "browser_user_agent": self.user_agent,
            "browser_version": self.chrome_version,
            "os_version": self.os_version,
            "referrer": "",
            "referring_domain": "",
            "referrer_current": "",
            "referring_domain_current": "",
            "release_channel": "stable",
            "client_build_number": self.build_number,
            "client_event_source": None,
            "design_id": random.randint(0, 10),
            "device_id": self.device_id,
            "session_id": self.session_id,
        }
        self.x_super = base64.b64encode(json.dumps(props).encode()).decode()

    def get_headers(self):
        return {
            "User-Agent": self.user_agent,
            "Sec-Ch-Ua": f'"Chromium";v="{self.chrome_version.split(".")[0]}", "Google Chrome";v="{self.chrome_version.split(".")[0]}", "Not?A_Brand";v="99"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": f'"{self.platform}"',
            "Sec-Ch-Ua-Arch": random.choice(['"x86"', '"ARM"']),
            "Sec-Ch-Ua-Bitness": random.choice(['"64"', '"32"']),
            "Sec-Ch-Ua-Full-Version": f'"{self.chrome_version}"',
            "X-Super-Properties": self.x_super,
            "X-Discord-Locale": self.locale,
            "X-Discord-Timezone": self.timezone,
        }

    def rotate(self):
        self._refresh()

# ═══════════════════════════════════════════════════════════════════════════════
# GERENCIADOR DE PROXIES (ULTRA 2026)
# ═══════════════════════════════════════════════════════════════════════════════

class ProxyPool:
    def __init__(self, log: Logger, min_proxies=5, max_proxies=30):
        self.log = log
        self.min_proxies = min_proxies
        self.max_proxies = max_proxies
        self.proxies = []           # lista de ip:porta válidos
        self.failed_counts = {}
        self.lock = threading.Lock()
        self.current_index = 0
        self.last_refresh = 0
        self.refresh_interval = 600  # 10 minutos
        self.is_refreshing = False
        self.real_ip = self._get_real_ip()
        self.load_cache()

    def _get_real_ip(self):
        try:
            r = requests.get("http://httpbin.org/ip", timeout=5)
            if r.ok:
                return r.json().get("origin", "unknown")
        except:
            pass
        return "unknown"

    # ---------- persistência ----------
    def load_cache(self):
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r") as f:
                    cached = json.load(f)
                    if isinstance(cached, list):
                        with self.lock:
                            self.proxies = cached
                        self.log.info(f"✅ {len(self.proxies)} proxies carregados do cache.")
            except:
                pass

    def save_cache(self):
        with self.lock:
            try:
                with open(CACHE_FILE, "w") as f:
                    json.dump(self.proxies, f)
            except:
                pass

    # ---------- coleta de fontes ----------
    def _fetch_text(self, url):
        try:
            resp = requests.get(url, timeout=10, headers={"User-Agent": random.choice(USER_AGENTS)})
            if resp.status_code == 200:
                return re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{2,5}', resp.text)
        except:
            pass
        return []

    def _fetch_json(self, url):
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                proxies = []
                items = data if isinstance(data, list) else data.get("data", [])
                for item in items:
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

    def fetch_all(self):
        raw = set()
        for src in PROXY_SOURCES:
            if "geonode" in src or "proxy-list.download" in src:
                raw.update(self._fetch_json(src))
            else:
                raw.update(self._fetch_text(src))
        return list(raw)

    # ---------- teste de qualidade ----------
    def test_proxy(self, proxy):
        """Retorna True se o proxy for anônimo e acessar o Discord."""
        proxy_url = f"http://{proxy}"
        pd = {"http": proxy_url, "https": proxy_url}
        # 1. Anonimato
        try:
            r = requests.get("http://httpbin.org/ip", proxies=pd, timeout=8)
            if r.status_code != 200 or r.json().get("origin") == self.real_ip:
                return False
        except:
            return False
        # 2. Discord
        try:
            headers = {
                "User-Agent": random.choice(USER_AGENTS),
                "Accept": "*/*"
            }
            r = requests.get(f"{DISCORD_API}/users/@me", headers=headers, proxies=pd, timeout=8)
            if r.status_code in (200, 401, 403, 429):
                return True
        except:
            pass
        return False

    # ---------- refresh ----------
    def refresh(self, force=False):
        if self.is_refreshing:
            return
        if not force and time.time() - self.last_refresh < self.refresh_interval:
            return
        with self.lock:
            if self.is_refreshing:
                return
            self.is_refreshing = True

        try:
            self.log.info("🔄 Coletando novos proxies anônimos...")
            raw = self.fetch_all()
            if not raw:
                self.log.warn("Nenhum proxy obtido das fontes.")
                return
            random.shuffle(raw)
            valid = []
            tested = 0
            for proxy in raw:
                if tested >= self.max_proxies * 3:
                    break
                if self.test_proxy(proxy):
                    valid.append(proxy)
                tested += 1
            if valid:
                with self.lock:
                    self.proxies = valid
                    self.failed_counts = {p: 0 for p in valid}
                    self.current_index = 0
                    self.last_refresh = time.time()
                self.save_cache()
                self.log.info(f"✅ {len(valid)} proxies anônimos carregados.")
            else:
                self.log.warn("Nenhum proxy anônimo válido. Mantendo pool atual.")
        except Exception as e:
            self.log.error(f"Erro no refresh: {e}")
        finally:
            self.is_refreshing = False

    # ---------- obtenção ----------
    def get(self):
        """Retorna um proxy (ip:porta) ou None."""
        with self.lock:
            if not self.proxies:
                return None
            # round-robin inteligente
            attempts = 0
            while attempts < len(self.proxies):
                proxy = self.proxies[self.current_index]
                self.current_index = (self.current_index + 1) % len(self.proxies)
                if self.failed_counts.get(proxy, 0) < 2:
                    return proxy
                attempts += 1
            # todos falharam -> força refresh
            self.log.warn("Todos os proxies com falhas. Forçando refresh...")
            self.refresh(force=True)
            if self.proxies:
                self.current_index = 0
                return self.proxies[0]
            return None

    def report_success(self, proxy):
        with self.lock:
            if proxy in self.failed_counts:
                self.failed_counts[proxy] = max(0, self.failed_counts[proxy] - 1)

    def report_failure(self, proxy):
        with self.lock:
            if proxy not in self.failed_counts:
                return
            self.failed_counts[proxy] += 1
            if self.failed_counts[proxy] >= 2:
                if proxy in self.proxies:
                    self.proxies.remove(proxy)
                del self.failed_counts[proxy]
                self.save_cache()
                if not self.proxies:
                    self.log.warn("Pool vazio após remoção. Iniciando refresh imediato.")
                    threading.Thread(target=self.refresh, args=(True,), daemon=True).start()

    def start_background_refresh(self):
        def loop():
            while True:
                time.sleep(self.refresh_interval)
                if not self.is_refreshing:
                    self.refresh()
        threading.Thread(target=loop, daemon=True).start()

# ═══════════════════════════════════════════════════════════════════════════════
# BOT PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

class AntiBanResistencia:
    def __init__(self, token: str, config_path="config.json"):
        self.token = token.strip()
        self.config_path = config_path
        self.log = Logger("Resistencia2026")
        self.config = {
            "delay_min": 1.0,
            "delay_max": 5.0,
            "proxy_enabled": True,
            "activity_interval": 30,
            "max_retries": 3,
        }
        self.load_config()

        self.running = False
        self.fingerprint = Fingerprint()
        self.fingerprint_rotate_counter = 0
        self.proxy_pool = ProxyPool(self.log)
        self.proxy_pool.refresh(force=True)
        self.proxy_pool.start_background_refresh()
        self.activity_stats = {
            "requests_sent": 0,
            "rate_limits_hit": 0,
            "proxies_used": 0,
            "start_time": None,
        }

        # Rate limit buckets simples
        self.rate_buckets = {
            "default": {"remaining": 50, "reset_time": time.time() + 1},
            "messages": {"remaining": 5, "reset_time": time.time() + 5},
        }

    def load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    self.config.update(loaded)
            except:
                pass
        else:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4)
            self.log.info(f"Configuração padrão salva em {self.config_path}")

    def _check_rate_limit(self, bucket="default"):
        b = self.rate_buckets.get(bucket)
        if not b:
            return
        if time.time() < b["reset_time"] and b["remaining"] <= 0:
            sleep_time = b["reset_time"] - time.time() + random.uniform(0.5, 2)
            self.log.debug(f"⏳ Rate limit ({bucket}), aguardando {sleep_time:.1f}s")
            time.sleep(sleep_time)
        # reset periódico
        if time.time() >= b["reset_time"]:
            b["remaining"] = 50 if bucket == "default" else 5
            b["reset_time"] = time.time() + (1 if bucket == "default" else 5)

    def _update_rate_limit(self, bucket, response):
        remaining = response.headers.get("X-RateLimit-Remaining")
        reset_after = response.headers.get("X-RateLimit-Reset-After")
        if remaining is not None:
            b = self.rate_buckets.setdefault(bucket, {})
            b["remaining"] = int(remaining)
            if reset_after:
                b["reset_time"] = time.time() + float(reset_after)
        if response.status_code == 429:
            self.activity_stats["rate_limits_hit"] += 1
            retry_after = response.json().get("retry_after", 5)
            self.log.warn(f"🚫 Rate limit global. Aguardando {retry_after}s")
            time.sleep(retry_after + random.uniform(1, 3))
            return False
        return True

    def _get_headers(self, extra=None):
        headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": f"{self.fingerprint.locale},en;q=0.9",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "DNT": "1",
            "Connection": "keep-alive",
        }
        headers.update(self.fingerprint.get_headers())
        headers["Authorization"] = self.token
        if extra:
            headers.update(extra)
        return headers

    def _rotate_fingerprint(self):
        self.fingerprint_rotate_counter += 1
        if self.fingerprint_rotate_counter >= 50:
            self.fingerprint.rotate()
            self.fingerprint_rotate_counter = 0
            self.log.debug("🔄 Fingerprint rotacionado.")

    def _get_proxy(self):
        if not self.config.get("proxy_enabled", True):
            return None
        return self.proxy_pool.get()

    def request(self, method, endpoint, bucket="default", data=None, headers=None, retries=0):
        if retries > self.config.get("max_retries", 3):
            self.log.error(f"Máximo de retries atingido para {endpoint}")
            return None

        self._rotate_fingerprint()
        self._check_rate_limit(bucket)

        if self.config.get("safe_mode", True):
            delay = random.uniform(self.config.get("delay_min", 1.0), self.config.get("delay_max", 5.0))
            time.sleep(delay)

        url = f"{DISCORD_API}{endpoint}" if not endpoint.startswith("http") else endpoint
        req_headers = self._get_headers()
        if headers:
            req_headers.update(headers)

        proxy_ip = self._get_proxy()
        proxies = None
        if proxy_ip:
            proxies = {"http": f"http://{proxy_ip}", "https": f"http://{proxy_ip}"}

        try:
            self.activity_stats["requests_sent"] += 1
            if proxies:
                self.activity_stats["proxies_used"] += 1

            if method == "GET":
                resp = requests.get(url, headers=req_headers, proxies=proxies, timeout=15)
            elif method == "POST":
                resp = requests.post(url, headers=req_headers, json=data, proxies=proxies, timeout=15)
            elif method == "PUT":
                resp = requests.put(url, headers=req_headers, json=data, proxies=proxies, timeout=15)
            elif method == "PATCH":
                resp = requests.patch(url, headers=req_headers, json=data, proxies=proxies, timeout=15)
            elif method == "DELETE":
                resp = requests.delete(url, headers=req_headers, proxies=proxies, timeout=15)
            else:
                return None

            ok = self._update_rate_limit(bucket, resp)
            if not ok:
                return self.request(method, endpoint, bucket, data, headers, retries + 1)

            if resp.status_code in (200, 201, 204):
                if proxy_ip:
                    self.proxy_pool.report_success(proxy_ip)
                return resp
            elif resp.status_code == 401:
                self.log.error("Token inválido. Encerrando.")
                self.running = False
                return None
            elif resp.status_code == 403:
                self.log.warn(f"Acesso negado: {endpoint}")
                if proxy_ip:
                    self.proxy_pool.report_failure(proxy_ip)
                return resp
            else:
                self.log.warn(f"{method} {endpoint} → {resp.status_code}")
                if proxy_ip and resp.status_code >= 500:
                    self.proxy_pool.report_failure(proxy_ip)
                return resp

        except requests.exceptions.ProxyError as e:
            self.log.warn(f"Proxy {proxy_ip} falhou: {e}")
            if proxy_ip:
                self.proxy_pool.report_failure(proxy_ip)
            # Tenta próximo proxy
            return self.request(method, endpoint, bucket, data, headers, retries + 1)

        except Exception as e:
            self.log.error(f"Erro na requisição: {e}")
            if proxy_ip:
                self.proxy_pool.report_failure(proxy_ip)
            time.sleep(2)
            return self.request(method, endpoint, bucket, data, headers, retries + 1)

    def validate_token(self):
        resp = self.request("GET", "/users/@me")
        if resp and resp.status_code == 200:
            self.user_data = resp.json()
            self.log.info(f"Conta conectada: {self.user_data.get('username')}#{self.user_data.get('discriminator', '0')}")
            return True
        return False

    def run(self):
        self.running = True
        self.activity_stats["start_time"] = datetime.now()
        if not self.validate_token():
            self.log.error("Token inválido. Abortando.")
            return

        # ═══════════════════════════════════════════════════════════
        # THREAD PARA COMANDOS INTERATIVOS (recarregar proxies)
        def stdin_listener():
            while self.running:
                try:
                    cmd = sys.stdin.readline().strip().lower()
                    if cmd == "r":
                        self.log.info("🔄 Recarregando proxies (comando 'r')...")
                        self.proxy_pool.refresh(force=True)
                except:
                    pass

        threading.Thread(target=stdin_listener, daemon=True).start()
        # ═══════════════════════════════════════════════════════════

        self.log.info("Sistema Anti-Ban ativo. Pressione Ctrl+C para parar.")
        while self.running:
            # Simula atividade humana leve (typing aleatório, presença)
            time.sleep(random.uniform(10, 30))
            self.request("GET", "/users/@me/affinities/guilds", bucket="default")
        self.log.info("Encerrado.")

    def stop(self):
        self.running = False

# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def print_banner():
    print(f"""{Fore.RED}
    █████╗ ███╗   ██╗████████╗██╗██████╗  ██████╗ ███████╗███╗   ██╗
   ██╔══██╗████╗  ██║╚══██╔══╝██║██╔══██╗██╔═══██╗██╔════╝████╗  ██║
   ███████║██╔██╗ ██║   ██║   ██║██████╔╝██║   ██║█████╗  ██╔██╗ ██║
   ██╔══██║██║╚██╗██║   ██║   ██║██╔══██╗██║   ██║██╔══╝  ██║╚██╗██║
   ██║  ██║██║ ╚████║   ██║   ██║██║  ██║╚██████╔╝███████╗██║ ╚████║
   ╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝{Style.RESET_ALL}
{Fore.YELLOW}              🔥  RESISTÊNCIA FOREVER 2026 ULTRA  🔥{Style.RESET_ALL}
{Fore.CYAN}    ═══════════════════════════════════════════════════════════════{Style.RESET_ALL}
    """)

def main():
    parser = argparse.ArgumentParser(description="Anti Ban Resistência 2026 Ultra")
    parser.add_argument("-t", "--token", required=True, help="Token do Discord")
    parser.add_argument("--config", default="config.json", help="Caminho da config")
    parser.add_argument("--no-proxy", action="store_true", help="Desabilitar proxies")
    parser.add_argument("--delay-min", type=float, default=1.0)
    parser.add_argument("--delay-max", type=float, default=5.0)
    args = parser.parse_args()
    print_banner()

    bot = AntiBanResistencia(args.token, args.config)
    if args.no_proxy:
        bot.config["proxy_enabled"] = False
    bot.config.update({
        "delay_min": args.delay_min,
        "delay_max": args.delay_max,
    })
    with open(args.config, "w") as f:
        json.dump(bot.config, f, indent=4)

    try:
        bot.run()
    except KeyboardInterrupt:
        bot.stop()
        print("\nEncerrado pelo usuário.")
    except Exception as e:
        print(f"{Fore.RED}Erro: {e}{Style.RESET_ALL}")
        sys.exit(1)

if __name__ == "__main__":
    main()
