"""
Módulo para integração com banco de dados Firebird 5.0.
CORRIGIDO: Problema com cursor.rowcount no Firebird
"""

import fdb
from typing import Optional, List, Any, Dict
import time
from contextlib import contextmanager

from manager.ConfigManager import ConfigManager
from logger.Logger import LoggerMixin, log_operacao
from utils.Utils import (
    validar_numero_loja,
    normalizar_tipo_numero_loja,
    validar_codigo_alfanumerico,
    comparar_numeros_loja,
)


class FirebirdManager(LoggerMixin):
    """Classe para gerenciar operações com banco Firebird."""

    def __init__(self):
        """Inicializa o gerenciador do Firebird."""
        self.config = ConfigManager()
        self.conexao = None
        self.conectado = False

        # Configurações do banco usando ConfigManager
        self.host = self.config.firebird_host
        self.database = self.config.firebird_database
        self.user = self.config.firebird_user
        self.password = self.config.firebird_password
        self.charset = self.config.firebird_charset
        self.port = self.config.firebird_port

    @log_operacao
    def conectar(self) -> bool:
        """
        Estabelece conexão com o banco Firebird.

        Returns:
            bool: True se conectado com sucesso, False caso contrário.
        """
        try:
            self.logger.info("Iniciando conexão com Firebird...")

            # String de conexão para Firebird
            dsn = f"{self.host}/{self.port}:{self.database}"

            self.logger.debug(f"Conectando ao DSN: {dsn}")

            # Estabelece conexão
            self.conexao = fdb.connect(
                dsn=dsn, user=self.user, password=self.password, charset=self.charset
            )

            # Testa a conexão
            if self.conexao:
                cursor = self.conexao.cursor()
                cursor.execute("SELECT 1 FROM RDB$DATABASE")
                cursor.fetchone()
                cursor.close()

                self.conectado = True
                self.logger.info("Conexão com Firebird estabelecida com sucesso!")
                return True
            else:
                self.logger.error("Falha ao estabelecer conexão com Firebird")
                return False

        except fdb.DatabaseError as e:
            self.logger.error(f"Erro de banco de dados ao conectar: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Erro inesperado ao conectar no Firebird: {e}")
            return False

    @contextmanager
    def obter_cursor(self):
        """
        Context manager para obter cursor do banco de forma segura.

        Yields:
            fdb.Cursor: Cursor do banco de dados.
        """
        if not self.conectado or not self.conexao:
            raise Exception("Não conectado ao banco Firebird")

        cursor = None
        try:
            cursor = self.conexao.cursor()
            yield cursor
        finally:
            if cursor:
                cursor.close()

    @log_operacao
    def verificar_estrutura_tabela(self) -> bool:
        """
        Verifica se a tabela TB_LOJA existe e tem as colunas necessárias.

        Returns:
            bool: True se estrutura está correta, False caso contrário.
        """
        try:
            with self.obter_cursor() as cursor:
                # Verifica se a tabela existe
                sql_tabela = """
                    SELECT COUNT(*) 
                    FROM RDB$RELATIONS 
                    WHERE RDB$RELATION_NAME = 'TB_LOJA'
                """
                cursor.execute(sql_tabela)
                resultado = cursor.fetchone()

                if not resultado or resultado[0] == 0:
                    self.logger.error("Tabela TB_LOJA não encontrada")
                    return False

                # Verifica se as colunas existem
                sql_colunas = """
                    SELECT RDB$FIELD_NAME 
                    FROM RDB$RELATION_FIELDS 
                    WHERE RDB$RELATION_NAME = 'TB_LOJA' 
                    AND RDB$FIELD_NAME IN ('CODLOJA', 'ID_STATUS')
                """
                cursor.execute(sql_colunas)
                colunas = [row[0].strip() for row in cursor.fetchall()]

                if "CODLOJA" not in colunas:
                    self.logger.error("Coluna CODLOJA não encontrada na tabela TB_LOJA")
                    return False

                if "ID_STATUS" not in colunas:
                    self.logger.error(
                        "Coluna ID_STATUS não encontrada na tabela TB_LOJA"
                    )
                    return False

                self.logger.info("Estrutura da tabela TB_LOJA verificada com sucesso")
                return True

        except Exception as e:
            self.logger.error(f"Erro ao verificar estrutura da tabela: {e}")
            return False

    @log_operacao
    def buscar_loja_por_codigo(self, codigo_loja: str) -> Optional[Dict[str, Any]]:
        """
        Busca uma loja pelo código na tabela TB_LOJA.

        Args:
            codigo_loja (str): Código da loja para buscar.

        Returns:
            Optional[Dict]: Informações da loja ou None se não encontrada.
        """
        try:
            if not validar_numero_loja(codigo_loja):
                self.logger.warning(f"Código de loja inválido: {codigo_loja}")
                return None

            # Normaliza o código da loja
            codigo_normalizado = normalizar_tipo_numero_loja(codigo_loja)

            self.logger.info(f"Buscando loja {codigo_loja} na tabela TB_LOJA...")

            with self.obter_cursor() as cursor:
                # Query para buscar a loja
                sql = """
                    SELECT CODLOJA, ID_STATUS
                    FROM TB_LOJA 
                    WHERE CODLOJA = ?
                """

                self.logger.debug(
                    f"Executando SQL: {sql} com parâmetro: {codigo_normalizado}"
                )

                cursor.execute(sql, (codigo_normalizado,))
                resultado = cursor.fetchone()

                if resultado and len(resultado) >= 2:
                    loja_info = {
                        "codigo_loja": (
                            str(resultado[0]).strip()
                            if resultado[0]
                            else codigo_normalizado
                        ),
                        "id_status": (
                            int(resultado[1]) if resultado[1] is not None else 0
                        ),
                    }

                    # Tenta obter nome se existe coluna NOME
                    try:
                        sql_nome = """
                            SELECT APELIDO
                            FROM TB_LOJA 
                            WHERE CODLOJA = ?
                        """
                        cursor.execute(sql_nome, (codigo_normalizado,))
                        resultado_nome = cursor.fetchone()
                        loja_info["nome"] = (
                            str(resultado_nome[0]).strip()
                            if resultado_nome and resultado_nome[0]
                            else "Nome não informado"
                        )
                    except:
                        loja_info["nome"] = "Nome não disponível"

                    self.logger.info(f"Loja {codigo_loja} encontrada: {loja_info}")
                    return loja_info
                else:
                    # Tenta busca com comparação flexível para códigos alfanuméricos
                    if validar_codigo_alfanumerico(codigo_normalizado):
                        return self._buscar_loja_alfanumerica_flexivel(
                            codigo_normalizado
                        )

                    self.logger.warning(
                        f"Loja {codigo_loja} não encontrada na tabela TB_LOJA"
                    )
                    return None

        except fdb.DatabaseError as e:
            self.logger.error(f"Erro de banco ao buscar loja {codigo_loja}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Erro inesperado ao buscar loja {codigo_loja}: {e}")
            import traceback

            self.logger.debug(f"Traceback: {traceback.format_exc()}")
            return None

    def _buscar_loja_alfanumerica_flexivel(
        self, codigo_normalizado: str
    ) -> Optional[Dict[str, Any]]:
        """
        Busca flexível para códigos alfanuméricos (I5 = I05, etc.).

        Args:
            codigo_normalizado (str): Código normalizado para buscar.

        Returns:
            Optional[Dict]: Informações da loja ou None se não encontrada.
        """
        try:
            with self.obter_cursor() as cursor:
                # Busca todos os códigos que começam com as mesmas letras
                import re

                match = re.match(r"^([A-Z]+)([0-9]+)$", codigo_normalizado.upper())

                if match:
                    letras, numeros = match.groups()

                    # Busca códigos que começam com as mesmas letras
                    sql = """
                        SELECT CODLOJA, ID_STATUS
                        FROM TB_LOJA 
                        WHERE UPPER(CODLOJA) STARTING WITH ?
                    """

                    cursor.execute(sql, (letras,))
                    resultados = cursor.fetchall()

                    # Compara cada resultado encontrado
                    for resultado in resultados:
                        if len(resultado) >= 2:
                            codigo_bd = str(resultado[0]).strip()
                            if comparar_numeros_loja(codigo_bd, codigo_normalizado):
                                loja_info = {
                                    "codigo_loja": codigo_bd,
                                    "id_status": (
                                        int(resultado[1])
                                        if resultado[1] is not None
                                        else 0
                                    ),
                                    "nome": "Nome não disponível",
                                }

                                self.logger.info(
                                    f"Loja encontrada com busca flexível: {loja_info}"
                                )
                                return loja_info

            return None

        except Exception as e:
            self.logger.debug(f"Erro na busca flexível: {e}")
            return None

    @log_operacao
    def atualizar_status_loja(self, codigo_loja: str, novo_status: int = 3) -> bool:
        """
        CORRIGIDA: Atualiza o ID_STATUS da loja na tabela TB_LOJA.
        Corrigido problema com cursor.rowcount no Firebird.

        Args:
            codigo_loja (str): Código da loja para atualizar.
            novo_status (int): Novo status (padrão: 3).

        Returns:
            bool: True se atualizado com sucesso, False caso contrário.
        """
        try:
            if not validar_numero_loja(codigo_loja):
                self.logger.error(f"Código de loja inválido: {codigo_loja}")
                return False

            # Primeiro verifica se a loja existe
            loja_info = self.buscar_loja_por_codigo(codigo_loja)
            if not loja_info:
                self.logger.error(f"Loja {codigo_loja} não encontrada para atualização")
                return False

            status_anterior = loja_info["id_status"]

            self.logger.info(
                f"Atualizando status da loja {codigo_loja} de {status_anterior} para {novo_status}..."
            )

            with self.obter_cursor() as cursor:
                # SQL para atualizar o status
                sql = """
                    UPDATE TB_LOJA 
                    SET ID_STATUS = ? 
                    WHERE CODLOJA = ?
                """

                self.logger.debug(
                    f"Executando SQL: {sql} com parâmetros: {novo_status}, {loja_info['codigo_loja']}"
                )

                # Executa a atualização usando o código exato encontrado no banco
                cursor.execute(sql, (novo_status, loja_info["codigo_loja"]))

                # Commit da transação
                self.conexao.commit()

                # CORREÇÃO: Verifica se a atualização foi bem-sucedida fazendo uma nova consulta
                # Em vez de confiar no cursor.rowcount que pode não funcionar corretamente no Firebird
                loja_info_atualizada = self.buscar_loja_por_codigo(codigo_loja)

                if (
                    loja_info_atualizada
                    and loja_info_atualizada["id_status"] == novo_status
                ):
                    self.logger.info(
                        f"✅ Status da loja {codigo_loja} atualizado com sucesso de {status_anterior} para {novo_status}"
                    )
                    return True
                elif (
                    loja_info_atualizada
                    and loja_info_atualizada["id_status"] == status_anterior
                ):
                    # Status não mudou - pode ser que já estava no valor desejado
                    if status_anterior == novo_status:
                        self.logger.info(
                            f"ℹ️  Loja {codigo_loja} já estava com status {novo_status}"
                        )
                        return True
                    else:
                        self.logger.warning(
                            f"❌ Status da loja {codigo_loja} não foi alterado (permanece {status_anterior})"
                        )
                        return False
                else:
                    self.logger.warning(
                        f"❌ Não foi possível confirmar a atualização da loja {codigo_loja}"
                    )
                    return False

        except fdb.DatabaseError as e:
            self.logger.error(
                f"Erro de banco ao atualizar status da loja {codigo_loja}: {e}"
            )
            try:
                if self.conexao:
                    self.conexao.rollback()
            except:
                pass
            return False
        except Exception as e:
            self.logger.error(
                f"Erro inesperado ao atualizar status da loja {codigo_loja}: {e}"
            )
            try:
                if self.conexao:
                    self.conexao.rollback()
            except:
                pass
            return False

    @log_operacao
    def listar_lojas_por_status(self, status: int) -> List[Dict[str, Any]]:
        """
        Lista todas as lojas com um determinado status.

        Args:
            status (int): Status para filtrar.

        Returns:
            List[Dict]: Lista de lojas com o status especificado.
        """
        try:
            self.logger.info(f"Listando lojas com status {status}...")

            with self.obter_cursor() as cursor:
                sql = """
                    SELECT CODLOJA, ID_STATUS
                    FROM TB_LOJA 
                    WHERE ID_STATUS = ?
                    ORDER BY CODLOJA
                """

                cursor.execute(sql, (status,))
                resultados = cursor.fetchall()

                lojas = []
                for resultado in resultados:
                    if len(resultado) >= 2:
                        loja_info = {
                            "codigo_loja": (
                                str(resultado[0]).strip() if resultado[0] else "N/A"
                            ),
                            "id_status": (
                                int(resultado[1]) if resultado[1] is not None else 0
                            ),
                            "nome": "Nome não disponível",
                        }
                        lojas.append(loja_info)

                self.logger.info(f"Encontradas {len(lojas)} lojas com status {status}")
                return lojas

        except fdb.DatabaseError as e:
            self.logger.error(f"Erro de banco ao listar lojas por status {status}: {e}")
            return []
        except Exception as e:
            self.logger.error(
                f"Erro inesperado ao listar lojas por status {status}: {e}"
            )
            return []

    def verificar_status_loja(self, codigo_loja: str) -> Optional[int]:
        """
        Verifica o status atual de uma loja.

        Args:
            codigo_loja (str): Código da loja.

        Returns:
            Optional[int]: Status atual da loja ou None se não encontrada.
        """
        try:
            loja_info = self.buscar_loja_por_codigo(codigo_loja)
            if loja_info:
                return loja_info["id_status"]
            return None

        except Exception as e:
            self.logger.error(f"Erro ao verificar status da loja {codigo_loja}: {e}")
            return None

    def testar_conexao(self) -> bool:
        """
        Testa a conexão com o banco Firebird.

        Returns:
            bool: True se conexão está funcionando, False caso contrário.
        """
        try:
            if not self.conectado or not self.conexao:
                return False

            with self.obter_cursor() as cursor:
                cursor.execute("SELECT 1 FROM RDB$DATABASE")
                resultado = cursor.fetchone()

                if resultado and resultado[0] == 1:
                    self.logger.info("Teste de conexão Firebird realizado com sucesso")
                    return True
                else:
                    return False

        except Exception as e:
            self.logger.error(f"Erro no teste de conexão Firebird: {e}")
            return False

    def obter_estatisticas_tabela(self) -> Dict[str, Any]:
        """
        Obtém estatísticas da tabela TB_LOJA.

        Returns:
            Dict: Estatísticas da tabela.
        """
        try:
            with self.obter_cursor() as cursor:
                # Total de lojas
                cursor.execute("SELECT COUNT(*) FROM TB_LOJA")
                resultado_total = cursor.fetchone()
                total_lojas = resultado_total[0] if resultado_total else 0

                # Lojas por status
                cursor.execute(
                    """
                    SELECT ID_STATUS, COUNT(*) 
                    FROM TB_LOJA 
                    GROUP BY ID_STATUS 
                    ORDER BY ID_STATUS
                """
                )
                resultados_status = cursor.fetchall()
                lojas_por_status = {}

                for resultado in resultados_status:
                    if len(resultado) >= 2:
                        status = int(resultado[0]) if resultado[0] is not None else 0
                        count = int(resultado[1]) if resultado[1] is not None else 0
                        lojas_por_status[status] = count

                estatisticas = {
                    "total_lojas": total_lojas,
                    "lojas_por_status": lojas_por_status,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                }

                self.logger.info(f"Estatísticas da tabela TB_LOJA: {estatisticas}")
                return estatisticas

        except Exception as e:
            self.logger.error(f"Erro ao obter estatísticas da tabela: {e}")
            return {"total_lojas": 0, "lojas_por_status": {}, "erro": str(e)}

    def desconectar(self):
        """Fecha a conexão com o banco Firebird."""
        try:
            if self.conexao:
                self.conexao.close()
                self.conexao = None
                self.conectado = False
                self.logger.info("Desconectado do Firebird")
        except Exception as e:
            self.logger.warning(f"Erro ao desconectar do Firebird: {e}")

    def __del__(self):
        """Destrutor para garantir que a conexão seja fechada."""
        self.desconectar()
