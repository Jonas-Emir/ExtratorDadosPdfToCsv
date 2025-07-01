import re

def processar_bloco_transacao(bloco_texto, portador, ano):
    bloco_texto_removido = re.sub(r'^\d+\s+', '', bloco_texto)
    match_transacao = re.search(r'(\d{2}/\d{2})\s+(.+?)\s+(-?[\d.,]+)(?:\s+[A-Z])?$', bloco_texto_removido)

    if match_transacao:
        descricao = match_transacao.group(2).strip()

        if any(keyword in descricao.upper() for keyword in ["TOTAL", "SALDO ANTERIOR", "CRÉDITO", "JUROS", "MULTA"]):
            if "PAGAMENTO" not in bloco_texto.upper():
                return None

        data_pdf = match_transacao.group(1)
        valor_str = match_transacao.group(3)
        data_formatada = f"{data_pdf}/{ano}"
        descricao_limpa = re.sub(r'\s+\d{2}/\d{2}$', '', descricao).strip()
        descricao_final = f"({portador}) - {descricao_limpa}"
        try:
            valor_float = float(valor_str.replace('.', '').replace(',', '.'))
        except ValueError:
            return None
        return {"Data": data_formatada, "Descrição": descricao_final, "Valor": valor_float}
    return None
