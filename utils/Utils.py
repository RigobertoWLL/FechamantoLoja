"""
Módulo de utilitários para o sistema de fechamento de lojas.
CORREÇÃO DEFINITIVA: Inclui função converter_letra_coluna_para_numero melhorada
"""

import re
from datetime import datetime
from typing import Any
from logger.Logger import obter_logger


def validar_numero_loja(numero_loja: Any) -> bool:
    """
    Valida se o número da loja é válido.

    Args:
        numero_loja: Número da loja para validar.

    Returns:
        bool: True se válido, False caso contrário.
    """
    if numero_loja is None:
        return False

    # Converte para string para validação
    numero_str = str(numero_loja).strip()

    # Verifica se não está vazio
    if not numero_str:
        return False

    # Verifica se é um número válido (pode conter letras e números)
    # Suporta formatos como: 123, I05, T09, ABC123, etc.
    return bool(re.match(r"^[A-Za-z0-9]+$", numero_str))


def validar_codigo_alfanumerico(codigo: Any) -> bool:
    """
    Validação específica para códigos alfanuméricos de lojas.
    Suporta formatos como I05, T09, I01, etc.

    Args:
        codigo: Código da loja para validar.

    Returns:
        bool: True se é um código alfanumérico válido, False caso contrário.
    """
    if codigo is None:
        return False

    codigo_str = str(codigo).strip().upper()

    if not codigo_str:
        return False

    # Padrão para códigos alfanuméricos: 1-3 letras seguidas de 1-4 números
    # Exemplos: I05, T09, I01, AB123, XYZ9999
    patron_alfanumerico = r"^[A-Z]{1,3}[0-9]{1,4}$"

    return bool(re.match(patron_alfanumerico, codigo_str))


def normalizar_codigo_alfanumerico(codigo: Any) -> str:
    """
    Normaliza códigos alfanuméricos para formato padrão.
    Converte para maiúsculo e adiciona padding de zeros quando necessário.

    Args:
        codigo: Código a ser normalizado.

    Returns:
        str: Código normalizado (ex: "i5" -> "I05", "t9" -> "T09").
    """
    if codigo is None:
        return ""

    try:
        codigo_str = str(codigo).strip().upper()

        if not codigo_str:
            return ""

        # Separa letras e números
        match = re.match(r"^([A-Z]+)([0-9]+)$", codigo_str)

        if match:
            letras, numeros = match.groups()

            # Para códigos com 1 letra, adiciona padding de zeros até 2 dígitos
            if len(letras) == 1 and len(numeros) <= 2:
                numeros_padded = numeros.zfill(2)
                resultado = f"{letras}{numeros_padded}"

                logger = obter_logger("utils")
                logger.debug(
                    f"Código alfanumérico normalizado: '{codigo}' -> '{resultado}'"
                )

                return resultado
            else:
                # Para outros casos, mantém como está
                return codigo_str

        # Se não corresponde ao padrão alfanumérico, retorna formatado normalmente
        return formatar_numero_loja(codigo_str)

    except Exception as e:
        logger = obter_logger("utils")
        logger.warning(f"Erro ao normalizar código alfanumérico '{codigo}': {e}")
        return formatar_numero_loja(codigo) if codigo else ""


def obter_data_atual() -> str:
    """
    Obtém a data atual no formato brasileiro.

    Returns:
        str: Data atual no formato DD/MM/AAAA.
    """
    return datetime.now().strftime("%d/%m/%Y")


def obter_data_hora_atual() -> str:
    """
    Obtém a data e hora atual no formato brasileiro.

    Returns:
        str: Data e hora atual no formato DD/MM/AAAA HH:MM:SS.
    """
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")


