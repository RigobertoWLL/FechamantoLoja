import re
from datetime import datetime
from typing import Optional, Any, Union
from .logger import obter_logger


def validar_numero_loja(numero_loja: Any) -> bool:
    if numero_loja is None:
        return False

    numero_str = str(numero_loja).strip()

    if not numero_str:
        return False

    return bool(re.match(r"^[A-Za-z0-9]+$", numero_str))


def validar_codigo_alfanumerico(codigo: Any) -> bool:
    if codigo is None:
        return False

    codigo_str = str(codigo).strip().upper()

    if not codigo_str:
        return False

    patron_alfanumerico = r"^[A-Z]{1,3}[0-9]{1,4}$"

    return bool(re.match(patron_alfanumerico, codigo_str))


def normalizar_codigo_alfanumerico(codigo: Any) -> str:
    if codigo is None:
        return ""

    try:
        codigo_str = str(codigo).strip().upper()

        if not codigo_str:
            return ""

        match = re.match(r"^([A-Z]+)([0-9]+)$", codigo_str)

        if match:
            letras, numeros = match.groups()

            if len(letras) == 1 and len(numeros) <= 2:
                numeros_padded = numeros.zfill(2)
                resultado = f"{letras}{numeros_padded}"

                logger = obter_logger("utils")
                logger.debug(
                    f"Código alfanumérico normalizado: '{codigo}' -> '{resultado}'"
                )

                return resultado
            else:
                return codigo_str

        return formatar_numero_loja(codigo_str)

    except Exception as e:
        logger = obter_logger("utils")
        logger.warning(f"Erro ao normalizar código alfanumérico '{codigo}': {e}")
        return formatar_numero_loja(codigo) if codigo else ""


def obter_data_atual() -> str:
    return datetime.now().strftime("%d/%m/%Y")


def obter_data_hora_atual() -> str:
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")


def formatar_numero_loja(numero_loja: Any) -> str:
    if numero_loja is None:
        return ""

    numero_str = str(numero_loja).strip()

    numero_limpo = re.sub(r"[^A-Za-z0-9]", "", numero_str)

    return numero_limpo.upper()


def validar_nome_loja(nome_loja: Any) -> bool:
    if nome_loja is None:
        return False

    nome_str = str(nome_loja).strip()
    return len(nome_str) > 0


def converter_numero_coluna_para_letra(numero: int) -> str:
    if numero < 1:
        return ""

    resultado = ""
    while numero > 0:
        numero -= 1
        resultado = chr(ord("A") + (numero % 26)) + resultado
        numero //= 26

    return resultado


def converter_letra_coluna_para_numero(letra: str) -> int:
    if not letra or not letra.strip():
        return 0

    letra = letra.strip().upper()
    
    if not re.match(r"^[A-Z]+$", letra):
        return 0

    numero = 0
    for char in letra:
        if "A" <= char <= "Z":
            numero = numero * 26 + (ord(char) - ord("A") + 1)
        else:
            return 0

    return numero


def limpar_texto(texto: Any) -> str:
    if texto is None:
        return ""

    texto_str = str(texto).strip()

    texto_limpo = re.sub(r"\s+", " ", texto_str)

    return texto_limpo


def criar_observacao_padrao(numero_loja: str) -> str:
    data_atual = obter_data_hora_atual()
    return f"Loja {numero_loja} fechada automaticamente via sistema em {data_atual}"


def safe_int(valor: Any, padrao: int = 0) -> int:
    try:
        if valor is None:
            return padrao

        if isinstance(valor, int):
            return valor

        if isinstance(valor, str):
            valor_limpo = valor.strip()
            if not valor_limpo:
                return padrao

            valor_numerico = ""
            for char in valor_limpo:
                if char.isdigit():
                    valor_numerico += char
                elif char in ".,":
                    break
                else:
                    if not valor_numerico:
                        continue
                    break

            if valor_numerico:
                return int(valor_numerico)
            else:
                return padrao

        if hasattr(valor, "__int__"):
            return int(valor)

        valor_str = str(valor)
        valor_numerico = ""
        for char in valor_str:
            if char.isdigit():
                valor_numerico += char
            else:
                break

        return int(valor_numerico) if valor_numerico else padrao

    except (ValueError, TypeError, OverflowError):
        return padrao
    except Exception as e:
        logger = obter_logger("utils")
        logger.warning(f"Erro inesperado em safe_int para '{valor}': {e}")
        return padrao


