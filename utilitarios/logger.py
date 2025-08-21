import logging
import os
from typing import Optional


def configurar_logging(nivel: str = 'INFO', arquivo_log: Optional[str] = None) -> logging.Logger:
    logger = logging.getLogger('fechamento_lojas')
    
    if logger.handlers:
        logger.handlers.clear()
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    if arquivo_log:
        try:
            dir_log = os.path.dirname(arquivo_log)
            if dir_log and not os.path.exists(dir_log):
                os.makedirs(dir_log)
            
            file_handler = logging.FileHandler(arquivo_log, encoding='utf-8')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Não foi possível criar arquivo de log {arquivo_log}: {e}")
    
    try:
        logger.setLevel(getattr(logging, nivel.upper()))
    except AttributeError:
        logger.setLevel(logging.INFO)
        logger.warning(f"Nível de log inválido '{nivel}', usando INFO")
    
    return logger


def obter_logger(nome: Optional[str] = None) -> logging.Logger:
    if nome:
        return logging.getLogger(f'fechamento_lojas.{nome}')
    return logging.getLogger('fechamento_lojas')


class MixinLogger:
    
    @property
    def logger(self) -> logging.Logger:
        nome_classe = self.__class__.__name__
        return obter_logger(nome_classe.lower())


def log_operacao(funcao):
    def wrapper(*args, **kwargs):
        logger = obter_logger('operacoes')
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


def log_erro(mensagem: str, exception: Optional[Exception] = None, logger: Optional[logging.Logger] = None):
    if logger is None:
        logger = obter_logger()
    
    if exception:
        logger.error(f"{mensagem}: {exception}", exc_info=True)
    else:
        logger.error(mensagem)


def log_info(mensagem: str, logger: Optional[logging.Logger] = None):
    if logger is None:
        logger = obter_logger()
    
    logger.info(mensagem)


def log_debug(mensagem: str, logger: Optional[logging.Logger] = None):
    if logger is None:
        logger = obter_logger()
    
    logger.debug(mensagem)


def log_warning(mensagem: str, logger: Optional[logging.Logger] = None):
    if logger is None:
        logger = obter_logger()
    
    logger.warning(mensagem)