def formatar_numero_loja(numero_loja: Any) -> str:
    """
    Formata o número da loja para padronização.

    Args:
        numero_loja: Número da loja para formatar.

    Returns:
        str: Número da loja formatado.
    """
    if numero_loja is None:
        return ""

    # Converte para string e remove espaços
    numero_str = str(numero_loja).strip()

    # Remove caracteres especiais, mantendo apenas letras e números
    numero_limpo = re.sub(r"[^A-Za-z0-9]", "", numero_str)

    return numero_limpo.upper()


def validar_nome_loja(nome_loja: Any) -> bool:
    """
    Valida se o nome da loja é válido.

    Args:
        nome_loja: Nome da loja para validar.

    Returns:
        bool: True se válido, False caso contrário.
    """
    if nome_loja is None:
        return False

    nome_str = str(nome_loja).strip()
    return len(nome_str) > 0


def converter_numero_coluna_para_letra(numero: int) -> str:
    """
    Converte número da coluna para letra (1=A, 2=B, etc.).

    Args:
        numero (int): Número da coluna.

    Returns:
        str: Letra correspondente à coluna.
    """
    if numero <= 0:
        raise ValueError("Número da coluna deve ser maior que zero")

    resultado = ""
    while numero > 0:
        numero -= 1
        resultado = chr(numero % 26 + ord("A")) + resultado
        numero //= 26
    return resultado


def converter_letra_coluna_para_numero(letra: str) -> int:
    """
    CORREÇÃO CRÍTICA: Converte letra da coluna para número (A=1, B=2, etc.).
    Esta função é essencial para resolver o erro do gspread.

    Args:
        letra (str): Letra da coluna.

    Returns:
        int: Número correspondente à coluna.
    """
    if not letra or not isinstance(letra, str):
        raise ValueError("Letra da coluna deve ser uma string válida")

    try:
        # Limpa e normaliza a entrada
        letra_limpa = str(letra).strip().upper()

        if not letra_limpa:
            raise ValueError("Letra da coluna não pode estar vazia")

        numero = 0
        for char in letra_limpa:
            if not char.isalpha():
                raise ValueError(f"Caractere inválido na letra da coluna: {char}")
            numero = numero * 26 + (ord(char) - ord("A") + 1)

        # Log para debug
        logger = obter_logger("utils")
        logger.debug(f"Conversão coluna: '{letra}' -> {numero}")

        return numero

    except Exception as e:
        logger = obter_logger("utils")
        logger.error(f"Erro ao converter letra da coluna '{letra}': {e}")
        # Em caso de erro, retorna valor padrão baseado na primeira letra
        if letra and len(letra) > 0:
            return ord(letra[0].upper()) - ord("A") + 1
        return 1  # Retorna 1 (coluna A) como fallback


def limpar_texto(texto: Any) -> str:
    """
    Limpa e formata texto removendo espaços extras e normalizando.

    Args:
        texto: Texto para limpar.

    Returns:
        str: Texto limpo.
    """
    if texto is None:
        return ""

    # Converte para string e remove espaços em excesso
    texto_str = str(texto).strip()

    # Remove múltiplos espaços internos
    texto_limpo = re.sub(r"\s+", " ", texto_str)

    return texto_limpo


def criar_observacao_padrao(numero_loja: str) -> str:
    """
    Cria uma observação padrão para o fechamento da loja.

    Args:
        numero_loja (str): Número da loja.

    Returns:
        str: Observação padrão.
    """
    data_atual = obter_data_hora_atual()
    return f"Loja {numero_loja} fechada automaticamente via sistema em {data_atual}"


