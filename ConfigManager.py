"""
Módulo para gerenciar configurações do sistema de fechamento de lojas.
ATUALIZADO: Inclui configurações do Firebird.
"""

import json
import os
from typing import Dict, Any
from Logger import configurar_logging


class ConfigManager:
    """Classe para gerenciar configurações do sistema."""

    def __init__(self, arquivo_config: str = "Config.json"):
        """
        Inicializa o gerenciador de configurações.

        Args:
            arquivo_config (str): Caminho para o arquivo de configuração.
        """
        self.logger = configurar_logging()
        self.arquivo_config = arquivo_config
        self.config = {}
        self._carregar_configuracao()

    def _carregar_configuracao(self):
        """Carrega as configurações do arquivo JSON."""
        try:
            if not os.path.exists(self.arquivo_config):
                raise FileNotFoundError(
                    f"Arquivo de configuração não encontrado: {self.arquivo_config}"
                )

            with open(self.arquivo_config, "r", encoding="utf-8") as f:
                self.config = json.load(f)

            self.logger.info("Configurações carregadas com sucesso")

        except FileNotFoundError as e:
            self.logger.error(f"Arquivo de configuração não encontrado: {e}")
            raise
        except json.JSONDecodeError as e:
            self.logger.error(
                f"Erro ao decodificar JSON do arquivo de configuração: {e}"
            )
            raise
        except Exception as e:
            self.logger.error(f"Erro inesperado ao carregar configuração: {e}")
            raise

    def validar_configuracao(self) -> bool:
        """
        Valida se as configurações estão corretas.

        Returns:
            bool: True se a configuração está válida, False caso contrário.
        """
        try:
            # Verifica campos obrigatórios
            campos_obrigatorios = [
                "planilha_id",
                "arquivo_credenciais",
                "aba_gerenciador",
                "aba_lojas_fechadas",
            ]

            for campo in campos_obrigatorios:
                if campo not in self.config or not self.config[campo]:
                    self.logger.error(
                        f"Campo obrigatório não encontrado ou vazio: {campo}"
                    )
                    return False

            # Verifica se arquivo de credenciais existe
            arquivo_credenciais = self.config["arquivo_credenciais"]
            if not os.path.exists(arquivo_credenciais):
                self.logger.error(
                    f"Arquivo de credenciais não encontrado: {arquivo_credenciais}"
                )
                return False

            # Valida configurações numéricas
            if "configuracoes_gerenciador" in self.config:
                linha_inicio = self.config["configuracoes_gerenciador"].get(
                    "linha_inicio"
                )
                if linha_inicio is not None and not isinstance(linha_inicio, int):
                    self.logger.error(
                        f"linha_inicio deve ser um número inteiro, recebido: {type(linha_inicio)}"
                    )
                    return False

            self.logger.info("Configuração válida")
            return True

        except Exception as e:
            self.logger.error(f"Erro ao validar configuração: {e}")
            return False

    # Propriedades Google Sheets (existentes)
    @property
    def planilha_id(self) -> str:
        """ID da planilha Google Sheets."""
        return self.config.get("planilha_id", "")

    @property
    def arquivo_credenciais(self) -> str:
        """Caminho para o arquivo de credenciais."""
        return self.config.get("arquivo_credenciais", "Credentials.json")

    @property
    def aba_gerenciador(self) -> str:
        """Nome da aba Gerenciador."""
        return self.config.get("aba_gerenciador", "Gerenciador")

    @property
    def aba_lojas_fechadas(self) -> str:
        """Nome da aba Lojas Fechadas."""
        return self.config.get("aba_lojas_fechadas", "Lojas Fechadas")

    @property
    def coluna_numero_loja_gerenciador(self) -> str:
        """Coluna do número da loja na aba Gerenciador."""
        return self.config.get("configuracoes_gerenciador", {}).get(
            "coluna_numero_loja", "C"
        )

    @property
    def coluna_status_gerenciador(self) -> str:
        """Coluna do status na aba Gerenciador."""
        return self.config.get("configuracoes_gerenciador", {}).get(
            "coluna_status", "D"
        )

    @property
    def colunas_limpar_gerenciador(self) -> list:
        """Colunas a limpar na aba Gerenciador."""
        return self.config.get("configuracoes_gerenciador", {}).get(
            "colunas_limpar", ["K"]
        )

    @property
    def linha_inicio_gerenciador(self) -> int:
        """Linha de início dos dados na aba Gerenciador."""
        valor = self.config.get("configuracoes_gerenciador", {}).get("linha_inicio", 6)
        # Garantir que seja sempre um inteiro para evitar erro de comparação
        if isinstance(valor, str):
            try:
                return int(valor)
            except ValueError:
                self.logger.warning(
                    f"linha_inicio não é um número válido: {valor}, usando 6"
                )
                return 6
        return int(valor) if valor is not None else 6

    @property
    def coluna_nome_loja_fechadas(self) -> str:
        """Coluna do nome da loja na aba Lojas Fechadas."""
        return self.config.get("configuracoes_lojas_fechadas", {}).get(
            "coluna_nome_loja", "B"
        )

    @property
    def coluna_numero_loja_fechadas(self) -> str:
        """Coluna do número da loja na aba Lojas Fechadas."""
        return self.config.get("configuracoes_lojas_fechadas", {}).get(
            "coluna_numero_loja", "C"
        )

    @property
    def coluna_status_fechadas(self) -> str:
        """Coluna do status na aba Lojas Fechadas."""
        return self.config.get("configuracoes_lojas_fechadas", {}).get(
            "coluna_status", "D"
        )

    @property
    def coluna_data_fechamento(self) -> str:
        """Coluna da data de fechamento na aba Lojas Fechadas."""
        return self.config.get("configuracoes_lojas_fechadas", {}).get(
            "coluna_data_fechamento", "E"
        )

    @property
    def coluna_observacao(self) -> str:
        """Coluna da observação na aba Lojas Fechadas."""
        return self.config.get("configuracoes_lojas_fechadas", {}).get(
            "coluna_observacao", "F"
        )

    @property
    def status_fechada(self) -> str:
        """Valor do status para loja fechada."""
        return self.config.get("valores_padrao", {}).get("status_fechada", "Fechada")

    @property
    def valor_padrao_status_fechadas(self) -> str:
        """Valor padrão do status na aba Lojas Fechadas."""
        return self.config.get("valores_padrao", {}).get(
            "status_padrao_lojas_fechadas", "NÃO"
        )

    # NOVAS: Propriedades Firebird
    @property
    def firebird_host(self) -> str:
        """Host do banco Firebird."""
        return self.config.get("configuracoes_firebird", {}).get("host", "localhost")

    @property
    def firebird_database(self) -> str:
        """Nome do banco Firebird."""
        return self.config.get("configuracoes_firebird", {}).get("database", "CCL_786")

    @property
    def firebird_port(self) -> int:
        """Porta do banco Firebird."""
        return self.config.get("configuracoes_firebird", {}).get("port", 3050)

    @property
    def firebird_user(self) -> str:
        """Usuário do banco Firebird."""
        return self.config.get("configuracoes_firebird", {}).get("user", "SYSDBA")

    @property
    def firebird_password(self) -> str:
        """Senha do banco Firebird."""
        return self.config.get("configuracoes_firebird", {}).get(
            "password", "masterkey"
        )

    @property
    def firebird_charset(self) -> str:
        """Charset do banco Firebird."""
        return self.config.get("configuracoes_firebird", {}).get("charset", "UTF8")

    @property
    def firebird_tabela_loja(self) -> str:
        """Nome da tabela de lojas no Firebird."""
        return self.config.get("configuracoes_firebird", {}).get(
            "tabela_loja", "TB_LOJA"
        )

    @property
    def firebird_coluna_codigo(self) -> str:
        """Nome da coluna de código da loja no Firebird."""
        return self.config.get("configuracoes_firebird", {}).get(
            "coluna_codigo", "CODLOJA"
        )

    @property
    def firebird_coluna_status(self) -> str:
        """Nome da coluna de status no Firebird."""
        return self.config.get("configuracoes_firebird", {}).get(
            "coluna_status", "ID_STATUS"
        )

    @property
    def firebird_status_fechada(self) -> int:
        """Valor do status para loja fechada no Firebird."""
        return self.config.get("configuracoes_firebird", {}).get("status_fechada", 3)

    def obter_configuracao_completa(self) -> Dict[str, Any]:
        """
        Retorna um dicionário com todas as configurações.

        Returns:
            Dict[str, Any]: Dicionário com todas as configurações.
        """
        return self.config.copy()

    def atualizar_configuracao(self, novas_configs: Dict[str, Any]) -> bool:
        """
        Atualiza configurações em memória e salva no arquivo.

        Args:
            novas_configs (Dict[str, Any]): Novas configurações para aplicar.

        Returns:
            bool: True se atualizado com sucesso, False caso contrário.
        """
        try:
            # Atualiza configurações em memória
            self.config.update(novas_configs)

            # Salva no arquivo
            with open(self.arquivo_config, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)

            self.logger.info("Configurações atualizadas com sucesso")
            return True

        except Exception as e:
            self.logger.error(f"Erro ao atualizar configurações: {e}")
            return False
