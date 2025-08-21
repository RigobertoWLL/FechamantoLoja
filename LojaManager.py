"""
Módulo para gerenciar operações de fechamento de lojas.
ATUALIZADO: Removida operação de limpeza das colunas A e B
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass

from GoogleSheetsManager import GoogleSheetsManager
from Logger import LoggerMixin, log_operacao
from Utils import (
    validar_numero_loja,
    validar_nome_loja,
    obter_data_atual,
    criar_observacao_padrao,
    formatar_lista_lojas,
)


@dataclass
class ResultadoFechamento:
    """Classe para representar o resultado de um fechamento de loja."""

    sucesso: bool
    mensagem: str
    detalhes: Optional[Dict[str, Any]] = None


class LojaManager(LoggerMixin):
    """Classe para gerenciar operações de fechamento de lojas."""

    def __init__(self):
        """Inicializa o gerenciador de lojas."""
        self.sheets_manager = GoogleSheetsManager()

    def conectar(self) -> bool:
        """
        Conecta ao Google Sheets.

        Returns:
            bool: True se conectado com sucesso, False caso contrário.
        """
        return self.sheets_manager.conectar()

    def desconectar(self):
        """Desconecta do Google Sheets."""
        self.sheets_manager.desconectar()
        self.logger.info("Gerenciador de lojas desconectado")

    def obter_informacoes_loja(self, numero_loja: str) -> Optional[Dict[str, Any]]:
        """
        Obtém informações completas da loja incluindo Grupo e Status.

        Args:
            numero_loja (str): Número da loja.

        Returns:
            Optional[Dict]: Informações da loja ou None se não encontrada.
        """
        try:
            if not validar_numero_loja(numero_loja):
                self.logger.warning(f"Número de loja inválido: {numero_loja}")
                return None

            # Usa a nova função que obtém informações completas
            info = self.sheets_manager.obter_informacoes_completas_loja(numero_loja)

            if info:
                self.logger.debug(
                    f"Informações obtidas para loja {numero_loja}: {info}"
                )
            else:
                self.logger.debug(f"Loja {numero_loja} não encontrada")

            return info

        except Exception as e:
            self.logger.error(f"Erro ao obter informações da loja {numero_loja}: {e}")
            return None

    @log_operacao
    def fechar_loja(
        self, numero_loja: str, observacao: Optional[str] = None
    ) -> ResultadoFechamento:
        """
        ATUALIZADO: Fecha uma loja específica (SEM limpeza de colunas A e B).

        Args:
            numero_loja (str): Número da loja para fechar.
            observacao (Optional[str]): Observação personalizada.

        Returns:
            ResultadoFechamento: Resultado da operação.
        """
        try:
            # Validação inicial
            if not validar_numero_loja(numero_loja):
                return ResultadoFechamento(
                    sucesso=False, mensagem=f"Número de loja inválido: {numero_loja}"
                )

            # Busca a loja na aba Gerenciador
            linha = self.sheets_manager.buscar_numero_loja_na_aba_gerenciador(
                numero_loja
            )
            if linha is None:
                return ResultadoFechamento(
                    sucesso=False,
                    mensagem=f"Loja {numero_loja} não encontrada na aba Gerenciador",
                )

            # Obtém o nome da loja
            nome_loja = self.sheets_manager.obter_nome_loja_por_numero(numero_loja)
            if not nome_loja:
                nome_loja = f"Loja {numero_loja}"

            # Atualiza status na aba Gerenciador (inclui formatação laranja)
            if not self.sheets_manager.atualizar_status_loja_gerenciador(linha):
                return ResultadoFechamento(
                    sucesso=False,
                    mensagem=f"Erro ao atualizar status da loja {numero_loja}",
                )

            # REMOVIDO: Limpeza das colunas A e B
            # A linha anterior `limpar_colunas_gerenciador` foi removida

            # Prepara dados para aba Lojas Fechadas
            data_fechamento = obter_data_atual()
            observacao_final = (
                observacao if observacao else criar_observacao_padrao(numero_loja)
            )

            # Adiciona loja na aba Lojas Fechadas (inclui formatação específica)
            if not self.sheets_manager.adicionar_loja_fechada(
                nome_loja, numero_loja, data_fechamento, observacao_final
            ):
                return ResultadoFechamento(
                    sucesso=False,
                    mensagem=f"Erro ao adicionar loja {numero_loja} na aba Lojas Fechadas",
                )

            return ResultadoFechamento(
                sucesso=True,
                mensagem=f"Loja {numero_loja} ({nome_loja}) fechada com sucesso!",
                detalhes={
                    "numero_loja": numero_loja,
                    "nome_loja": nome_loja,
                    "linha_gerenciador": linha,
                    "data_fechamento": data_fechamento,
                    "observacao": observacao_final,
                },
            )

        except Exception as e:
            self.logger.error(f"Erro inesperado ao fechar loja {numero_loja}: {e}")
            return ResultadoFechamento(
                sucesso=False,
                mensagem=f"Erro inesperado ao fechar loja {numero_loja}: {e}",
            )

    def fechar_multiplas_lojas(
        self, numeros_lojas: list, observacao: Optional[str] = None
    ) -> Dict[str, ResultadoFechamento]:
        """
        Fecha múltiplas lojas.

        Args:
            numeros_lojas (list): Lista de números de lojas para fechar.
            observacao (Optional[str]): Observação personalizada.

        Returns:
            Dict[str, ResultadoFechamento]: Resultados indexados por número da loja.
        """
        resultados = {}

        for numero_loja in numeros_lojas:
            if not numero_loja or not numero_loja.strip():
                continue

            numero_limpo = numero_loja.strip()
            resultado = self.fechar_loja(numero_limpo, observacao)
            resultados[numero_limpo] = resultado

        return resultados

    def validar_conexao(self) -> bool:
        """
        Valida se a conexão está funcionando.

        Returns:
            bool: True se conexão válida, False caso contrário.
        """
        return self.sheets_manager.testar_conexao()
