# Importa a biblioteca Flet (interface gráfica)
import flet as ft
# Importa a biblioteca para manipular JSON
import json
# Biblioteca para manipular arquivos e diretórios
import os
# Para pegar o mês atual e datas
from datetime import datetime

# Pasta onde os arquivos JSON ficarão armazenados
DATA_DIR = "data"

# Cria a pasta "data" caso ela não exista
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)


# Função que retorna o caminho do arquivo JSON de um mês específico
def caminho_arquivo(mes):
    return os.path.join(DATA_DIR, f"gastos_{mes}.json")


# Função para carregar os dados de um mês
def carregar_gastos(mes):
    arquivo = caminho_arquivo(mes)
    # Se o arquivo existir, abre e retorna o conteúdo JSON
    if os.path.exists(arquivo):
        with open(arquivo, "r", encoding="utf-8") as f:
            return json.load(f)
    # Se não existir, retorna estrutura padrão
    return {"salario": 0, "limite": 0, "gastos": []}


# Função para salvar os gastos no JSON
def salvar_gastos(mes, dados):
    with open(caminho_arquivo(mes), "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


# Função principal do app Flet
def main(page: ft.Page):

    # Configurações da janela
    page.title = "💸 Controle de gastos mensal"
    page.theme_mode = "light"
    page.window_width = 550
    page.window_height = 750
    page.padding = 20
    page.scroll = "adaptive"
    page.horizontal_alignment = "center"
    page.vertical_alignment = "center"

    # Cores personalizadas
    rosa = "#ffb6c1"
    cinza = "#f8f8f8"

    # Lista dos meses do ano
    meses = [
        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
    ]

    # Descobre o mês atual baseado no sistema operacional
    mes_atual = meses[datetime.now().month - 1]
    dados = carregar_gastos(mes_atual)

    # Campos de entrada
    salario_input = ft.TextField(label="Salário mensal (R$)", width=200)
    limite_input = ft.TextField(label="Limite mensal (R$)", width=200)
    gasto_nome = ft.TextField(label="Nome do gasto", width=200)
    gasto_valor = ft.TextField(label="Valor (R$)", width=100)

    # Área onde a tabela de gastos ficará
    tabela = ft.Column(scroll="auto", expand=True)

    # Textos de resumo
    total_gasto_txt = ft.Text(size=16, weight="bold")
    saldo_restante_txt = ft.Text(size=16, weight="bold", color="green")
    titulo_mes = ft.Text(f"Mês atual: {mes_atual}", size=18, weight="bold", color=rosa)

    # -----------------------------
    # Função para atualizar resumo
    # -----------------------------
    def atualizar_resumo():
        # Soma todos os valores de gastos
        total = sum([float(g["valor"]) for g in dados["gastos"]])
        total_gasto_txt.value = f"Total gasto: R$ {total:.2f}"

        # Se existe salário configurado
        if dados["salario"]:
            saldo = float(dados["salario"]) - total

            # Se saldo negativo, muda para vermelho
            if saldo < 0:
                saldo_restante_txt.value = f"Saldo restante: -R$ {abs(saldo):.2f}"
                saldo_restante_txt.color = "red"
            else:
                saldo_restante_txt.value = f"Saldo restante: R$ {saldo:.2f}"
                saldo_restante_txt.color = "green"
        else:
            # Caso não tenha salário registrado
            saldo_restante_txt.value = "Saldo restante: R$ 0,00"
            saldo_restante_txt.color = "black"

        page.update()

    # -----------------------------------
    # Função responsável por renderizar a tabela
    # -----------------------------------
    def renderizar_tabela():
        tabela.controls.clear()  # Limpa tabela antes de recriar

        # Cabeçalho
        cabecalho = ft.Container(
            content=ft.Row(
                [
                    ft.Container(ft.Text("ITEM", weight="bold"), expand=True, alignment=ft.alignment.center_left),
                    ft.Container(ft.Text("VALOR (R$)", weight="bold"), width=100, alignment=ft.alignment.center),
                    ft.Container(ft.Text("EXCLUIR", weight="bold"), width=80, alignment=ft.alignment.center),
                ],
                alignment="spaceBetween",
            ),
            bgcolor=cinza,
            padding=10,
            border=ft.border.all(1, rosa),
            border_radius=8,
        )
        tabela.controls.append(cabecalho)

        # Renderiza cada linha da lista de gastos
        for i, g in enumerate(dados["gastos"]):
            linha = ft.Container(
                content=ft.Row(
                    [
                        ft.Container(ft.Text(g["nome"]), expand=True, alignment=ft.alignment.center_left),
                        ft.Container(ft.Text(f"R$ {float(g['valor']):.2f}"), width=100, alignment=ft.alignment.center),
                        ft.Container(
                            ft.IconButton(
                                icon=ft.Icons.DELETE,
                                icon_color="red",
                                tooltip="Remover",
                                on_click=lambda e, i=i: remover_gasto(i)  # Remove item certo
                            ),
                            width=80,
                            alignment=ft.alignment.center,
                        ),
                    ],
                    alignment="spaceBetween",
                ),
                padding=10,
                border=ft.border.all(1, rosa),
                border_radius=8,
            )
            tabela.controls.append(linha)

        atualizar_resumo()

    # -------------------------
    # Função para adicionar gasto
    # -------------------------
    def adicionar_gasto(e):
        # Verifica se os campos estão vazios
        if not gasto_nome.value or not gasto_valor.value:
            page.snack_bar = ft.SnackBar(ft.Text("Preencha todos os campos!"), bgcolor="red")
            page.snack_bar.open = True
            page.update()
            return

        # Converte valor para float
        try:
            valor = float(gasto_valor.value)
        except ValueError:
            page.snack_bar = ft.SnackBar(ft.Text("Valor inválido!"), bgcolor="red")
            page.snack_bar.open = True
            page.update()
            return

        # Soma total atual + o novo gasto
        total = sum([float(g["valor"]) for g in dados["gastos"]]) + valor

        # Se ultrapassar o limite, mostrar alerta
        if dados["limite"] > 0 and total > dados["limite"]:

            # Função continuar mesmo passando o limite
            def continuar(e):
                dados["gastos"].append({"nome": gasto_nome.value, "valor": valor})
                gasto_nome.value = ""
                gasto_valor.value = ""
                salvar_gastos(mes_atual, dados)
                page.close(alerta)
                renderizar_tabela()

            # Função cancelar
            def cancelar(e):
                page.close(alerta)
                page.update()

            # Criando alerta estilizado
            alerta = ft.AlertDialog(
                modal=True,
                title=ft.Text("⚠️ Limite ultrapassado!", color="red", size=18, weight="bold"),
                content=ft.Text(
                    f"Você ultrapassou o limite mensal de R$ {dados['limite']:.2f}.\nDeseja continuar?",
                    size=16,
                ),
                actions=[
                    ft.TextButton("💖 Continuar", on_click=continuar),
                    ft.TextButton("Cancelar", on_click=cancelar),
                ],
                actions_alignment="end",
                bgcolor="#fff0f5",
            )

            page.dialog = alerta
            page.update()
            alerta.open = True
            page.update()
            return

        # Caso o limite não seja ultrapassado
        dados["gastos"].append({"nome": gasto_nome.value, "valor": valor})
        gasto_nome.value = ""
        gasto_valor.value = ""
        salvar_gastos(mes_atual, dados)
        renderizar_tabela()

    # -------------------------
    # Função para remover um gasto
    # -------------------------
    def remover_gasto(index):
        del dados["gastos"][index]
        salvar_gastos(mes_atual, dados)
        renderizar_tabela()

    # -------------------------
    # Salvar salário
    # -------------------------
    def salvar_salario(e):
        try:
            dados["salario"] = float(salario_input.value)
            salvar_gastos(mes_atual, dados)
            atualizar_resumo()
            page.snack_bar = ft.SnackBar(ft.Text("Salário adicionado!"), bgcolor=rosa)
            page.snack_bar.open = True
            page.update()
        except ValueError:
            page.snack_bar = ft.SnackBar(ft.Text("Digite um salário válido!"), bgcolor="red")
            page.snack_bar.open = True
            page.update()

    # -------------------------
    # Salvar limite mensal
    # -------------------------
    def salvar_limite(e):
        try:
            dados["limite"] = float(limite_input.value)
            salvar_gastos(mes_atual, dados)
            atualizar_resumo()

            # Caixa de diálogo confirmando limite
            confirm = ft.AlertDialog(
                modal=True,
                title=ft.Text("✅ Limite adicionado!", color="green", size=18, weight="bold"),
                content=ft.Text(f"Seu limite mensal foi definido para R$ {dados['limite']:.2f}."),
                actions=[ft.TextButton("Fechar", on_click=lambda e: page.close(confirm))],
                actions_alignment="center",
                bgcolor="#f0fff0",
            )

            page.dialog = confirm
            page.update()
            confirm.open = True
            page.update()

        except ValueError:
            page.snack_bar = ft.SnackBar(ft.Text("Digite um limite válido!"), bgcolor="red")
            page.snack_bar.open = True
            page.update()

    # -------------------------
    # Função para trocar o mês no drawer
    # -------------------------
    def abrir_mes(e):
        nonlocal dados, mes_atual
        mes_atual = e.control.title.value  # Pega o mês clicado
        titulo_mes.value = f"Mês atual: {mes_atual}"
        dados = carregar_gastos(mes_atual)

        # Preenche campos com dados do mês carregado
        salario_input.value = str(dados["salario"]) if dados["salario"] else ""
        limite_input.value = str(dados["limite"]) if dados["limite"] else ""

        renderizar_tabela()
        page.drawer.open = False
        page.update()

    # Drawer lateral com lista de meses
    drawer = ft.NavigationDrawer(
        controls=[
            ft.Container(
                ft.Text("📅 Selecione um mês", size=18, weight="bold", color=rosa),
                padding=15,
            ),
            *[ft.ListTile(title=ft.Text(m), on_click=abrir_mes) for m in meses],
        ]
    )

    # Abre o drawer quando clicar no menu
    def abrir_drawer(e):
        page.drawer = drawer
        page.drawer.open = True
        page.update()

    # App bar superior
    page.appbar = ft.AppBar(
        leading=ft.IconButton(icon=ft.Icons.MENU, on_click=abrir_drawer),
        title=ft.Text("💸 Controle de Gastos", color=rosa, weight="bold"),
        bgcolor="white",
        center_title=True,
    )

    # Conteúdo principal do app
    page.add(
        ft.Column(
            [
                titulo_mes,

                # Linha de salário
                ft.Row(
                    [
                        salario_input,
                        ft.ElevatedButton(
                            "Adicionar salário",
                            on_click=salvar_salario,
                            bgcolor=rosa,
                            color="white",
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=12),
                                padding=20,
                            ),
                        ),
                    ],
                    alignment="center",
                ),

                # Linha do limite
                ft.Row(
                    [
                        limite_input,
                        ft.ElevatedButton(
                            "Adicionar limite",
                            on_click=salvar_limite,
                            bgcolor="#f48fb1",
                            color="white",
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=12),
                                padding=20,
                            ),
                        ),
                    ],
                    alignment="center",
                ),

                ft.Divider(),

                ft.Text("Adicionar novo gasto", size=18, weight="bold"),

                # Linha para adicionar gasto
                ft.Row(
                    [
                        gasto_nome,
                        gasto_valor,
                        ft.FloatingActionButton(icon=ft.Icons.ADD, bgcolor=rosa, on_click=adicionar_gasto),
                    ],
                    alignment="center",
                ),

                ft.Divider(),

                ft.Text("Lista de gastos", size=18, weight="bold"),

                tabela,

                # Linha com total e saldo
                ft.Row(
                    [
                        ft.Container(
                            content=total_gasto_txt,
                            border=ft.border.all(1, rosa),
                            border_radius=12,
                            padding=10,
                            bgcolor=cinza,
                            expand=True,
                        ),
                        ft.Container(
                            content=saldo_restante_txt,
                            border=ft.border.all(1, rosa),
                            border_radius=12,
                            padding=10,
                            bgcolor=cinza,
                            expand=True,
                        ),
                    ],
                    alignment="center",
                ),
            ],
            alignment="center",
            horizontal_alignment="center",
        )
    )

    # Atualiza a tabela ao iniciar
    renderizar_tabela()


# Inicializa o app Flet chamando a função principal
ft.app(target=main)
