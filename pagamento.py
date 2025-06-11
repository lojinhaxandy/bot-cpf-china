import mercadopago
from config import MERCADO_PAGO_TOKEN

sdk = mercadopago.SDK(MERCADO_PAGO_TOKEN)

def gerar_link_pagamento(valor, user_id, qtd):
    external_reference = f"{user_id}_{qtd}"
    preference_data = {
        "items": [{
            "title": f"Compra de {qtd} CPFs",
            "quantity": 1,
            "currency_id": "BRL",
            "unit_price": float(valor)
        }],
        "external_reference": external_reference,
    }
    preference_response = sdk.preference().create(preference_data)
    preference = preference_response["response"]
    return preference["init_point"], external_reference

def verificar_pagamento(external_reference):
    search_result = sdk.payment().search({"external_reference": external_reference})
    pagamentos = search_result["response"]["results"]
    for pagamento in pagamentos:
        if pagamento["status"] == "approved":
            return True
    return False
