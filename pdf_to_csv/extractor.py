import pdfplumber
import re

def extrair_transacoes(caminho_pdf, ano, senha, processar_bloco_transacao):
    print("📄 Iniciando leitura do arquivo PDF...")
    transacoes = []
    portador_atual = "Não Identificado"

    try:
        with pdfplumber.open(caminho_pdf, password=senha) as pdf:
            for pagina in pdf.pages:
                if pagina.page_number == 1:
                    print(f"-> Ignorando página 1 (resumo da fatura).")
                    continue

                print(f"-> Processando página {pagina.page_number} de {len(pdf.pages)}...")
                metade_da_pagina = pagina.width / 2
                colunas = [
                    (0, 0, metade_da_pagina, pagina.height),
                    (metade_da_pagina, 0, pagina.width, pagina.height)
                ]

                for i, bbox_coluna in enumerate(colunas):
                    print(f"   -> Lendo coluna {i + 1}...")
                    pagina_cortada = pagina.crop(bbox=bbox_coluna)
                    texto_coluna = pagina_cortada.extract_text(layout=True, x_tolerance=2, y_tolerance=3)

                    if not texto_coluna:
                        continue

                    linhas = texto_coluna.split('\n')
                    linha_pendente = ""

                    for linha_atual in linhas:
                        linha_limpa = linha_atual.strip()
                        
                        if not linha_limpa:
                            continue

                        match_portador = re.search(r'^([A-Z\s@.*]+?)\s+-\s+\d{4}', linha_limpa)
                        if match_portador:
                            nome_completo = match_portador.group(1).replace('@', '').strip()
                            portador_atual = nome_completo.split()[0].capitalize()
                            print(f"       👤 Portador na coluna {i + 1}: {portador_atual}")
                            linha_pendente = ""
                            continue

                        resultado = processar_bloco_transacao(linha_limpa, portador_atual, ano)
                        if resultado:
                            transacoes.append(resultado)
                            linha_pendente = ""
                            continue

                        if linha_pendente:
                            bloco_combinado = linha_pendente + " " + linha_limpa
                            resultado_combinado = processar_bloco_transacao(bloco_combinado, portador_atual, ano)
                            if resultado_combinado:
                                transacoes.append(resultado_combinado)
                                linha_pendente = ""
                                continue

                        if re.match(r'^\d{2}/\d{2}', linha_limpa):
                            linha_pendente = linha_limpa

    except pdfplumber.exceptions.PDFPasswordIncorrect:
        print("\n❌ ERRO: Senha do PDF incorreta.")
        return None
    except Exception as e:
        print(f"\n❌ Ocorreu um erro inesperado: {e}")
        return None

    return transacoes