#!/usr/bin/env python3
"""
Sistema de Fechamento de Lojas - Google Sheets
==============================================

ATUALIZADO: Exibe informações completas incluindo Grupo, Nome e Status
"""

import sys
import argparse
from typing import List, Optional

from ConfigManager import ConfigManager
from LojaManager import LojaManager
from Logger import configurar_logging
from Utils import validar_numero_loja, listar_formatos_suportados


def imprimir_banner():
    """Imprime o banner do sistema."""
    print("=" * 60)
    print("🏪 SISTEMA DE FECHAMENTO DE LOJAS")
    print("   Integração com Google Sheets")
    print("   ✨ Suporte para códigos alfanuméricos (I05, T09, I01, etc.)")
    print("=" * 60)
    print()


def imprimir_formatos_suportados():
    """Imprime informações sobre formatos de código suportados."""
    formatos = listar_formatos_suportados()

    print("📋 FORMATOS DE CÓDIGO SUPORTADOS:")
    print()
    print("🔢 Numéricos:")
    print(f"   {', '.join(formatos['numericos'])}")
    print()
    print("🔤 Alfanuméricos padrão:")
    print(f"   {', '.join(formatos['alfanumericos_padrao'])}")
    print()
    print("🔀 Variações aceitas (normalizadas automaticamente):")
    for original, normalizado in formatos["variacao_aceita"].items():
        print(f"   {original} → {normalizado}")
    print()


def validar_configuracao() -> bool:
    """
    Valida se todas as configurações necessárias estão definidas.

    Returns:
        bool: True se configuração válida, False caso contrário.
    """
    logger = configurar_logging()

    print("📋 Validando configuração...")

    try:
        config_manager = ConfigManager()
        if not config_manager.validar_configuracao():
            print("❌ Configuração inválida!")
            print("\nPara configurar o sistema:")
            print("1. Verifique o arquivo Config.json")
            print("2. Verifique o arquivo Credentials.json")
            return False
    except Exception as e:
        print(f"❌ Erro ao validar configuração: {e}")
        return False

    print("✅ Configuração válida!")
    return True


def fechar_loja_unica(numero_loja: str, observacao: Optional[str] = None) -> bool:
    """
    Fecha uma única loja.

    Args:
        numero_loja (str): Número da loja para fechar.
        observacao (Optional[str]): Observação personalizada.

    Returns:
        bool: True se fechada com sucesso, False caso contrário.
    """
    gerenciador = LojaManager()

    try:
        print(f"🔌 Conectando ao Google Sheets...")
        if not gerenciador.conectar():
            print("❌ Falha ao conectar com Google Sheets")
            return False

        print("✅ Conectado com sucesso!")
        print()

        print(f"📍 Processando loja: {numero_loja}")

        resultado = gerenciador.fechar_loja(numero_loja, observacao)

        if resultado.sucesso:
            print(f"✅ {resultado.mensagem}")
            if resultado.detalhes:
                print(f"   📅 Data: {resultado.detalhes['data_fechamento']}")
                print(f"   📝 Observação: {resultado.detalhes['observacao']}")
            return True
        else:
            print(f"❌ {resultado.mensagem}")
            return False

    except KeyboardInterrupt:
        print("\n⚠️  Operação cancelada pelo usuário")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False
    finally:
        gerenciador.desconectar()


def verificar_loja(numero_loja: str) -> bool:
    """
    ATUALIZADO: Verifica se uma loja existe e mostra informações completas.

    Args:
        numero_loja (str): Número da loja para verificar.

    Returns:
        bool: True se encontrada, False caso contrário.
    """
    gerenciador = LojaManager()

    try:
        print(f"🔌 Conectando ao Google Sheets...")
        if not gerenciador.conectar():
            print("❌ Falha ao conectar com Google Sheets")
            return False

        print("✅ Conectado com sucesso!")
        print()

        print(f"🔍 Verificando loja: {numero_loja}")

        info = gerenciador.obter_informacoes_loja(numero_loja)

        if info:
            print(f"✅ Loja encontrada!")
            print(f"   🏪 Nome: {info['nome_loja']}")
            print(f"   📍 Número: {info['numero_loja']}")
            print(f"   👥 Grupo: {info['grupo']}")
            print(f"   📊 Status D: {info['status_d']}")
            print(f"   📊 Status I: {info['status_i']}")
            print(f"   📍 Linha: {info['linha_gerenciador']}")
            return True
        else:
            print(f"❌ Loja {numero_loja} não encontrada na aba Gerenciador")
            return False

    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False
    finally:
        gerenciador.desconectar()


