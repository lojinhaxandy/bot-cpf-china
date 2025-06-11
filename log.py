import os

LOG_FILE = "vendas.log"

def log_venda(user_id, qtd, preco, status):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{user_id};{qtd};{preco:.2f};{status}\n")

def total_vendido():
    if not os.path.exists(LOG_FILE):
        return 0
    total = 0
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for linha in f:
            try:
                partes = linha.strip().split(";")
                qtd = int(partes[1])
                status = partes[3]
                if status == "aprovado":
                    total += qtd
            except:
                continue
    return total
