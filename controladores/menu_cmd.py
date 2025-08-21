from servicos.gerenciador_loja import GerenciadorLoja
from servicos.gerenciador_firebird import GerenciadorFirebird
from utilitarios.logger import configurar_logging


def imprimir_banner():
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
    configurar_logging()

    imprimir_banner()

    gerenciador_loja = GerenciadorLoja()
    gerenciador_firebird = GerenciadorFirebird()

    while True:
        menu()
        escolha = input("Escolha a opção desejada: ").strip()

        if escolha == "1":
            print("\n🏪 FECHAMENTO DE LOJA (SHEETS)")
            numero_loja = input("Digite o número da loja: ").strip()
            if not numero_loja:
                print("❌ Número da loja é obrigatório!")
                continue

            observacao = input("Observação (opcional): ").strip()
            
            try:
                if gerenciador_loja.conectar():
                    resultado = gerenciador_loja.fechar_loja(
                        numero_loja, observacao if observacao else None
                    )
                    if resultado.sucesso:
                        print(f"✅ {resultado.mensagem}")
                    else:
                        print(f"❌ {resultado.mensagem}")
                else:
                    print("❌ Erro ao conectar no Google Sheets")
            except Exception as e:
                print(f"❌ Erro inesperado: {e}")
            finally:
                gerenciador_loja.desconectar()

        elif escolha == "2":
            print("\n🔥 ATUALIZAR STATUS LOJA (FIREBIRD)")
            codigo_loja = input("Digite o código da loja: ").strip()
            if not codigo_loja:
                print("❌ Código da loja é obrigatório!")
                continue

            status_input = input("Status (padrão 3 = fechada): ").strip()
            status = 3
            if status_input:
                try:
                    status = int(status_input)
                except ValueError:
                    print("❌ Status deve ser um número!")
                    continue

            try:
                if gerenciador_firebird.conectar():
                    if gerenciador_firebird.atualizar_status_loja(codigo_loja, status):
                        print(f"✅ Status da loja {codigo_loja} atualizado para {status}")
                    else:
                        print(f"❌ Erro ao atualizar status da loja {codigo_loja}")
                else:
                    print("❌ Erro ao conectar no Firebird")
            except Exception as e:
                print(f"❌ Erro inesperado: {e}")
            finally:
                gerenciador_firebird.desconectar()

        elif escolha == "3":
            print("\n📊 VERIFICAR LOJA (SHEETS)")
            numero_loja = input("Digite o número da loja: ").strip()
            if not numero_loja:
                print("❌ Número da loja é obrigatório!")
                continue

            try:
                if gerenciador_loja.conectar():
                    info = gerenciador_loja.obter_informacoes_loja(numero_loja)
                    if info:
                        print(f"✅ Loja encontrada!")
                        print(f"   🏪 Nome: {info['nome_loja']}")
                        print(f"   📍 Número: {info['numero_loja']}")
                        print(f"   👥 Grupo: {info['grupo']}")
                        print(f"   📊 Status D: {info['status_d']}")
                        print(f"   📊 Status I: {info['status_i']}")
                        print(f"   📍 Linha: {info['linha_gerenciador']}")
                    else:
                        print(f"❌ Loja {numero_loja} não encontrada")
                else:
                    print("❌ Erro ao conectar no Google Sheets")
            except Exception as e:
                print(f"❌ Erro inesperado: {e}")
            finally:
                gerenciador_loja.desconectar()

        elif escolha == "4":
            print("\n🔥 VERIFICAR STATUS LOJA (FIREBIRD)")
            codigo_loja = input("Digite o código da loja: ").strip()
            if not codigo_loja:
                print("❌ Código da loja é obrigatório!")
                continue

            try:
                if gerenciador_firebird.conectar():
                    status = gerenciador_firebird.verificar_status_loja(codigo_loja)
                    if status is not None:
                        print(f"✅ Loja {codigo_loja} tem status: {status}")
                    else:
                        print(f"❌ Loja {codigo_loja} não encontrada")
                else:
                    print("❌ Erro ao conectar no Firebird")
            except Exception as e:
                print(f"❌ Erro inesperado: {e}")
            finally:
                gerenciador_firebird.desconectar()

        elif escolha == "5":
            print("\n📋 LISTAR LOJAS POR STATUS (FIREBIRD)")
            status_input = input("Digite o status (ex: 1, 2, 3): ").strip()
            if not status_input:
                print("❌ Status é obrigatório!")
                continue

            try:
                status = int(status_input)
            except ValueError:
                print("❌ Status deve ser um número!")
                continue

            try:
                if gerenciador_firebird.conectar():
                    lojas = gerenciador_firebird.listar_lojas_por_status(status)
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
                gerenciador_firebird.desconectar()

        elif escolha == "6":
            print("\n🔍 VERIFICAÇÃO ESTRUTURA TABELA")
            try:
                if gerenciador_firebird.conectar():
                    if gerenciador_firebird.verificar_estrutura_tabela():
                        print("✅ Estrutura da tabela TB_LOJA está correta")
                    else:
                        print("❌ Problemas encontrados na estrutura da tabela")
                else:
                    print("❌ Erro ao conectar no Firebird")
            except Exception as e:
                print(f"❌ Erro inesperado: {e}")
            finally:
                gerenciador_firebird.desconectar()

        elif escolha == "7":
            print("\n📊 ESTATÍSTICAS DA TABELA")
            try:
                if gerenciador_firebird.conectar():
                    stats = gerenciador_firebird.obter_estatisticas_tabela()
                    if stats:
                        print("✅ Estatísticas da tabela TB_LOJA:")
                        print(f"   📊 Total de lojas: {stats['total_lojas']}")
                        print(f"   📋 Lojas por status:")
                        for status, count in stats["por_status"].items():
                            print(f"      Status {status}: {count} lojas")
                    else:
                        print("❌ Erro ao obter estatísticas")
                else:
                    print("❌ Erro ao conectar no Firebird")
            except Exception as e:
                print(f"❌ Erro inesperado: {e}")
            finally:
                gerenciador_firebird.desconectar()

        elif escolha == "8":
            print("\n🔌 TESTE DE CONEXÕES")

            print("📊 Testando Google Sheets...")
            try:
                if gerenciador_loja.conectar():
                    if gerenciador_loja.validar_conexao():
                        print("   ✅ Google Sheets conectado com sucesso")
                    else:
                        print("   ❌ Erro na validação do Google Sheets")
                else:
                    print("   ❌ Erro ao conectar no Google Sheets")
            except Exception as e:
                print(f"   ❌ Erro inesperado: {e}")
            finally:
                gerenciador_loja.desconectar()

            print("🔥 Testando Firebird...")
            try:
                if gerenciador_firebird.conectar():
                    if gerenciador_firebird.testar_conexao():
                        print("   ✅ Firebird conectado com sucesso")
                    else:
                        print("   ❌ Erro na validação do Firebird")
                else:
                    print("   ❌ Erro ao conectar no Firebird")
            except Exception as e:
                print(f"   ❌ Erro inesperado: {e}")
            finally:
                gerenciador_firebird.desconectar()

        elif escolha == "9":
            print("\n👋 Saindo do sistema. Até mais!")
            break

        else:
            print("❌ Opção inválida! Tente novamente.")

        input("\nPressione Enter para continuar...")


if __name__ == "__main__":
    main()