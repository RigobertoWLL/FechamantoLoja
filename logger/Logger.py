"""
Módulo de logging para o sistema de fechamento de lojas.
Configura e disponibiliza funcionalidades de logging padronizadas.
"""

import logging
import os
from typing import Optional


def configurar_logging(
    nivel: str = "ERROR", arquivo_log: Optional[str] = None
) -> logging.Logger:
    """
    Configura o sistema de logging.

    Args:
        nivel (str): Nível de logging (DEBUG, INFO, WARNING, ERROR).
        arquivo_log (Optional[str]): Arquivo para salvar logs. Se None, usa apenas console.

    Returns:
        logging.Logger: Logger configurado.
    """
    logger = logging.getLogger("fechamento_lojas")

    # Remove handlers existentes para evitar duplicação
    if logger.handlers:
        logger.handlers.clear()

    # Configuração do formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Handler para arquivo (se especificado)
    if arquivo_log:
        try:
            # Cria diretório se não existir
            dir_log = os.path.dirname(arquivo_log)
            if dir_log and not os.path.exists(dir_log):
                os.makedirs(dir_log)

            file_handler = logging.FileHandler(arquivo_log, encoding="utf-8")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            # Se falhar ao criar arquivo de log, continua apenas com console
            logger.warning(f"Não foi possível criar arquivo de log {arquivo_log}: {e}")

    # Define o nível
    try:
        logger.setLevel(getattr(logging, nivel.upper()))
    except AttributeError:
        logger.setLevel(logging.INFO)
        logger.warning(f"Nível de log inválido '{nivel}', usando INFO")

    return logger


def obter_logger(nome: Optional[str] = None) -> logging.Logger:
    """
    Obtém um logger já configurado.

    Args:
        nome (Optional[str]): Nome do logger. Se None, usa o logger padrão.

    Returns:
        logging.Logger: Logger configurado.
    """
    if nome:
        return logging.getLogger(f"fechamento_lojas.{nome}")
    return logging.getLogger("fechamento_lojas")


class LoggerMixin:
    """Mixin para classes que precisam de logging."""

    @property
    def logger(self) -> logging.Logger:
        """Propriedade para acessar o logger da classe."""
        nome_classe = self.__class__.__name__
        return obter_logger(nome_classe.lower())


def log_operacao(funcao):
    """
    Decorator para logar início e fim de operações.

    Args:
        funcao: Função a ser decorada.

    Returns:
        Função decorada com logging.
    """

    def wrapper(*args, **kwargs):
        logger = obter_logger("operacoes")
        nome_funcao = funcao.__name__

        logger.info(f"Iniciando operação: {nome_funcao}")

        try:
            resultado = funcao(*args, **kwargs)
            logger.info(f"Operação concluída com sucesso: {nome_funcao}")
            return resultado
        except Exception as e:
            logger.error(f"Erro na operação {nome_funcao}: {e}")
            raise

    return wrapper


def log_erro(
    mensagem: str,
    exception: Optional[Exception] = None,
    logger: Optional[logging.Logger] = None,
):
    """
    Função auxiliar para logar erros de forma padronizada.

    Args:
        mensagem (str): Mensagem de erro.
        exception (Optional[Exception]): Exceção associada ao erro.
        logger (Optional[logging.Logger]): Logger específico a usar.
    """
    if logger is None:
        logger = obter_logger()

    if exception:
        logger.error(f"{mensagem}: {exception}", exc_info=True)
    else:
        logger.error(mensagem)


def log_info(mensagem: str, logger: Optional[logging.Logger] = None):
    """
    Função auxiliar para logar informações de forma padronizada.

    Args:
        mensagem (str): Mensagem informativa.
        logger (Optional[logging.Logger]): Logger específico a usar.
    """
    if logger is None:
        logger = obter_logger()

    logger.info(mensagem)


def log_debug(mensagem: str, logger: Optional[logging.Logger] = None):
    """
    Função auxiliar para logar debug de forma padronizada.

    Args:
        mensagem (str): Mensagem de debug.
        logger (Optional[logging.Logger]): Logger específico a usar.
    """
    if logger is None:
        logger = obter_logger()

    logger.debug(mensagem)


def log_warning(mensagem: str, logger: Optional[logging.Logger] = None):
    """
    Função auxiliar para logar avisos de forma padronizada.

    Args:
        mensagem (str): Mensagem de aviso.
        logger (Optional[logging.Logger]): Logger específico a usar.
    """
    if logger is None:
        logger = obter_logger()

    logger.warning(mensagem)