def safe_int(valor: Any, padrao: int = 0) -> int:
    """
    CORREÇÃO CRÍTICA: Converte um valor para inteiro de forma ultra-segura.

    Args:
        valor: Valor a ser convertido.
        padrao (int): Valor padrão caso a conversão falhe.

    Returns:
        int: Valor convertido ou padrão.
    """
    if valor is None:
        return padrao

    try:
        # Se já é int, retorna diretamente
        if isinstance(valor, int):
            return valor

        # Se é float, converte para int
        elif isinstance(valor, float):
            if valor != valor:  # Checa se é NaN
                return padrao
            if valor == float("inf") or valor == float("-inf"):
                return padrao
            return int(valor)

        # Se é string, tenta converter
        elif isinstance(valor, str):
            valor_limpo = valor.strip()
            if not valor_limpo:
                return padrao

            # Tenta conversão direta primeiro
            try:
                return int(valor_limpo)
            except ValueError:
                # Se falhar, tenta como float primeiro
                try:
                    float_val = float(valor_limpo)
                    if float_val != float_val:  # Checa se é NaN
                        return padrao
                    if float_val == float("inf") or float_val == float("-inf"):
                        return padrao
                    return int(float_val)
                except ValueError:
                    # Se ainda falhar, extrai apenas números da string
                    numeros_na_string = re.findall(r"-?\d+", valor_limpo)
                    if numeros_na_string:
                        return int(numeros_na_string[0])
                    return padrao

        # Para outros tipos, tenta conversão direta
        else:
            return int(valor)

    except (ValueError, TypeError, OverflowError) as e:
        logger = obter_logger("utils")
        logger.debug(
            f"safe_int: Erro ao converter '{valor}' (tipo: {type(valor)}) para int: {e}. Usando padrão: {padrao}"
        )
        return padrao


def normalizar_tipo_numero_loja(valor: Any) -> str:
    """
    CORREÇÃO CRÍTICA: Normaliza qualquer tipo de entrada para string.

    Args:
        valor: Valor a ser normalizado (pode ser int, str, float, etc.)

    Returns:
        str: Valor normalizado como string padronizada.
    """
    if valor is None:
        return ""

    try:
        # Se for um número (int ou float), converte para string
        if isinstance(valor, (int, float)):
            # Tratamento especial para floats
            if isinstance(valor, float):
                if valor != valor:  # Checa se é NaN
                    return ""
                if valor == float("inf") or valor == float("-inf"):
                    return ""
                # Remove decimais desnecessários para floats
                if valor.is_integer():
                    valor = int(valor)
            valor_str = str(valor)
        else:
            # Se for string ou outro tipo, converte para string
            valor_str = str(valor)

        # Primeiro tenta normalização de código alfanumérico
        if validar_codigo_alfanumerico(valor_str):
            return normalizar_codigo_alfanumerico(valor_str)

        # Senão, aplica formatação padrão
        return formatar_numero_loja(valor_str)

    except Exception as e:
        logger = obter_logger("utils")
        logger.warning(
            f"normalizar_tipo_numero_loja: Erro ao normalizar '{valor}': {e}"
        )
        return ""


def comparar_numeros_loja(numero1: Any, numero2: Any) -> bool:
    """
    CORREÇÃO CRÍTICA: Compara dois números de loja de forma ultra-segura.

    Args:
        numero1: Primeiro número de loja.
        numero2: Segundo número de loja.

    Returns:
        bool: True se são iguais, False caso contrário.
    """
    try:
        # Normaliza ambos os valores para string
        num1_normalizado = normalizar_tipo_numero_loja(numero1)
        num2_normalizado = normalizar_tipo_numero_loja(numero2)

        # Compara os valores normalizados (sempre strings agora)
        resultado = num1_normalizado == num2_normalizado

        # Se não são iguais mas são códigos alfanuméricos, tenta comparação flexível
        if (
            not resultado
            and validar_codigo_alfanumerico(num1_normalizado)
            and validar_codigo_alfanumerico(num2_normalizado)
        ):
            # Compara sem padding de zeros (I5 == I05)
            resultado = comparar_codigos_flexivel(num1_normalizado, num2_normalizado)

        # Log para debug
        logger = obter_logger("utils")
        logger.debug(
            f"comparar_numeros_loja: '{numero1}' ({type(numero1)}) com '{numero2}' ({type(numero2)}) -> '{num1_normalizado}' == '{num2_normalizado}' = {resultado}"
        )

        return resultado

    except Exception as e:
        logger = obter_logger("utils")
        logger.error(
            f"comparar_numeros_loja: Erro ao comparar '{numero1}' e '{numero2}': {e}"
        )
        return False


