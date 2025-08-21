import fdb
from typing import Optional, List, Tuple, Any, Dict
import time
from contextlib import contextmanager

from configuracao.GerenciadorConfiguracao import GerenciadorConfiguracao
from utilitarios.logger import obter_logger, MixinLogger, log_operacao
from utilitarios.Utilitarios import (
    validar_numero_loja,
    normalizar_tipo_numero_loja,
    safe_int,
    validar_codigo_alfanumerico,
    comparar_numeros_loja,
)


class GerenciadorFirebird(MixinLogger):

    def __init__(self):
        self.config = GerenciadorConfiguracao()
        self.conexao = None
        self.conectado = False

        self.host = self.config.firebird_host
        self.database = self.config.firebird_database
        self.user = self.config.firebird_user
        self.password = self.config.firebird_password
        self.charset = self.config.firebird_charset
        self.port = self.config.firebird_port

    def conectar(self) -> bool:
        try:
            if self.conectado and self.conexao:
                return True

            self.logger.info(f"Conectando ao Firebird em {self.host}:{self.port}")

            dsn = f"{self.host}/{self.port}:{self.database}"

            self.conexao = fdb.connect(
                dsn=dsn,
                user=self.user,
                password=self.password,
                charset=self.charset,
            )

            self.conectado = True
            self.logger.info("Conectado ao Firebird com sucesso")
            return True

        except Exception as e:
            self.logger.error(f"Erro ao conectar no Firebird: {e}")
            self.conectado = False
            return False

    @contextmanager
    def obter_cursor(self):
        if not self.conectado or not self.conexao:
            raise Exception("Não conectado ao banco Firebird")

        cursor = self.conexao.cursor()
        try:
            yield cursor
        finally:
            cursor.close()

    @log_operacao
    def verificar_estrutura_tabela(self) -> bool:
        try:
            with self.obter_cursor() as cursor:
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

                sql_colunas = """
                    SELECT RDB$FIELD_NAME 
                    FROM RDB$RELATION_FIELDS 
                    WHERE RDB$RELATION_NAME = 'TB_LOJA' 
                    AND RDB$FIELD_NAME IN ('CODLOJA', 'ID_STATUS')
                """
                cursor.execute(sql_colunas)
                colunas = cursor.fetchall()

                colunas_esperadas = {'CODLOJA', 'ID_STATUS'}
                colunas_encontradas = {col[0].strip() for col in colunas}

                if not colunas_esperadas.issubset(colunas_encontradas):
                    faltando = colunas_esperadas - colunas_encontradas
                    self.logger.error(f"Colunas necessárias não encontradas: {faltando}")
                    return False

                self.logger.info("Estrutura da tabela TB_LOJA verificada com sucesso")
                return True

        except Exception as e:
            self.logger.error(f"Erro ao verificar estrutura da tabela: {e}")
            return False

    def buscar_loja_por_codigo(self, codigo_loja: str) -> Optional[Dict[str, Any]]:
        if not validar_numero_loja(codigo_loja):
            self.logger.warning(f"Código de loja inválido: {codigo_loja}")
            return None

        try:
            tabela = self.config.firebird_tabela_loja
            coluna_codigo = self.config.firebird_coluna_codigo
            coluna_status = self.config.firebird_coluna_status

            with self.obter_cursor() as cursor:
                codigo_normalizado = normalizar_tipo_numero_loja(codigo_loja)

                if validar_codigo_alfanumerico(codigo_normalizado):
                    resultado = self._buscar_loja_alfanumerica_flexivel(
                        cursor, codigo_normalizado, tabela, coluna_codigo, coluna_status
                    )
                    if resultado:
                        return resultado

                try:
                    codigo_numerico = int(codigo_normalizado)
                    sql = f"""
                        SELECT {coluna_codigo}, {coluna_status}
                        FROM {tabela}
                        WHERE {coluna_codigo} = ?
                    """
                    cursor.execute(sql, (codigo_numerico,))
                    resultado = cursor.fetchone()

                    if resultado:
                        return {
                            "codigo_loja": str(resultado[0]),
                            "id_status": safe_int(resultado[1]),
                        }

                except ValueError:
                    pass

                sql_texto = f"""
                    SELECT {coluna_codigo}, {coluna_status}
                    FROM {tabela}
                    WHERE UPPER(TRIM({coluna_codigo})) = UPPER(?)
                """
                cursor.execute(sql_texto, (codigo_normalizado,))
                resultado = cursor.fetchone()

                if resultado:
                    return {
                        "codigo_loja": str(resultado[0]),
                        "id_status": safe_int(resultado[1]),
                    }

                return None

        except Exception as e:
            self.logger.error(f"Erro ao buscar loja por código '{codigo_loja}': {e}")
            return None

    def _buscar_loja_alfanumerica_flexivel(
        self, cursor, codigo_normalizado: str, tabela: str, coluna_codigo: str, coluna_status: str
    ) -> Optional[Dict[str, Any]]:
        try:
            sql_like = f"""
                SELECT {coluna_codigo}, {coluna_status}
                FROM {tabela}
                WHERE UPPER(TRIM({coluna_codigo})) LIKE UPPER(?)
            """

            padroes = [
                f"{codigo_normalizado}%",
                f"%{codigo_normalizado}",
                f"%{codigo_normalizado}%",
            ]

            for padrao in padroes:
                cursor.execute(sql_like, (padrao,))
                resultados = cursor.fetchall()

                if resultados:
                    for resultado in resultados:
                        codigo_db = str(resultado[0]).strip()
                        if comparar_numeros_loja(codigo_db, codigo_normalizado):
                            return {
                                "codigo_loja": codigo_db,
                                "id_status": safe_int(resultado[1]),
                            }

            return None

        except Exception as e:
            self.logger.warning(f"Erro na busca flexível para '{codigo_normalizado}': {e}")
            return None

    @log_operacao
    def atualizar_status_loja(self, codigo_loja: str, novo_status: int = 3) -> bool:
        try:
            loja = self.buscar_loja_por_codigo(codigo_loja)
            if not loja:
                self.logger.error(f"Loja '{codigo_loja}' não encontrada para atualização")
                return False

            tabela = self.config.firebird_tabela_loja
            coluna_codigo = self.config.firebird_coluna_codigo
            coluna_status = self.config.firebird_coluna_status

            with self.obter_cursor() as cursor:
                try:
                    codigo_numerico = int(loja["codigo_loja"])
                    sql = f"""
                        UPDATE {tabela}
                        SET {coluna_status} = ?
                        WHERE {coluna_codigo} = ?
                    """
                    cursor.execute(sql, (novo_status, codigo_numerico))
                except ValueError:
                    sql = f"""
                        UPDATE {tabela}
                        SET {coluna_status} = ?
                        WHERE UPPER(TRIM({coluna_codigo})) = UPPER(?)
                    """
                    cursor.execute(sql, (novo_status, loja["codigo_loja"]))

                self.conexao.commit()

                self.logger.info(f"Status da loja '{codigo_loja}' atualizado para {novo_status}")
                return True

        except Exception as e:
            if self.conexao:
                try:
                    self.conexao.rollback()
                except:
                    pass
            self.logger.error(f"Erro ao atualizar status da loja '{codigo_loja}': {e}")
            return False

    def listar_lojas_por_status(self, status: int) -> List[Dict[str, Any]]:
        try:
            tabela = self.config.firebird_tabela_loja
            coluna_codigo = self.config.firebird_coluna_codigo
            coluna_status = self.config.firebird_coluna_status

            with self.obter_cursor() as cursor:
                sql = f"""
                    SELECT {coluna_codigo}, {coluna_status}
                    FROM {tabela}
                    WHERE {coluna_status} = ?
                    ORDER BY {coluna_codigo}
                """
                cursor.execute(sql, (status,))
                resultados = cursor.fetchall()

                lojas = []
                for resultado in resultados:
                    lojas.append({
                        "codigo_loja": str(resultado[0]),
                        "id_status": safe_int(resultado[1]),
                    })

                self.logger.info(f"Encontradas {len(lojas)} lojas com status {status}")
                return lojas

        except Exception as e:
            self.logger.error(f"Erro ao listar lojas por status {status}: {e}")
            return []

    def verificar_status_loja(self, codigo_loja: str) -> Optional[int]:
        loja = self.buscar_loja_por_codigo(codigo_loja)
        return loja["id_status"] if loja else None

    def testar_conexao(self) -> bool:
        try:
            if not self.conectado or not self.conexao:
                return False

            with self.obter_cursor() as cursor:
                cursor.execute("SELECT 1 FROM RDB$DATABASE")
                resultado = cursor.fetchone()
                return resultado is not None

        except Exception as e:
            self.logger.error(f"Teste de conexão falhou: {e}")
            return False

    def obter_estatisticas_tabela(self) -> Dict[str, Any]:
        try:
            tabela = self.config.firebird_tabela_loja
            coluna_status = self.config.firebird_coluna_status

            with self.obter_cursor() as cursor:
                sql_total = f"SELECT COUNT(*) FROM {tabela}"
                cursor.execute(sql_total)
                total = cursor.fetchone()[0]

                sql_status = f"""
                    SELECT {coluna_status}, COUNT(*)
                    FROM {tabela}
                    GROUP BY {coluna_status}
                    ORDER BY {coluna_status}
                """
                cursor.execute(sql_status)
                status_counts = cursor.fetchall()

                estatisticas = {
                    "total_lojas": total,
                    "por_status": {safe_int(status): count for status, count in status_counts},
                }

                return estatisticas

        except Exception as e:
            self.logger.error(f"Erro ao obter estatísticas: {e}")
            return {}

    def desconectar(self):
        try:
            if self.conexao:
                self.conexao.close()
                self.logger.info("Conexão Firebird fechada")
        except Exception as e:
            self.logger.warning(f"Erro ao fechar conexão: {e}")
        finally:
            self.conexao = None
            self.conectado = False

    def __del__(self):
        self.desconectar()