def normalizar_tipo_numero_loja(valor: Any) -> str:
    if valor is None:
        return ""

    try:
        if isinstance(valor, (int, float)):
            if isinstance(valor, float) and valor.is_integer():
                valor = int(valor)
            valor_str = str(valor)
        else:
            valor_str = str(valor).strip()

        if not valor_str:
            return ""

        if validar_codigo_alfanumerico(valor_str):
            return normalizar_codigo_alfanumerico(valor_str)
        else:
            return formatar_numero_loja(valor_str)

    except Exception as e:
        logger = obter_logger("utils")
        logger.warning(f"Erro ao normalizar tipo número loja '{valor}': {e}")
        return formatar_numero_loja(valor) if valor else ""


def comparar_numeros_loja(numero1: Any, numero2: Any) -> bool:
    try:
        if numero1 is None or numero2 is None:
            return False

        num1_normalizado = normalizar_tipo_numero_loja(numero1)
        num2_normalizado = normalizar_tipo_numero_loja(numero2)

        if not num1_normalizado or not num2_normalizado:
            return False

        return num1_normalizado.upper() == num2_normalizado.upper()

    except Exception as e:
        logger = obter_logger("utils")
        logger.warning(f"Erro ao comparar números de loja '{numero1}' e '{numero2}': {e}")
        return False


def comparar_codigos_flexivel(codigo1: str, codigo2: str) -> bool:
    try:
        if not codigo1 or not codigo2:
            return False

        c1 = str(codigo1).strip().upper()
        c2 = str(codigo2).strip().upper()

        if c1 == c2:
            return True

        c1_normalizado = normalizar_tipo_numero_loja(c1)
        c2_normalizado = normalizar_tipo_numero_loja(c2)

        return c1_normalizado == c2_normalizado

    except Exception as e:
        logger = obter_logger("utils")
        logger.debug(f"Erro na comparação flexível '{codigo1}' vs '{codigo2}': {e}")
        return False


def formatar_lista_lojas(lista_str: str) -> list:
    if not lista_str:
        return []

    try:
        lista_limpa = lista_str.replace(" ", "").replace("\n", "").replace("\t", "")
        numeros = [num.strip() for num in lista_limpa.split(",") if num.strip()]
        return numeros
    except Exception as e:
        logger = obter_logger("utils")
        logger.warning(f"Erro ao formatar lista de lojas '{lista_str}': {e}")
        return []


def validar_configuracao_coluna(coluna: str) -> bool:
    if not coluna or not isinstance(coluna, str):
        return False

    coluna = coluna.strip().upper()
    return bool(re.match(r"^[A-Z]+$", coluna)) and len(coluna) <= 3


def truncar_texto(texto: str, max_length: int = 100) -> str:
    if not texto:
        return ""
    
    if len(texto) <= max_length:
        return texto
    
    return texto[:max_length-3] + "..."


def debug_tipo_valor(valor: Any, nome_variavel: str = "valor") -> None:
    logger = obter_logger("debug")
    tipo = type(valor).__name__
    representacao = repr(valor)[:100]
    logger.debug(f"{nome_variavel}: tipo={tipo}, valor={representacao}")


def listar_formatos_suportados() -> dict:
    return {
        "numericos": ["123", "456", "789", "1000"],
        "alfanumericos_padrao": ["I05", "T09", "I01", "A99"],
        "alfanumericos_multiplas_letras": ["AB12", "XYZ999"],
        "variacao_aceita": {"I5": "I05", "T9": "T09", "i01": "I01", "t09": "T09"},
    }