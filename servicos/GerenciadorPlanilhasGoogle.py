import gspread
from google.auth.exceptions import GoogleAuthError
from gspread.exceptions import APIError, SpreadsheetNotFound, WorksheetNotFound
from typing import List, Optional, Tuple, Any, Dict
import time

from configuracao.GerenciadorConfiguracao import GerenciadorConfiguracao
from utilitarios.logger import obter_logger, MixinLogger, log_operacao
from utilitarios.Utilitarios import (
    limpar_texto,
    normalizar_tipo_numero_loja,
    comparar_numeros_loja,
    safe_int,
    validar_codigo_alfanumerico,
    comparar_codigos_flexivel,
    converter_letra_coluna_para_numero,
)


class GerenciadorPlanilhasGoogle(MixinLogger):

    def __init__(self):
        self.config = GerenciadorConfiguracao()
        self.cliente = None
        self.planilha = None
        self.conectado = False

    @log_operacao
    def conectar(self) -> bool:
        try:
            self.logger.info("Iniciando conexão com Google Sheets...")

            self.cliente = gspread.service_account(
                filename=self.config.arquivo_credenciais
            )

            self.planilha = self.cliente.open_by_key(self.config.planilha_id)

            self.conectado = True
            self.logger.info("Conexão estabelecida com sucesso!")

            return True

        except GoogleAuthError as e:
            self.logger.error(f"Erro de autenticação: {e}")
            self.conectado = False
            return False
        except SpreadsheetNotFound as e:
            self.logger.error(f"Planilha não encontrada: {e}")
            self.conectado = False
            return False
        except Exception as e:
            self.logger.error(f"Erro inesperado ao conectar: {e}")
            self.conectado = False
            return False

    def obter_aba(self, nome_aba: str):
        if not self.conectado or not self.planilha:
            self.logger.error("Não conectado ao Google Sheets")
            return None

        try:
            aba = self.planilha.worksheet(nome_aba)
            self.logger.debug(f"Aba '{nome_aba}' acessada com sucesso")
            return aba

        except WorksheetNotFound:
            self.logger.error(f"Aba '{nome_aba}' não encontrada")
            return None
        except Exception as e:
            self.logger.error(f"Erro ao acessar aba '{nome_aba}': {e}")
            return None

    def buscar_numero_loja_na_aba_gerenciador(self, numero_loja: str) -> Optional[int]:
        if not numero_loja or not numero_loja.strip():
            self.logger.warning("Número da loja vazio ou inválido")
            return None

        aba = self.obter_aba(self.config.aba_gerenciador)
        if not aba:
            return None

        try:
            coluna_numero_loja = self.config.coluna_numero_loja_gerenciador
            linha_inicio = self.config.linha_inicio_gerenciador

            self.logger.debug(
                f"Buscando loja '{numero_loja}' na coluna {coluna_numero_loja} a partir da linha {linha_inicio}"
            )

            numero_loja_normalizado = normalizar_tipo_numero_loja(numero_loja)

            coluna_int = converter_letra_coluna_para_numero(coluna_numero_loja)
            if coluna_int <= 0:
                self.logger.error(f"Coluna inválida: {coluna_numero_loja}")
                return None

            try:
                valores_coluna = aba.col_values(coluna_int)
                self.logger.debug(f"Valores obtidos da coluna {coluna_numero_loja}: {len(valores_coluna)} células")
            except Exception as e:
                self.logger.error(f"Erro ao obter valores da coluna {coluna_numero_loja}: {e}")
                return None

            for linha_atual in range(linha_inicio, len(valores_coluna) + 1):
                try:
                    indice_lista = linha_atual - 1
                    if indice_lista >= len(valores_coluna):
                        break

                    valor_celula = valores_coluna[indice_lista]
                    if not valor_celula:
                        continue

                    if comparar_numeros_loja(valor_celula, numero_loja_normalizado):
                        self.logger.info(
                            f"Loja '{numero_loja}' encontrada na linha {linha_atual}"
                        )
                        return linha_atual

                except Exception as e:
                    self.logger.warning(
                        f"Erro ao processar linha {linha_atual}: {e}"
                    )
                    continue

            self.logger.info(f"Loja '{numero_loja}' não encontrada na aba Gerenciador")
            return None

        except APIError as e:
            self.logger.error(f"Erro da API Google Sheets: {e}")
            return None
        except Exception as e:
            self.logger.error(
                f"Erro inesperado ao buscar loja '{numero_loja}': {e}"
            )
            return None

    def obter_informacoes_completas_loja(
        self, numero_loja: str
    ) -> Optional[Dict[str, Any]]:
        try:
            linha_int = self.buscar_numero_loja_na_aba_gerenciador(numero_loja)
            if linha_int is None:
                return None

            aba = self.obter_aba(self.config.aba_gerenciador)
            if not aba:
                return None

            try:
                grupo = aba.cell(linha_int, 2).value
                grupo = limpar_texto(grupo) if grupo else "Não informado"

                nome_loja = aba.cell(linha_int, 7).value
                nome_loja = limpar_texto(nome_loja) if nome_loja else "Não informado"

                status_d = aba.cell(linha_int, 4).value
                status_d = limpar_texto(status_d) if status_d else "Não informado"

                status_i = aba.cell(linha_int, 9).value
                status_i = limpar_texto(status_i) if status_i else "Não informado"

                self.logger.debug(
                    f"Informações obtidas para loja {numero_loja} na linha {linha_int}"
                )
                self.logger.debug(f"  Grupo (B): '{grupo}'")
                self.logger.debug(f"  Nome (G): '{nome_loja}'")
                self.logger.debug(f"  Status D: '{status_d}'")
                self.logger.debug(f"  Status I: '{status_i}'")

                return {
                    "numero_loja": numero_loja,
                    "nome_loja": nome_loja,
                    "grupo": grupo,
                    "status_d": status_d,
                    "status_i": status_i,
                    "linha_gerenciador": linha_int,
                }

            except Exception as e:
                self.logger.error(
                    f"Erro ao obter dados da linha {linha_int}: {e}"
                )
                return None

        except Exception as e:
            self.logger.error(
                f"Erro ao obter informações completas da loja {numero_loja}: {e}"
            )
            return None

    def obter_nome_loja_por_numero(self, numero_loja: str) -> Optional[str]:
        info = self.obter_informacoes_completas_loja(numero_loja)
        if info and info.get("nome_loja"):
            nome = info["nome_loja"]
            if nome != "Não informado":
                return nome

        return None

    @log_operacao
    def aplicar_formatacao_laranja_linha(self, linha: int) -> bool:
        try:
            aba = self.obter_aba(self.config.aba_gerenciador)
            if not aba:
                return False

            formato_laranja = {
                "backgroundColor": {"red": 1.0, "green": 0.647, "blue": 0.0},
                "textFormat": {"bold": True}
            }

            range_linha = f"{linha}:{linha}"

            aba.format(range_linha, formato_laranja)

            time.sleep(0.5)

            self.logger.info(f"Formatação laranja aplicada à linha {linha}")
            return True

        except Exception as e:
            self.logger.error(f"Erro ao aplicar formatação laranja na linha {linha}: {e}")
            return False

    @log_operacao
    def aplicar_formatacao_lojas_fechadas(self, linha: int) -> bool:
        try:
            aba = self.obter_aba(self.config.aba_lojas_fechadas)
            if not aba:
                return False

            formato_verde = {
                "backgroundColor": {"red": 0.863, "green": 0.941, "blue": 0.776},  # #dcf0c6
                "horizontalAlignment": "CENTER"
            }

            range_linha = f"{linha}:{linha}"

            aba.format(range_linha, formato_verde)

            time.sleep(0.5)

            self.logger.info(f"Formatação verde aplicada à linha {linha} na aba Lojas Fechadas")
            return True

        except Exception as e:
            self.logger.error(f"Erro ao aplicar formatação na linha {linha}: {e}")
            return False

    @log_operacao
    def atualizar_status_loja_gerenciador(self, linha: int) -> bool:
        try:
            aba = self.obter_aba(self.config.aba_gerenciador)
            if not aba:
                return False

            coluna_status = self.config.coluna_status_gerenciador
            status_fechada = self.config.status_fechada

            coluna_int = converter_letra_coluna_para_numero(coluna_status)
            if coluna_int <= 0:
                self.logger.error(f"Coluna de status inválida: {coluna_status}")
                return False

            aba.update_cell(linha, coluna_int, status_fechada)

            time.sleep(0.5)

            if not self.aplicar_formatacao_laranja_linha(linha):
                self.logger.warning(f"Status atualizado mas formatação falhou na linha {linha}")

            self.logger.info(f"Status da linha {linha} atualizado para '{status_fechada}' com formatação")
            return True

        except Exception as e:
            self.logger.error(f"Erro ao atualizar status da linha {linha}: {e}")
            return False

    def encontrar_proxima_linha_vazia_lojas_fechadas(self) -> Optional[int]:
        try:
            aba = self.obter_aba(self.config.aba_lojas_fechadas)
            if not aba:
                return None

            valores = aba.get_all_values()
            if not valores:
                return 2

            for i, linha in enumerate(valores, start=1):
                if not any(cell.strip() for cell in linha if cell):
                    return i

            return len(valores) + 1

        except Exception as e:
            self.logger.error(f"Erro ao encontrar próxima linha vazia: {e}")
            return None

    def adicionar_loja_fechada(
        self, nome_loja: str, numero_loja: str, data_fechamento: str, observacao: str
    ) -> bool:
        try:
            aba = self.obter_aba(self.config.aba_lojas_fechadas)
            if not aba:
                return False

            linha = self.encontrar_proxima_linha_vazia_lojas_fechadas()
            if linha is None:
                self.logger.error("Não foi possível encontrar linha vazia")
                return False

            config_fechadas = self.config.config.get("configuracoes_lojas_fechadas", {})
            
            col_nome = converter_letra_coluna_para_numero(config_fechadas.get("coluna_nome_loja", "B"))
            col_numero = converter_letra_coluna_para_numero(config_fechadas.get("coluna_numero_loja", "C"))
            col_status = converter_letra_coluna_para_numero(config_fechadas.get("coluna_status", "D"))
            col_data = converter_letra_coluna_para_numero(config_fechadas.get("coluna_data_fechamento", "E"))
            col_obs = converter_letra_coluna_para_numero(config_fechadas.get("coluna_observacao", "F"))
            
            status_padrao = self.config.valor_padrao_status_fechadas

            updates = [
                (linha, col_nome, nome_loja),
                (linha, col_numero, numero_loja),
                (linha, col_status, status_padrao),
                (linha, col_data, data_fechamento),
                (linha, col_obs, observacao),
            ]

            for lin, col, valor in updates:
                if col > 0:
                    aba.update_cell(lin, col, valor)
                    time.sleep(0.3)

            if not self.aplicar_formatacao_lojas_fechadas(linha):
                self.logger.warning(f"Loja adicionada mas formatação falhou na linha {linha}")

            self.logger.info(f"Loja {numero_loja} adicionada na linha {linha} da aba Lojas Fechadas")
            return True

        except Exception as e:
            self.logger.error(f"Erro ao adicionar loja fechada: {e}")
            return False

    def testar_conexao(self) -> bool:
        try:
            if not self.conectado or not self.planilha:
                return False

            aba_teste = self.obter_aba(self.config.aba_gerenciador)
            if not aba_teste:
                return False

            aba_teste.cell(1, 1)
            return True

        except Exception as e:
            self.logger.error(f"Teste de conexão falhou: {e}")
            return False

    def desconectar(self):
        self.cliente = None
        self.planilha = None
        self.conectado = False
        self.logger.info("Desconectado do Google Sheets")