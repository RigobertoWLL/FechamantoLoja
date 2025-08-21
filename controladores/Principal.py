import sys
import argparse
from typing import List, Optional

from configuracao.GerenciadorConfiguracao import GerenciadorConfiguracao
from servicos.GerenciadorLoja import GerenciadorLoja
from utilitarios.logger import configurar_logging
from utilitarios.Utilitarios import validar_numero_loja, listar_formatos_suportados


def imprimir_banner():
    print("=" * 60)
    print("🏪 SISTEMA DE FECHAMENTO DE LOJAS")
    print("   Integração com Google Sheets")
    print("   ✨ Suporte para códigos alfanuméricos (I05, T09, I01, etc.)")
    print("=" * 60)
    print()


def imprimir_formatos_suportados():
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
    logger = configurar_logging()

    print("📋 Validando configuração...")

    try:
        gerenciador_config = GerenciadorConfiguracao()
        if not gerenciador_config.validar_configuracao():
            print("❌ Configuração inválida!")
            print("\nPara configurar o sistema:")
            print("1. Verifique o arquivo config.json")
            print("2. Verifique o arquivo credentials.json")
            return False
    except Exception as e:
        print(f"❌ Erro ao validar configuração: {e}")
        return False

    print("✅ Configuração válida!")
    return True


def fechar_loja_unica(numero_loja: str, observacao: Optional[str] = None) -> bool:
    gerenciador = GerenciadorLoja()

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
    gerenciador = GerenciadorLoja()

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

    gerenciador = GerenciadorLoja()

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
    parser = argparse.ArgumentParser(
        description="Sistema de Fechamento de Lojas - Google Sheets (com informações completas)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:

Códigos numéricos:
    python main.py 123
    python main.py 456 "Fechamento por reforma"

Códigos alfanuméricos:
    python main.py I05
    python main.py T09 "Fechamento temporário"
    python main.py i01

Verificação (mostra Grupo, Nome, Status D e I):
    python main.py --verificar 789
    python main.py --verificar I05

Múltiplas lojas:
    python main.py --multiplas "123,456,789"
    python main.py --multiplas "I05,T09,I01"
    python main.py --multiplas "100,I05,T09" "Fechamento em lote"

Formatos:
    python main.py --formatos

Configuração:
    Configure config.json com suas preferências
    Configure credentials.json com suas credenciais Google Sheets
        """,
    )

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
    try:
        imprimir_banner()

        parser = criar_parser()
        args = parser.parse_args()

        nivel_log = "DEBUG" if args.debug else "INFO"
        configurar_logging(nivel_log)

        if args.formatos:
            imprimir_formatos_suportados()
            sys.exit(0)

        if not validar_configuracao():
            sys.exit(1)

        print()

        sucesso = False

        if args.verificar:
            sucesso = verificar_loja(args.verificar)

        elif args.multiplas:
            sucesso = fechar_multiplas_lojas(args.multiplas, args.observacao)

        elif args.numero_loja:
            sucesso = fechar_loja_unica(args.numero_loja, args.observacao)

        else:
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