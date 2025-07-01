import pandas as pd

def salvar_csv(transacoes, caminho_saida):
    df = pd.DataFrame(transacoes)
    df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y')
    df = df.sort_values(by=['Data', 'Descrição']).reset_index(drop=True)
    df['Data'] = df['Data'].dt.strftime('%d/%m/%Y')
    df.to_csv(caminho_saida, index=False, sep=';', decimal=',')

    compras = df[df['Valor'] >= 0]
    pagamentos = df[df['Valor'] < 0]

    return len(compras), len(pagamentos)