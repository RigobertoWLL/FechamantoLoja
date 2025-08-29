"""
Módulo para integração com Google Sheets API.
ATUALIZADO: Removido método limpar_colunas_gerenciador
"""

import gspread
from google.auth.exceptions import GoogleAuthError
from gspread.exceptions import APIError, SpreadsheetNotFound, WorksheetNotFound
from typing import Optional, Any, Dict

from manager.ConfigManager import ConfigManager
from logger.Logger import LoggerMixin, log_operacao
from utils.Utils import (
    limpar_texto,
    normalizar_tipo_numero_loja,
    comparar_numeros_loja,
    safe_int,
    validar_codigo_alfanumerico,
    comparar_codigos_flexivel,
    converter_letra_coluna_para_numero,
)


class GoogleSheetsManager(LoggerMixin):
    """Classe para gerenciar operações com Google Sheets."""

    def __init__(self):
        """Inicializa o gerenciador do Google Sheets."""
        self.config = ConfigManager()
        self.cliente = None
        self.planilha = None
        self.conectado = False

    @log_operacao
    def conectar(self) -> bool:
        """
        Estabelece conexão com Google Sheets usando as credenciais.

        Returns:
            bool: True se conectado com sucesso, False caso contrário.
        """
        try:
            self.logger.info("Iniciando conexão com Google Sheets...")

            # Autentica usando arquivo de credenciais
            self.cliente = gspread.service_account(
                filename=self.config.arquivo_credenciais
            )

            # Abre a planilha
            self.planilha = self.cliente.open_by_key(self.config.planilha_id)

            self.conectado = True
            self.logger.info("Conexão estabelecida com sucesso!")
            return True

        except FileNotFoundError:
            self.logger.error(
                f"Arquivo de credenciais não encontrado: {self.config.arquivo_credenciais}"
            )
            return False
        except GoogleAuthError as e:
            self.logger.error(f"Erro de autenticação: {e}")
            return False
        except SpreadsheetNotFound:
            self.logger.error(
                f"Planilha não encontrada com ID: {self.config.planilha_id}"
            )
            return False
        except Exception as e:
            self.logger.error(f"Erro inesperado ao conectar: {e}")
            return False

    def obter_aba(self, nome_aba: str):
        """
        Obtém uma aba específica da planilha.

        Args:
            nome_aba (str): Nome da aba.

        Returns:
            Worksheet: Objeto da aba ou None se não encontrada.
        """
        if not self.conectado:
            self.logger.error("Não conectado ao Google Sheets")
            return None

        try:
            aba = self.planilha.worksheet(nome_aba)
            self.logger.debug(f"Aba '{nome_aba}' obtida com sucesso")
            return aba
        except WorksheetNotFound:
            self.logger.error(f"Aba '{nome_aba}' não encontrada")
            return None
        except Exception as e:
            self.logger.error(f"Erro ao obter aba '{nome_aba}': {e}")
            return None

    def buscar_numero_loja_na_aba_gerenciador(self, numero_loja: str) -> Optional[int]:
        """
        Busca o número da loja na aba Gerenciador e retorna a linha onde foi encontrada.

        Args:
            numero_loja (str): Número da loja para buscar.

        Returns:
            Optional[int]: Número da linha onde a loja foi encontrada ou None.
        """
        try:
            aba = self.obter_aba(self.config.aba_gerenciador)
            if not aba:
                return None

            self.logger.info(f"Buscando loja {numero_loja} na aba Gerenciador...")

            # Converte letra da coluna para número
            coluna_letra = self.config.coluna_numero_loja_gerenciador  # "C"
            coluna_numero = converter_letra_coluna_para_numero(coluna_letra)  # 3

            self.logger.debug(
                f"Coluna configurada: '{coluna_letra}' -> número {coluna_numero}"
            )

            # Obtém todos os valores da coluna C usando o número da coluna
            coluna_valores = aba.col_values(
                coluna_numero,
                value_render_option="UNFORMATTED_VALUE",
            )

            # Normaliza o número da loja procurado
            numero_loja_normalizado = normalizar_tipo_numero_loja(numero_loja)

            # Converte linha_inicio para int ANTES de usar
            linha_inicio_raw = self.config.linha_inicio_gerenciador
            linha_inicio = safe_int(linha_inicio_raw, 6)

            self.logger.debug(
                f"Procurando loja normalizada: '{numero_loja_normalizado}'"
            )
            self.logger.debug(
                f"Linha de início: {linha_inicio} (convertido de {linha_inicio_raw}, tipo original: {type(linha_inicio_raw)})"
            )

            # Identifica se é código alfanumérico para busca especializada
            eh_codigo_alfanumerico = validar_codigo_alfanumerico(
                numero_loja_normalizado
            )
            if eh_codigo_alfanumerico:
                self.logger.debug(
                    f"Detectado código alfanumérico: {numero_loja_normalizado}"
                )

            # Busca o número da loja com comparações seguras
            for indice_lista, valor_celula in enumerate(coluna_valores):
                # IMPORTANTE: indice_lista é baseado em 0, mas linha da planilha é baseada em 1
                linha_planilha = indice_lista + 1

                # Garante que ambas as variáveis sejam int antes da comparação
                linha_planilha_int = safe_int(linha_planilha, 0)
                linha_inicio_int = safe_int(linha_inicio, 6)

                self.logger.debug(
                    f"Comparando linhas: linha_planilha_int={linha_planilha_int} >= linha_inicio_int={linha_inicio_int}"
                )

                # Só considera linhas a partir da linha configurada
                if linha_planilha_int >= linha_inicio_int:
                    # Normaliza o valor da planilha para comparação segura
                    valor_normalizado = normalizar_tipo_numero_loja(valor_celula)

                    self.logger.debug(
                        f"Linha {linha_planilha_int}: valor_original='{valor_celula}' (tipo:{type(valor_celula)}) -> valor_normalizado='{valor_normalizado}'"
                    )

                    # Usa a função de comparação segura
                    if comparar_numeros_loja(
                        valor_normalizado, numero_loja_normalizado
                    ):
                        self.logger.info(
                            f"Loja {numero_loja} encontrada na linha {linha_planilha_int} (comparação exata)"
                        )
                        return linha_planilha_int

                    # Para códigos alfanuméricos, tenta busca flexível adicional
                    if eh_codigo_alfanumerico and validar_codigo_alfanumerico(
                        valor_normalizado
                    ):
                        if comparar_codigos_flexivel(
                            valor_normalizado, numero_loja_normalizado
                        ):
                            self.logger.info(
                                f"Loja {numero_loja} encontrada na linha {linha_planilha_int} (comparação flexível: {valor_normalizado} ≈ {numero_loja_normalizado})"
                            )
                            return linha_planilha_int

            self.logger.warning(f"Loja {numero_loja} não encontrada na aba Gerenciador")

            # Log adicional para debug
            if eh_codigo_alfanumerico:
                self.logger.debug(
                    f"Busca para código alfanumérico '{numero_loja_normalizado}' não encontrou correspondência"
                )

            # Debug: mostra alguns valores encontrados na coluna
            self.logger.debug("Primeiros valores encontrados na coluna (para debug):")
            for i, val in enumerate(coluna_valores[:5]):
                val_norm = normalizar_tipo_numero_loja(val)
                linha_real = i + 1
                if linha_real >= linha_inicio_int:
                    self.logger.debug(f"  Linha {linha_real}: '{val}' -> '{val_norm}'")

            return None

        except APIError as e:
            self.logger.error(f"Erro da API ao buscar loja: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Erro inesperado ao buscar loja: {e}")
            # Log adicional para debug do erro específico
            import traceback

            self.logger.error(f"Traceback completo: {traceback.format_exc()}")
            return None

    def obter_informacoes_completas_loja(
        self, numero_loja: str
    ) -> Optional[Dict[str, Any]]:
        """
        Obtém informações completas da loja incluindo Grupo, Nome e Status.

        Args:
            numero_loja (str): Número da loja.

        Returns:
            Optional[Dict]: Dicionário com informações da loja ou None se não encontrada.
        """
        try:
            linha = self.buscar_numero_loja_na_aba_gerenciador(numero_loja)
            if linha is None:
                return None

            aba = self.obter_aba(self.config.aba_gerenciador)
            if not aba:
                return None

            # Garante que linha seja inteiro
            linha_int = safe_int(linha, 0)
            if linha_int <= 0:
                self.logger.error(f"Linha inválida: {linha}")
                return None

            # Obtém informações das colunas específicas
            try:
                # Coluna B - Grupo
                grupo = aba.cell(linha_int, 2).value  # Coluna B = 2
                grupo = limpar_texto(grupo) if grupo else "Não informado"

                # Coluna G - Nome da loja
                nome_loja = aba.cell(linha_int, 7).value  # Coluna G = 7
                nome_loja = (
                    limpar_texto(nome_loja) if nome_loja else "Nome não encontrado"
                )

                # Coluna D - Status Principal
                status_d = aba.cell(linha_int, 4).value  # Coluna D = 4
                status_d = limpar_texto(status_d) if status_d else "Não informado"

                # Coluna I - Status Secundário
                status_i = aba.cell(linha_int, 9).value  # Coluna I = 9
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
                    "linha_gerenciador": linha_int,
                    "grupo": grupo,
                    "nome_loja": nome_loja,
                    "status_d": status_d,
                    "status_i": status_i,
                }

            except Exception as e:
                self.logger.error(f"Erro ao obter células da linha {linha_int}: {e}")
                return None

        except Exception as e:
            self.logger.error(
                f"Erro ao obter informações completas da loja {numero_loja}: {e}"
            )
            return None

    def obter_nome_loja_por_numero(self, numero_loja: str) -> Optional[str]:
        """
        Obtém o nome da loja pelo seu número na aba Gerenciador.

        Args:
            numero_loja (str): Número da loja.

        Returns:
            Optional[str]: Nome da loja ou None se não encontrada.
        """
        try:
            linha = self.buscar_numero_loja_na_aba_gerenciador(numero_loja)
            if linha is None:
                return None

            aba = self.obter_aba(self.config.aba_gerenciador)
            if not aba:
                return None

            # Garante que linha seja inteiro
            linha_int = safe_int(linha, 0)
            if linha_int <= 0:
                self.logger.error(f"Linha inválida: {linha}")
                return None

            # Nome está na coluna G (7)
            nome = aba.cell(linha_int, 7).value  # Coluna G = 7
            return limpar_texto(nome) if nome else "Nome não encontrado"

        except Exception as e:
            self.logger.error(f"Erro ao obter nome da loja: {e}")
            return None

    @log_operacao
    def aplicar_formatacao_laranja_linha(self, linha: int) -> bool:
        """
        Aplica formatação laranja em toda a linha da aba Gerenciador.

        Args:
            linha (int): Linha para aplicar formatação.

        Returns:
            bool: True se aplicado com sucesso, False caso contrário.
        """
        try:
            aba = self.obter_aba(self.config.aba_gerenciador)
            if not aba:
                return False

            # Garante que linha seja inteiro
            linha_int = safe_int(linha, 0)
            if linha_int <= 0:
                self.logger.error(f"Linha inválida para formatação: {linha}")
                return False

            # Define o range da linha inteira (colunas A até Z)
            range_linha = f"A{linha_int}:Z{linha_int}"

            # Formato laranja
            formato_laranja = {
                "backgroundColor": {
                    "red": 1.0,  # 255/255
                    "green": 0.647,  # 165/255
                    "blue": 0.0,  # 0/255
                    # Resultado: #FFA500 (laranja)
                }
            }

            self.logger.debug(
                f"Aplicando formatação laranja na linha {linha_int}, range: {range_linha}"
            )

            # Aplica a formatação
            aba.format(range_linha, formato_laranja)

            self.logger.info(
                f"Formatação laranja aplicada na linha {linha_int} da aba Gerenciador"
            )
            return True

        except APIError as e:
            self.logger.error(f"Erro da API ao aplicar formatação laranja: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Erro inesperado ao aplicar formatação laranja: {e}")
            import traceback

            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return False

    @log_operacao
    def aplicar_formatacao_lojas_fechadas(self, linha: int) -> bool:
        """
        Aplica formatação específica para aba Lojas Fechadas.
        Cor: #DCF0C6, Alinhamento: Centro, Bordas: Sim

        Args:
            linha (int): Linha para aplicar formatação.

        Returns:
            bool: True se aplicado com sucesso, False caso contrário.
        """
        try:
            aba = self.obter_aba(self.config.aba_lojas_fechadas)
            if not aba:
                return False

            # Garante que linha seja inteiro
            linha_int = safe_int(linha, 0)
            if linha_int <= 0:
                self.logger.error(f"Linha inválida para formatação: {linha}")
                return False

            # Define o range das colunas A até F
            range_linha = f"A{linha_int}:F{linha_int}"

            # Formatação específica para Lojas Fechadas
            formatacao_lojas_fechadas = {
                "backgroundColor": {
                    "red": 0.863,  # 220/255 = 0.863 (DC)
                    "green": 0.941,  # 240/255 = 0.941 (F0)
                    "blue": 0.776,  # 198/255 = 0.776 (C6)
                    # Resultado: #DCF0C6 (verde claro)
                },
                "horizontalAlignment": "CENTER",
                "verticalAlignment": "MIDDLE",
                "borders": {
                    "top": {
                        "style": "SOLID",
                        "width": 1,
                        "color": {"red": 0.0, "green": 0.0, "blue": 0.0},
                    },
                    "bottom": {
                        "style": "SOLID",
                        "width": 1,
                        "color": {"red": 0.0, "green": 0.0, "blue": 0.0},
                    },
                    "left": {
                        "style": "SOLID",
                        "width": 1,
                        "color": {"red": 0.0, "green": 0.0, "blue": 0.0},
                    },
                    "right": {
                        "style": "SOLID",
                        "width": 1,
                        "color": {"red": 0.0, "green": 0.0, "blue": 0.0},
                    },
                },
            }

            self.logger.debug(
                f"Aplicando formatação específica na linha {linha_int}, range: {range_linha}"
            )
            self.logger.debug(f"Formatação: cor #DCF0C6, centro, bordas")

            # Aplica a formatação
            aba.format(range_linha, formatacao_lojas_fechadas)

            self.logger.info(
                f"Formatação específica aplicada na linha {linha_int} da aba Lojas Fechadas"
            )
            return True

        except APIError as e:
            self.logger.warning(f"Erro da API ao aplicar formatação específica: {e}")
            return False  # Não crítico
        except Exception as e:
            self.logger.warning(f"Erro ao aplicar formatação específica: {e}")
            import traceback

            self.logger.debug(f"Traceback formatação: {traceback.format_exc()}")
            return False  # Não crítico

    @log_operacao
    def atualizar_status_loja_gerenciador(self, linha: int) -> bool:
        """
        Atualiza o status da loja na aba Gerenciador com formato correto da API.

        Args:
            linha (int): Linha onde a loja está localizada.

        Returns:
            bool: True se atualizado com sucesso, False caso contrário.
        """
        try:
            aba = self.obter_aba(self.config.aba_gerenciador)
            if not aba:
                return False

            # Garante que linha seja inteiro
            linha_int = safe_int(linha, 0)
            if linha_int <= 0:
                self.logger.error(f"Linha inválida: {linha}")
                return False

            # Atualiza o status para "Fechada" com formato correto da API
            celula_status = f"{self.config.coluna_status_gerenciador}{linha_int}"

            # Usar formato de lista de listas
            aba.update(celula_status, [[self.config.status_fechada]])

            self.logger.info(
                f"Status atualizado para '{self.config.status_fechada}' na linha {linha_int}"
            )

            # Aplica formatação laranja na linha inteira
            if not self.aplicar_formatacao_laranja_linha(linha_int):
                self.logger.warning(
                    f"Erro ao aplicar formatação laranja na linha {linha_int}, mas prosseguindo..."
                )

            return True

        except APIError as e:
            self.logger.error(f"Erro da API ao atualizar status: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Erro inesperado ao atualizar status: {e}")
            return False

    def encontrar_proxima_linha_vazia_lojas_fechadas(self) -> Optional[int]:
        """
        Encontra a próxima linha vazia na aba Lojas Fechadas.

        Returns:
            Optional[int]: Número da próxima linha vazia ou None em caso de erro.
        """
        try:
            aba = self.obter_aba(self.config.aba_lojas_fechadas)
            if not aba:
                return None

            # Converte letra da coluna para número
            coluna_letra = self.config.coluna_nome_loja_fechadas  # "B"
            coluna_numero = converter_letra_coluna_para_numero(coluna_letra)  # 2

            # Obtém todos os valores da coluna B (nome da loja)
            valores_coluna_b = aba.col_values(coluna_numero)

            # A próxima linha vazia é o tamanho da lista + 1
            proxima_linha = len(valores_coluna_b) + 1

            self.logger.debug(
                f"Próxima linha vazia na aba Lojas Fechadas: {proxima_linha}"
            )
            return proxima_linha

        except APIError as e:
            self.logger.error(f"Erro da API ao encontrar linha vazia: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Erro inesperado ao encontrar linha vazia: {e}")
            return None

    @log_operacao
    def adicionar_loja_fechada(
        self, nome_loja: str, numero_loja: str, data_fechamento: str, observacao: str
    ) -> bool:
        """
        Adiciona uma nova loja na aba Lojas Fechadas com formatação específica.

        Args:
            nome_loja (str): Nome da loja.
            numero_loja (str): Número da loja.
            data_fechamento (str): Data de fechamento.
            observacao (str): Observação sobre o fechamento.

        Returns:
            bool: True se adicionado com sucesso, False caso contrário.
        """
        try:
            aba = self.obter_aba(self.config.aba_lojas_fechadas)
            if not aba:
                return False

            linha = self.encontrar_proxima_linha_vazia_lojas_fechadas()
            if linha is None:
                return False

            # Garante que linha seja inteiro
            linha_int = safe_int(linha, 0)
            if linha_int <= 0:
                self.logger.error(f"Linha inválida: {linha}")
                return False

            # Prepara os dados para inserir usando batch_update (formato correto)
            updates = [
                {
                    "range": f"{self.config.coluna_nome_loja_fechadas}{linha_int}",
                    "values": [[nome_loja]],
                },
                {
                    "range": f"{self.config.coluna_numero_loja_fechadas}{linha_int}",
                    "values": [[numero_loja]],
                },
                {
                    "range": f"{self.config.coluna_status_fechadas}{linha_int}",
                    "values": [[self.config.valor_padrao_status_fechadas]],
                },
                {
                    "range": f"{self.config.coluna_data_fechamento}{linha_int}",
                    "values": [[data_fechamento]],
                },
                {
                    "range": f"{self.config.coluna_observacao}{linha_int}",
                    "values": [[observacao]],
                },
            ]

            # Executa batch_update
            aba.batch_update(updates)

            # Aplica formatação específica (cor #DCF0C6, centro, bordas)
            if not self.aplicar_formatacao_lojas_fechadas(linha_int):
                self.logger.warning(
                    f"Erro ao aplicar formatação na linha {linha_int}, mas dados foram inseridos"
                )

            self.logger.info(
                f"Loja {numero_loja} adicionada à aba Lojas Fechadas na linha {linha_int}"
            )
            return True

        except APIError as e:
            self.logger.error(f"Erro da API ao adicionar loja fechada: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Erro inesperado ao adicionar loja fechada: {e}")
            import traceback

            self.logger.error(f"Traceback completo: {traceback.format_exc()}")
            return False

    def testar_conexao(self) -> bool:
        """
        Testa a conexão com a planilha fazendo uma operação simples.

        Returns:
            bool: True se conexão está funcionando, False caso contrário.
        """
        try:
            if not self.conectado:
                return False

            # Tenta obter as abas principais
            aba_gerenciador = self.obter_aba(self.config.aba_gerenciador)
            aba_lojas_fechadas = self.obter_aba(self.config.aba_lojas_fechadas)

            if aba_gerenciador is None or aba_lojas_fechadas is None:
                return False

            self.logger.info("Teste de conexão realizado com sucesso")
            return True

        except Exception as e:
            self.logger.error(f"Erro no teste de conexão: {e}")
            return False

    def desconectar(self):
        """Limpa a conexão com Google Sheets."""
        self.cliente = None
        self.planilha = None
        self.conectado = False
        self.logger.info("Desconectado do Google Sheets")
