#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Launcher do Anti Ban Resistência Forever
- Cria ambiente virtual automaticamente
- Instala dependências dentro do venv
- Solicita o token e executa o script principal
"""

import subprocess
import sys
import os
import json
import getpass
import platform
import venv

REQUIRED_PACKAGES = ["requests", "websocket-client", "colorama"]
MAIN_SCRIPT = "anti_ban_resistencia_forever.py"
VENV_DIR = "venv_resistencia"

def create_venv():
    """Cria o ambiente virtual se não existir."""
    if not os.path.isdir(VENV_DIR):
        print(f"🔧 Criando ambiente virtual em {VENV_DIR}...")
        builder = venv.EnvBuilder(with_pip=True)
        builder.create(VENV_DIR)
        print("✅ Ambiente virtual criado.")
    else:
        print(f"✅ Ambiente virtual {VENV_DIR} já existe.")

def get_venv_python():
    """Retorna o caminho para o Python dentro do venv."""
    if platform.system() == "Windows":
        return os.path.join(VENV_DIR, "Scripts", "python.exe")
    else:
        return os.path.join(VENV_DIR, "bin", "python")

def install_packages():
    """Instala pacotes necessários dentro do venv."""
    python = get_venv_python()
    print("🔍 Verificando dependências...")
    for pkg in REQUIRED_PACKAGES:
        # Tenta importar dentro do venv
        try:
            subprocess.check_call([python, "-c", f"import {pkg.replace('-', '_')}"], 
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"✅ {pkg} já instalado.")
        except subprocess.CalledProcessError:
            print(f"📦 Instalando {pkg}...")
            subprocess.check_call([python, "-m", "pip", "install", pkg])

def check_main_script():
    """Verifica se o script principal existe."""
    if not os.path.isfile(MAIN_SCRIPT):
        print(f"❌ Erro: {MAIN_SCRIPT} não encontrado no diretório atual.")
        print("   Certifique-se de que ele está no mesmo local que este launcher.")
        sys.exit(1)

def get_token():
    """Solicita o token ao usuário de forma segura."""
    print("\n" + "="*50)
    print("🔑  INSIRA O TOKEN DA SUA CONTA DISCORD")
    print("="*50)
    token = getpass.getpass("Token: ")
    if not token.strip():
        print("❌ Token vazio. Encerrando.")
        sys.exit(1)
    return token.strip()

def save_token(token, filename="token.txt"):
    """Salva o token em um arquivo (opcional)."""
    save = input("Deseja salvar o token para uso futuro? (s/N): ").strip().lower()
    if save == "s":
        with open(filename, "w") as f:
            f.write(token)
        print(f"✅ Token salvo em {filename}")
        return True
    return False

def load_saved_token(filename="token.txt"):
    """Tenta carregar token salvo anteriormente."""
    if os.path.isfile(filename):
        with open(filename, "r") as f:
            token = f.read().strip()
        if token:
            return token
    return None

def run_main_script(token, extra_args=None):
    """Executa o script principal usando o Python do venv."""
    python = get_venv_python()
    cmd = [python, MAIN_SCRIPT, "-t", token]
    if extra_args:
        cmd.extend(extra_args)
    print("\n🚀 Iniciando Anti Ban Resistência Forever...\n")
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n⏹️  Encerrado pelo usuário.")
    except Exception as e:
        print(f"❌ Erro ao executar: {e}")

def main():
    # Verifica script principal
    check_main_script()

    # Cria ambiente virtual
    create_venv()

    # Instala dependências no venv
    install_packages()

    # Tenta carregar token salvo
    token = load_saved_token()
    if token:
        use_saved = input(f"Token salvo encontrado. Usar? (S/n): ").strip().lower()
        if use_saved == "n":
            token = None

    if not token:
        token = get_token()
        save_token(token)  # pergunta se quer salvar

    # Argumentos adicionais
    print("\n⚙️  Opções extras (pressione Enter para pular):")
    extra = input("Ex: --no-gateway --delay-min 2 (ou deixe vazio): ").strip()
    extra_args = extra.split() if extra else []

    # Executa
    run_main_script(token, extra_args)

if __name__ == "__main__":
    main()
