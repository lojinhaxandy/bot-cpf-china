import threading

lock = threading.Lock()
estoque_cpfs = []

def pegar_cpfs(qtd):
    with lock:
        return estoque_cpfs[:qtd]

def remover_cpfs(cpfs):
    with lock:
        for cpf in cpfs:
            if cpf in estoque_cpfs:
                estoque_cpfs.remove(cpf)

def contar_estoque():
    with lock:
        return len(estoque_cpfs)

def adicionar_cpfs(novos_cpfs):
    with lock:
        for cpf in novos_cpfs:
            if cpf not in estoque_cpfs:
                estoque_cpfs.append(cpf)
