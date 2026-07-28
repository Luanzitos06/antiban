#!/usr/bin/env python3
"""
start.py - Launcher inteligente do Anti Ban Resistência 2026
  1. Verifica / cria ambiente virtual (venv_resistencia)
  2. Instala todas as dependências automaticamente
  3. Pede o token (argumento ou interativo) e inicia o bot
  4. Durante a execução, digite 'r' + Enter para recarregar proxies
"""

import os
import sys
import subprocess
import platform
import threading

# ═══════════════ CONFIGURAÇÕES ═══════════════
VENV_DIR = "venv_resistencia"
REQUIREMENTS = [
    "requests>=2.31.0",
    "colorama>=0.4.6",
    "websocket-client>=1.6.0",   # opcional, para gateway
]
# Nome correto do script principal
MAIN_SCRIPT = "anti_ban_resistencia_forever.py"
# ══════════════════════════════════════════════

def check_python():
    if sys.version_info < (3, 8):
        print("ERRO: Python 3.8 ou superior é necessário.")
        sys.exit(1)

def create_venv():
    if not os.path.exists(VENV_DIR):
        print(f"[+] Criando ambiente virtual em '{VENV_DIR}'...")
        subprocess.check_call([sys.executable, "-m", "venv", VENV_DIR])
    else:
        print(f"[✓] Ambiente virtual '{VENV_DIR}' já existe.")

def get_venv_python():
    if platform.system() == "Windows":
        return os.path.join(VENV_DIR, "Scripts", "python.exe")
    return os.path.join(VENV_DIR, "bin", "python")

def install_deps():
    venv_python = get_venv_python()
    print("[+] Instalando dependências...")
    subprocess.check_call([venv_python, "-m", "pip", "install", "--upgrade", "pip"])
    for req in REQUIREMENTS:
        subprocess.check_call([venv_python, "-m", "pip", "install", req])
    print("[✓] Todas as dependências instaladas.")

def get_token():
    """Obtém o token: 1º argumento -t/--token, 2º variável de ambiente, 3º input."""
    # Procura pelo argumento -t ou --token e o próximo valor
    args = sys.argv[1:]
    for i, arg in enumerate(args):
        if arg in ("-t", "--token"):
            if i + 1 < len(args):
                return args[i + 1]
            else:
                print("ERRO: Nenhum token após -t/--token")
                sys.exit(1)

    # Tenta variável de ambiente
    env_token = os.environ.get("DISCORD_TOKEN")
    if env_token:
        return env_token

    # Pede interativamente
    print("\nNenhum token fornecido.")
    return input("Insira o token do Discord: ").strip()

def run_bot(token):
    venv_python = get_venv_python()
    print(f"\n[+] Iniciando o bot com o token...\n{'='*50}\n")

    # Comando para rodar o script principal
    cmd = [venv_python, MAIN_SCRIPT, "-t", token]

    # Inicia como subprocesso, capturando stdin/stdout
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=sys.stdout,
        stderr=sys.stderr,
        text=True,
        bufsize=1
    )

    print("\n💡 Dica: digite 'r' + Enter a qualquer momento para recarregar proxies.\n")

    # Thread para enviar comandos via stdin do processo filho
    def input_listener():
        while proc.poll() is None:
            try:
                user_input = input()
                if user_input.strip().lower() == "r":
                    proc.stdin.write("r\n")
                    proc.stdin.flush()
                    print("[+] Comando 'r' enviado para recarregar proxies.")
            except EOFError:
                break
            except KeyboardInterrupt:
                proc.terminate()
                break

    listener = threading.Thread(target=input_listener, daemon=True)
    listener.start()

    # Aguarda o bot terminar
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        print("\n[!] Bot encerrado pelo usuário.")

def main():
    check_python()
    create_venv()
    install_deps()
    token = get_token()
    if not token:
        print("Token inválido. Encerrando.")
        sys.exit(1)
    run_bot(token)

if __name__ == "__main__":
    main()