def fechar_multiplas_lojas(
    numeros_lojas_str: str, observacao: Optional[str] = None
) -> bool:
    """
    Fecha múltiplas lojas.

    Args:
        numeros_lojas_str (str): String com números das lojas separados por vírgula.
        observacao (Optional[str]): Observação personalizada.

    Returns:
        bool: True se pelo menos uma loja foi fechada, False caso contrário.
    """
    # Parse dos números das lojas
    try:
        numeros_lojas = [
            loja.strip() for loja in numeros_lojas_str.split(",") if loja.strip()
        ]
        if not numeros_lojas:
            print("❌ Nenhum número de loja válido fornecido")
            return False
    except Exception as e:
        print(f"❌ Erro ao processar lista de lojas: {e}")
        return False

    gerenciador = LojaManager()

    try:
        print(f"🔌 Conectando ao Google Sheets...")
        if not gerenciador.conectar():
            print("❌ Falha ao conectar com Google Sheets")
            return False

        print("✅ Conectado com sucesso!")
        print()

        print(f"📋 Processando {len(numeros_lojas)} lojas...")
        print()

        resultados = gerenciador.fechar_multiplas_lojas(numeros_lojas, observacao)

        # Exibe resultados
        sucessos = 0
        for numero_loja, resultado in resultados.items():
            if resultado.sucesso:
                print(f"✅ Loja {numero_loja}: {resultado.mensagem}")
                sucessos += 1
            else:
                print(f"❌ Loja {numero_loja}: {resultado.mensagem}")

        print()
        print(f"📊 Resumo: {sucessos}/{len(resultados)} lojas fechadas com sucesso")

        return sucessos > 0

    except KeyboardInterrupt:
        print("\n⚠️  Operação cancelada pelo usuário")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False
    finally:
        gerenciador.desconectar()


def criar_parser() -> argparse.ArgumentParser:
    """
    Cria o parser de argumentos da linha de comando.

    Returns:
        argparse.ArgumentParser: Parser configurado.
    """
    parser = argparse.ArgumentParser(
        description="Sistema de Fechamento de Lojas - Google Sheets (com informações completas)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:

Códigos numéricos:
    python Main.py 123
    python Main.py 456 "Fechamento por reforma"

Códigos alfanuméricos:
    python Main.py I05
    python Main.py T09 "Fechamento temporário"
    python Main.py i01  # Normalizado automaticamente para I01

Verificação (mostra Grupo, Nome, Status D e I):
    python Main.py --verificar 789
    python Main.py --verificar I05

Múltiplas lojas:
    python Main.py --multiplas "123,456,789"
    python Main.py --multiplas "I05,T09,I01"
    python Main.py --multiplas "100,I05,T09" "Fechamento em lote"

Formatos:
    python Main.py --formatos  # Mostra formatos suportados

Configuração:
    Configure Config.json com suas preferências
    Configure Credentials.json com suas credenciais Google Sheets
        """,
    )

    # Grupo mutuamente exclusivo para operações principais
    grupo_operacao = parser.add_mutually_exclusive_group(required=True)

    grupo_operacao.add_argument(
        "numero_loja", nargs="?", help="Número da loja para fechar (ex: 123, I05, T09)"
    )

    grupo_operacao.add_argument(
        "--verificar",
        metavar="NUMERO_LOJA",
        help="Verifica uma loja e mostra informações completas (ex: --verificar I05)",
    )

    grupo_operacao.add_argument(
        "--multiplas",
        metavar="LISTA_LOJAS",
        help='Fecha múltiplas lojas (números separados por vírgula, ex: "123,I05,T09")',
    )

    grupo_operacao.add_argument(
        "--formatos",
        action="store_true",
        help="Mostra os formatos de código de loja suportados",
    )

    parser.add_argument(
        "observacao", nargs="?", help="Observação personalizada para o fechamento"
    )

    parser.add_argument(
        "--debug", action="store_true", help="Ativa modo debug com logs detalhados"
    )

    return parser


def main():
    """Função principal do sistema."""
    try:
        # Banner
        imprimir_banner()

        # Parse dos argumentos
        parser = criar_parser()
        args = parser.parse_args()

        # Configuração de logging
        nivel_log = "DEBUG" if args.debug else "INFO"
        configurar_logging(nivel_log)

        # Se solicitados formatos, mostra e sai
        if args.formatos:
            imprimir_formatos_suportados()
            sys.exit(0)

        # Validação da configuração
        if not validar_configuracao():
            sys.exit(1)

        print()

        # Execução baseada nos argumentos
        sucesso = False

        if args.verificar:
            # Modo verificação
            sucesso = verificar_loja(args.verificar)

        elif args.multiplas:
            # Modo múltiplas lojas
            sucesso = fechar_multiplas_lojas(args.multiplas, args.observacao)

        elif args.numero_loja:
            # Modo loja única
            sucesso = fechar_loja_unica(args.numero_loja, args.observacao)

        else:
            # Não deveria chegar aqui devido ao mutually_exclusive_group
            parser.print_help()
            sys.exit(1)

        print()
        if sucesso:
            print("🎉 Operação concluída com sucesso!")
            sys.exit(0)
        else:
            print("⚠️  Operação concluída com erros!")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⚠️  Programa interrompido pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro crítico: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