def comparar_codigos_flexivel(codigo1: str, codigo2: str) -> bool:
    """
    Compara códigos alfanuméricos de forma flexível.
    Considera I5 == I05, T9 == T09, etc.

    Args:
        codigo1 (str): Primeiro código.
        codigo2 (str): Segundo código.

    Returns:
        bool: True se são equivalentes, False caso contrário.
    """
    try:
        # Extrai letras e números de cada código
        match1 = re.match(r"^([A-Z]+)([0-9]+)$", codigo1.upper())
        match2 = re.match(r"^([A-Z]+)([0-9]+)$", codigo2.upper())

        if match1 and match2:
            letras1, numeros1 = match1.groups()
            letras2, numeros2 = match2.groups()

            # Compara letras e números como inteiros (remove zeros à esquerda)
            return letras1 == letras2 and int(numeros1) == int(numeros2)

        return False

    except Exception as e:
        logger = obter_logger("utils")
        logger.debug(
            f"comparar_codigos_flexivel: Erro na comparação de '{codigo1}' e '{codigo2}': {e}"
        )
        return False


def formatar_lista_lojas(lista_str: str) -> list:
    """
    Formata uma string com lista de lojas separadas por vírgula.

    Args:
        lista_str (str): String com números separados por vírgula.

    Returns:
        list: Lista de números de loja formatados.
    """
    if not lista_str or not isinstance(lista_str, str):
        return []

    try:
        # Separa por vírgula e formata cada item
        numeros = []
        for item in lista_str.split(","):
            numero_formatado = normalizar_tipo_numero_loja(item.strip())
            if numero_formatado and validar_numero_loja(numero_formatado):
                numeros.append(numero_formatado)

        return numeros

    except Exception as e:
        logger = obter_logger("utils")
        logger.error(f"formatar_lista_lojas: Erro ao formatar lista '{lista_str}': {e}")
        return []


def validar_configuracao_coluna(coluna: str) -> bool:
    """
    Valida se uma configuração de coluna está no formato correto.

    Args:
        coluna (str): Letra da coluna (ex: 'A', 'B', 'C', etc.).

    Returns:
        bool: True se válida, False caso contrário.
    """
    if not coluna or not isinstance(coluna, str):
        return False

    # Verifica se é uma letra válida de coluna
    return bool(re.match(r"^[A-Z]+$", coluna.upper()))


def truncar_texto(texto: str, max_length: int = 100) -> str:
    """
    Trunca um texto se ele for muito longo.

    Args:
        texto (str): Texto a ser truncado.
        max_length (int): Tamanho máximo permitido.

    Returns:
        str: Texto truncado se necessário.
    """
    if not texto or not isinstance(texto, str):
        return ""

    if len(texto) <= max_length:
        return texto

    return texto[: max_length - 3] + "..."


def debug_tipo_valor(valor: Any, nome_variavel: str = "valor") -> None:
    """
    Função auxiliar para debug de tipos de valores.

    Args:
        valor: Valor para análise.
        nome_variavel (str): Nome da variável para log.
    """
    logger = obter_logger("utils")
    logger.debug(
        f"DEBUG {nome_variavel}: valor='{valor}', tipo={type(valor)}, repr={repr(valor)}"
    )


def listar_formatos_suportados() -> dict:
    """
    Retorna uma lista dos formatos de código de loja suportados.

    Returns:
        dict: Dicionário com exemplos de formatos suportados.
    """
    return {
        "numericos": ["123", "456", "789", "1000"],
        "alfanumericos_padrao": ["I05", "T09", "I01", "A99"],
        "alfanumericos_multiplas_letras": ["AB12", "XYZ999"],
        "variacao_aceita": {"I5": "I05", "T9": "T09", "i01": "I01", "t09": "T09"},
    }
