from typing import Optional, Dict, Any
from modelos.resultado_fechamento import ResultadoFechamento
from .gerenciador_planilhas_google import GerenciadorPlanilhasGoogle
from utilitarios.logger import MixinLogger, log_operacao
from utilitarios.utilitarios import (
    validar_numero_loja,
    validar_nome_loja,
    obter_data_atual,
    criar_observacao_padrao,
    formatar_lista_lojas,
)


class GerenciadorLoja(MixinLogger):

    def __init__(self):
        self.gerenciador_planilhas = GerenciadorPlanilhasGoogle()

    def conectar(self) -> bool:
        return self.gerenciador_planilhas.conectar()

    def desconectar(self):
        self.gerenciador_planilhas.desconectar()
        self.logger.info("Gerenciador de lojas desconectado")

    def obter_informacoes_loja(self, numero_loja: str) -> Optional[Dict[str, Any]]:
        try:
            if not validar_numero_loja(numero_loja):
                self.logger.warning(f"Número de loja inválido: {numero_loja}")
                return None

            info = self.gerenciador_planilhas.obter_informacoes_completas_loja(numero_loja)

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
        try:
            if not validar_numero_loja(numero_loja):
                return ResultadoFechamento(
                    sucesso=False, mensagem=f"Número de loja inválido: {numero_loja}"
                )

            linha = self.gerenciador_planilhas.buscar_numero_loja_na_aba_gerenciador(
                numero_loja
            )
            if linha is None:
                return ResultadoFechamento(
                    sucesso=False,
                    mensagem=f"Loja {numero_loja} não encontrada na aba Gerenciador",
                )

            nome_loja = self.gerenciador_planilhas.obter_nome_loja_por_numero(numero_loja)
            if not nome_loja:
                nome_loja = f"Loja {numero_loja}"

            if not self.gerenciador_planilhas.atualizar_status_loja_gerenciador(linha):
                return ResultadoFechamento(
                    sucesso=False,
                    mensagem=f"Erro ao atualizar status da loja {numero_loja}",
                )

            data_fechamento = obter_data_atual()
            observacao_final = (
                observacao if observacao else criar_observacao_padrao(numero_loja)
            )

            if not self.gerenciador_planilhas.adicionar_loja_fechada(
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
        resultados = {}

        for numero_loja in numeros_lojas:
            if not numero_loja or not numero_loja.strip():
                continue

            numero_limpo = numero_loja.strip()
            resultado = self.fechar_loja(numero_limpo, observacao)
            resultados[numero_limpo] = resultado

        return resultados

    def validar_conexao(self) -> bool:
        return self.gerenciador_planilhas.testar_conexao()