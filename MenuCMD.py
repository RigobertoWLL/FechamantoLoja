"""
Menu de operações via CMD para o Sistema de Fechamento de Lojas.
CORRIGIDO: Melhor tratamento de erros e opções de debug.
"""

from manager.LojaManager import LojaManager
from manager.FirebirdManager import FirebirdManager
from logger.Logger import configurar_logging


def imprimir_banner():
    """Imprime o banner do sistema."""
    print("=" * 60)
    print("🏪 SISTEMA DE FECHAMENTO DE LOJAS - MENU INTERATIVO")
    print("   📊 Google Sheets + 🔥 Firebird 5.0")
    print("=" * 60)
    print()


def menu():
    print("\n========== MENU DE OPERAÇÕES ==========")
    print("1 - Fechar loja (Sheets + formatação)")
    print("2 - Atualizar status da loja no Firebird")
    print("3 - Verificar loja (Sheets)")
    print("4 - Verificar status loja (Firebird)")
    print("5 - Listar lojas do Firebird por status")
    print("6 - Verificar estrutura tabela TB_LOJA")
    print("7 - Estatísticas da tabela TB_LOJA")
    print("8 - Testar conexões")
    print("9 - Sair")
    print("========================================\n")


def main():
    # Configurar logging
    configurar_logging()

    imprimir_banner()

    loja_manager = LojaManager()
    firebird_manager = FirebirdManager()

    while True:
        menu()
        escolha = input("Escolha a opção desejada: ").strip()

        if escolha == "1":
            print("\n🏪 FECHAMENTO DE LOJA (SHEETS)")
            numero_loja = input("Digite o número da loja: ").strip()
            if not numero_loja:
                print("❌ Número da loja não pode estar vazio!")
                continue

            obs = input("Observação (opcional): ").strip()

            try:
                if loja_manager.conectar():
                    resultado = loja_manager.fechar_loja(
                        numero_loja, obs if obs else None
                    )
                    if resultado.sucesso:
                        print(f"✅ {resultado.mensagem}")
                        if resultado.detalhes:
                            print(
                                f"   📅 Data: {resultado.detalhes['data_fechamento']}"
                            )
                            print(
                                f"   📝 Observação: {resultado.detalhes['observacao']}"
                            )
                    else:
                        print(f"❌ {resultado.mensagem}")
                else:
                    print("❌ Erro ao conectar no Google Sheets")
            except Exception as e:
                print(f"❌ Erro inesperado: {e}")
            finally:
                loja_manager.desconectar()

        elif escolha == "2":
            print("\n🔥 ATUALIZAÇÃO STATUS FIREBIRD")
            codigo_loja = input("Digite o número da loja: ").strip()
            if not codigo_loja:
                print("❌ Código da loja não pode estar vazio!")
                continue

            status = input("Status (padrão 3): ").strip()
            status = int(status) if status.isdigit() else 3

            try:
                if firebird_manager.conectar():
                    if firebird_manager.atualizar_status_loja(codigo_loja, status):
                        print(
                            f"✅ Loja {codigo_loja} atualizada para ID_STATUS={status}"
                        )
                    else:
                        print(f"❌ Erro ao atualizar loja {codigo_loja}")
                else:
                    print("❌ Erro ao conectar no Firebird")
            except Exception as e:
                print(f"❌ Erro inesperado: {e}")
            finally:
                firebird_manager.desconectar()

        elif escolha == "3":
            print("\n📊 VERIFICAÇÃO LOJA (SHEETS)")
            numero_loja = input("Digite o número da loja para verificar: ").strip()
            if not numero_loja:
                print("❌ Número da loja não pode estar vazio!")
                continue

            try:
                if loja_manager.conectar():
                    info = loja_manager.obter_informacoes_loja(numero_loja)
                    if info:
                        print("✅ Loja encontrada:")
                        print(f"   🏪 Nome: {info['nome_loja']}")
                        print(f"   📍 Número: {info['numero_loja']}")
                        print(f"   👥 Grupo: {info['grupo']}")
                        print(f"   📊 Status D: {info['status_d']}")
                        print(f"   📊 Status I: {info['status_i']}")
                        print(f"   📍 Linha: {info['linha_gerenciador']}")
                    else:
                        print("❌ Loja não encontrada")
                else:
                    print("❌ Erro ao conectar no Google Sheets")
            except Exception as e:
                print(f"❌ Erro inesperado: {e}")
            finally:
                loja_manager.desconectar()

        elif escolha == "4":
            print("\n🔥 VERIFICAÇÃO STATUS (FIREBIRD)")
            codigo_loja = input("Digite o número da loja: ").strip()
            if not codigo_loja:
                print("❌ Código da loja não pode estar vazio!")
                continue

            try:
                if firebird_manager.conectar():
                    loja_info = firebird_manager.buscar_loja_por_codigo(codigo_loja)
                    if loja_info:
                        print("✅ Loja encontrada:")
                        print(f"   🔢 Código: {loja_info['codigo_loja']}")
                        print(f"   📊 Status: {loja_info['id_status']}")
                        print(f"   🏪 Nome: {loja_info.get('nome', 'N/A')}")
                    else:
                        print("❌ Loja não encontrada")
                else:
                    print("❌ Erro ao conectar no Firebird")
            except Exception as e:
                print(f"❌ Erro inesperado: {e}")
            finally:
                firebird_manager.desconectar()

        elif escolha == "5":
            print("\n📋 LISTAR LOJAS POR STATUS")
            status_input = input("Digite o status (número): ").strip()
            if not status_input.isdigit():
                print("❌ Status deve ser um número!")
                continue

            status = int(status_input)

            try:
                if firebird_manager.conectar():
                    lojas = firebird_manager.listar_lojas_por_status(status)
                    if lojas:
                        print(f"✅ Encontradas {len(lojas)} lojas com status {status}:")
                        for i, loja in enumerate(lojas, 1):
                            print(
                                f"   {i:3d}. {loja['codigo_loja']} (Status: {loja['id_status']})"
                            )
                    else:
                        print(f"❌ Nenhuma loja encontrada com status {status}")
                else:
                    print("❌ Erro ao conectar no Firebird")
            except Exception as e:
                print(f"❌ Erro inesperado: {e}")
            finally:
                firebird_manager.desconectar()

        elif escolha == "6":
            print("\n🔍 VERIFICAÇÃO ESTRUTURA TABELA")
            try:
                if firebird_manager.conectar():
                    if firebird_manager.verificar_estrutura_tabela():
                        print("✅ Estrutura da tabela TB_LOJA está correta")
                    else:
                        print("❌ Problemas na estrutura da tabela TB_LOJA")
                else:
                    print("❌ Erro ao conectar no Firebird")
            except Exception as e:
                print(f"❌ Erro inesperado: {e}")
            finally:
                firebird_manager.desconectar()

        elif escolha == "7":
            print("\n📈 ESTATÍSTICAS DA TABELA")
            try:
                if firebird_manager.conectar():
                    stats = firebird_manager.obter_estatisticas_tabela()
                    if stats:
                        print("✅ Estatísticas da tabela TB_LOJA:")
                        print(f"   📊 Total de lojas: {stats['total_lojas']}")
                        print(f"   📅 Timestamp: {stats['timestamp']}")
                        print(f"   📋 Lojas por status:")
                        for status, count in stats["lojas_por_status"].items():
                            print(f"      Status {status}: {count} lojas")
                    else:
                        print("❌ Erro ao obter estatísticas")
                else:
                    print("❌ Erro ao conectar no Firebird")
            except Exception as e:
                print(f"❌ Erro inesperado: {e}")
            finally:
                firebird_manager.desconectar()

        elif escolha == "8":
            print("\n🔌 TESTE DE CONEXÕES")

            # Teste Google Sheets
            print("📊 Testando Google Sheets...")
            try:
                if loja_manager.conectar():
                    if loja_manager.validar_conexao():
                        print("   ✅ Google Sheets conectado com sucesso")
                    else:
                        print("   ❌ Erro na validação do Google Sheets")
                else:
                    print("   ❌ Erro ao conectar no Google Sheets")
            except Exception as e:
                print(f"   ❌ Erro inesperado: {e}")
            finally:
                loja_manager.desconectar()

            # Teste Firebird
            print("🔥 Testando Firebird...")
            try:
                if firebird_manager.conectar():
                    if firebird_manager.testar_conexao():
                        print("   ✅ Firebird conectado com sucesso")
                    else:
                        print("   ❌ Erro na validação do Firebird")
                else:
                    print("   ❌ Erro ao conectar no Firebird")
            except Exception as e:
                print(f"   ❌ Erro inesperado: {e}")
            finally:
                firebird_manager.desconectar()

        elif escolha == "9":
            print("\n👋 Saindo do sistema. Até mais!")
            break

        else:
            print("❌ Opção inválida! Tente novamente.")

        # Pausa antes de mostrar menu novamente
        input("\nPressione Enter para continuar...")


if __name__ == "__main__":
    main()
