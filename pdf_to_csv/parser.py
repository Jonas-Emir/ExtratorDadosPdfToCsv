import re

def processar_bloco_transacao(bloco_texto, portador, ano):
    bloco_texto_removido = re.sub(r'^\d+\s+', '', bloco_texto)

    match = re.search(
        r'(\d{2}/\d{2})\s+(.+?)\s+(\d{2}/\d{2})\s+(-?[\d.,]+)(?:\s+[A-Z])?$',
        bloco_texto_removido
    )

    parcela = None

    if not match:
        match = re.search(
            r'(\d{2}/\d{2})\s+(.+?)\s+(-?[\d.,]+)(?:\s+[A-Z])?$',
            bloco_texto_removido
        )
    else:
        parcela = match.group(3)

    if match:
        data_pdf = match.group(1)
        descricao = match.group(2).strip()
        valor_str = match.group(4) if parcela else match.group(3)

        if any(k in descricao.upper() for k in ["TOTAL", "SALDO ANTERIOR", "CRÉDITO", "JUROS", "MULTA"]):
            if "PAGAMENTO" not in bloco_texto.upper():
                print("⏩ Ignorado: linha de resumo.")
                return None

        data_formatada = f"{data_pdf}/{ano}"
        descricao_limpa = re.sub(r'\s+\d{2}/\d{2}$', '', descricao).strip()
        descricao_final = f"({portador}) - {descricao_limpa}"

        try:
            valor_float = float(valor_str.replace('.', '').replace(',', '.'))
        except ValueError:
            print(f"⚠️ Valor inválido: {valor_str}")
            return None

        return {
            "Data": data_formatada,
            "Descrição": descricao_final,
            "Parcela": parcela,
            "Valor": valor_float
        }

    return None
