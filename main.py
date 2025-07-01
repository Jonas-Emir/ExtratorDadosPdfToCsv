import os
import getpass
from pdf_to_csv.extractor import extrair_transacoes
from pdf_to_csv.parser import processar_bloco_transacao
from pdf_to_csv.converter import salvar_csv

ARQUIVO_PDF = r"D:/Projetos/Python/TesteSantander.PDF"
ARQUIVO_SAIDA_CSV = "fatura_processada_final.csv"
ANO_DA_FATURA = "2025"

if __name__ == "__main__":
    if os.path.exists(ARQUIVO_PDF):
        try:
            senha_pdf = getpass.getpass("🔑 Digite a senha do PDF e pressione Enter (deixe em branco se não houver senha): ")
        except Exception:
            senha_pdf = input("⚠️ getpass não suportado. Digite a senha (ficará visível): ")

        transacoes = extrair_transacoes(ARQUIVO_PDF, ANO_DA_FATURA, senha_pdf, processar_bloco_transacao)

        if transacoes:
            qtd_compras, qtd_pagamentos = salvar_csv(transacoes, ARQUIVO_SAIDA_CSV)
            print(f"\n✅ Sucesso! Transações salvas em '{ARQUIVO_SAIDA_CSV}'")
            print(f"📊 {qtd_compras} compras | {qtd_pagamentos} pagamentos/créditos")
        else:
            print("\n⚠️ Nenhuma transação encontrada. Verifique o PDF e a senha.")
    else:
        print(f"❌ Arquivo não encontrado em '{ARQUIVO_PDF}'")