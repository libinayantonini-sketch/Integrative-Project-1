"""Cria o banco projeto_sinalizacoes e aplica os scripts de database/migracoes/ em ordem.

Uso (na raiz do repositório, com o venv ativado e o backend/.env preenchido):

    python backend/db/criar_banco.py

Pode rodar quantas vezes quiser: cada script é aplicado uma única vez
(os já aplicados ficam registrados na tabela schema_versao).
Para mudar o banco no futuro, crie um NOVO arquivo numerado (ex.: 03_nova_coluna.sql);
nunca edite um script que já foi aplicado.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError

import config

PASTA = config.RAIZ / "database" / "migracoes"
NOME_ESPERADO = "projeto_sinalizacoes"


def comandos(sql: str):
    """Divide o script em comandos (separados por ';' no fim da linha)."""
    linhas = [l for l in sql.splitlines() if not l.strip().startswith("--")]
    return [c.strip() for c in "\n".join(linhas).split(";") if c.strip()]


def main():
    url = make_url(config.DB_URL)
    banco = url.database
    if banco != NOME_ESPERADO:
        print(f"ATENÇÃO: o DB_URL aponta para '{banco}', mas os scripts usam '{NOME_ESPERADO}'.")
        print("Ajuste o DB_URL no backend/.env para terminar em /projeto_sinalizacoes.")
        sys.exit(1)

    servidor = create_engine(url._replace(database=None))   # conecta no servidor, sem escolher banco
    with servidor.connect() as c:
        c.exec_driver_sql(f"CREATE DATABASE IF NOT EXISTS `{banco}` "
                          "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        c.exec_driver_sql(f"USE `{banco}`")
        c.exec_driver_sql("CREATE TABLE IF NOT EXISTS schema_versao ("
                          " arquivo VARCHAR(255) PRIMARY KEY,"
                          " aplicado_em DATETIME DEFAULT CURRENT_TIMESTAMP)")
        aplicados = {r[0] for r in c.exec_driver_sql("SELECT arquivo FROM schema_versao")}
        c.commit()

    scripts = sorted(PASTA.glob("*.sql"))
    if not scripts:
        sys.exit(f"Nenhum script encontrado em {PASTA}")
    for arq in scripts:
        if arq.name in aplicados:
            print(f"  já aplicado: {arq.name}")
            continue
        print(f"  aplicando:   {arq.name}")
        conexao = servidor.raw_connection()   # cursor do driver: o SQL vai exatamente como está no arquivo
        try:
            cur = conexao.cursor()
            cur.execute(f"USE `{banco}`")
            for cmd in comandos(arq.read_text(encoding="utf-8")):
                cur.execute(cmd)
            cur.execute("INSERT INTO schema_versao (arquivo) VALUES (%s)", (arq.name,))
            conexao.commit()
        finally:
            conexao.close()
    print("Banco pronto:", banco)


if __name__ == "__main__":
    try:
        main()
    except OperationalError as e:
        sys.exit(f"\nNão foi possível falar com o MySQL: {e.orig}\n"
                 "Confira se o MySQL está ligado e se usuário/senha do DB_URL (backend/.env) estão corretos.\n")
