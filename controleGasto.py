import flet as ft
import json
import os
from datetime import datetime

DATA_DIR = "data"

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)


def caminho_arquivo(mes):
    return os.path.join(DATA_DIR, f"gastos_{mes}.json")


def carregar_gastos(mes):
    arquivo = caminho_arquivo(mes)
    if os.path.exists(arquivo):
        with open(arquivo, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"salario": 0, "limite": 0, "gastos": []}


def salvar_gastos(mes, dados):
    with open(caminho_arquivo(mes), "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------
# TELA DE CONTROLE DE GASTOS (SEGUNDA TELA)
# ---------------------------------------------------
def tela_gastos(page: ft.Page):

    rosa = "#ffb6c1"
    cinza = "#f8f8f8"

    meses_2026 = [
        "Janeiro 2026", "Fevereiro 2026", "Março 2026", "Abril 2026",
        "Maio 2026", "Junho 2026", "Julho 2026", "Agosto 2026",
        "Setembro 2026", "Outubro 2026", "Novembro 2026", "Dezembro 2026"
    ]

    mes_atual = meses_2026[0]
    dados = carregar_gastos(mes_atual)

    salario_input = ft.TextField(label="Salário mensal (R$)", width=200)
    limite_input = ft.TextField(label="Limite mensal (R$)", width=200)
    gasto_nome = ft.TextField(label="Nome do gasto", width=200)
    gasto_valor = ft.TextField(label="Valor (R$)", width=100)

    tabela = ft.Column(scroll="auto", expand=True)

    total_gasto_txt = ft.Text(size=16, weight="bold")
    saldo_restante_txt = ft.Text(size=16, weight="bold", color="green")
    titulo_mes = ft.Text(f"Mês atual: {mes_atual}", size=20, weight="bold", color=rosa)

    # --------------------------------------
    def atualizar_resumo():
        total = sum([float(g["valor"]) for g in dados["gastos"]])
        total_gasto_txt.value = f"Total gasto: R$ {total:.2f}"

        if dados["salario"]:
            saldo = float(dados["salario"]) - total
            if saldo < 0:
                saldo_restante_txt.value = f"Saldo restante: -R$ {abs(saldo):.2f}"
                saldo_restante_txt.color = "red"
            else:
                saldo_restante_txt.value = f"Saldo restante: R$ {saldo:.2f}"
                saldo_restante_txt.color = "green"
        else:
            saldo_restante_txt.value = "Saldo restante: R$ 0,00"
            saldo_restante_txt.color = "black"

        page.update()

    # --------------------------------------
    def renderizar_tabela():
        tabela.controls.clear()

        cabecalho = ft.Container(
            content=ft.Row(
                [
                    ft.Container(ft.Text("ITEM", weight="bold"), expand=True),
                    ft.Container(ft.Text("VALOR (R$)", weight="bold"), width=100),
                    ft.Container(ft.Text("EXCLUIR", weight="bold"), width=80),
                ],
                alignment="spaceBetween",
            ),
            bgcolor=cinza,
            padding=10,
            border=ft.border.all(1, rosa),
            border_radius=8,
        )
        tabela.controls.append(cabecalho)

        for i, g in enumerate(dados["gastos"]):
            linha = ft.Container(
                content=ft.Row(
                    [
                        ft.Container(ft.Text(g["nome"]), expand=True),
                        ft.Container(ft.Text(f"R$ {float(g['valor']):.2f}"), width=100),
                        ft.Container(
                            ft.IconButton(
                                icon=ft.Icons.DELETE,
                                icon_color="red",
                                on_click=lambda e, i=i: remover_gasto(i)
                            ),
                            width=80,
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

    # --------------------------------------
    def adicionar_gasto(e):
        if not gasto_nome.value or not gasto_valor.value:
            page.snack_bar = ft.SnackBar(ft.Text("Preencha todos os campos!"), bgcolor="red")
            page.snack_bar.open = True
            page.update()
            return

        try:
            valor = float(gasto_valor.value)
        except ValueError:
            page.snack_bar = ft.SnackBar(ft.Text("Valor inválido!"), bgcolor="red")
            page.snack_bar.open = True
            page.update()
            return

        total = sum([float(g["valor"]) for g in dados["gastos"]]) + valor

        if dados["limite"] > 0 and total > dados["limite"]:

            def continuar(e):
                dados["gastos"].append({"nome": gasto_nome.value, "valor": valor})
                gasto_nome.value = ""
                gasto_valor.value = ""
                salvar_gastos(mes_atual, dados)
                page.close(alerta)
                renderizar_tabela()

            def cancelar(e):
                page.close(alerta)

            alerta = ft.AlertDialog(
                modal=True,
                title=ft.Text("⚠️ Limite ultrapassado!", color="red", size=18),
                content=ft.Text(
                    f"Você ultrapassou o limite mensal.\nDeseja continuar?",
                    size=16,
                ),
                actions=[
                    ft.TextButton("Continuar", on_click=continuar),
                    ft.TextButton("Cancelar", on_click=cancelar),
                ],
                actions_alignment="end",
                bgcolor="#fff0f5",
            )

            page.dialog = alerta
            alerta.open = True
            page.update()
            return

        dados["gastos"].append({"nome": gasto_nome.value, "valor": valor})
        gasto_nome.value = ""
        gasto_valor.value = ""
        salvar_gastos(mes_atual, dados)
        renderizar_tabela()

    # --------------------------------------
    def remover_gasto(index):
        del dados["gastos"][index]
        salvar_gastos(mes_atual, dados)
        renderizar_tabela()

    # --------------------------------------
    def salvar_salario(e):
        try:
            dados["salario"] = float(salario_input.value)
            salvar_gastos(mes_atual, dados)
            atualizar_resumo()
        except:
            pass

    def salvar_limite(e):
        try:
            dados["limite"] = float(limite_input.value)
            salvar_gastos(mes_atual, dados)
            atualizar_resumo()
        except:
            pass

    # --------------------------------------
    def abrir_mes(e):
        nonlocal dados, mes_atual
        mes_atual = e.control.title.value
        titulo_mes.value = f"Mês atual: {mes_atual}"
        dados = carregar_gastos(mes_atual)
        salario_input.value = str(dados["salario"]) if dados["salario"] else ""
        limite_input.value = str(dados["limite"]) if dados["limite"] else ""
        renderizar_tabela()
        page.drawer.open = False
        page.update()

    # Drawer
    drawer = ft.NavigationDrawer(
        controls=[
            ft.Container(
                ft.Text("📅 Meses de 2026", size=18, weight="bold", color=rosa),
                padding=15,
            ),
            *[ft.ListTile(title=ft.Text(m), on_click=abrir_mes) for m in meses_2026],
        ]
    )

    # AppBar
    page.appbar = ft.AppBar(
        leading=ft.IconButton(icon=ft.Icons.MENU, on_click=lambda e: toggle_drawer()),
        title=ft.Text("💸 Controle de Gastos", color=rosa, weight="bold"),
        bgcolor="white",
        center_title=True,
    )

    def toggle_drawer():
        page.drawer = drawer
        page.drawer.open = True
        page.update()

    # Conteúdo da página
    page.add(
        ft.Column(
            [
                titulo_mes,

                ft.Row([salario_input,
                        ft.ElevatedButton("Salvar", on_click=salvar_salario, bgcolor=rosa, color="white")],
                       alignment="center"),

                ft.Row([limite_input,
                        ft.ElevatedButton("Salvar", on_click=salvar_limite, bgcolor="#f48fb1", color="white")],
                       alignment="center"),

                ft.Divider(),

                ft.Text("Adicionar novo gasto", size=18, weight="bold"),

                ft.Row([
                    gasto_nome,
                    gasto_valor,
                    ft.FloatingActionButton(icon=ft.Icons.ADD, bgcolor=rosa, on_click=adicionar_gasto),
                ], alignment="center"),

                ft.Divider(),

                ft.Text("Lista de gastos", size=18, weight="bold"),

                tabela,

                ft.Row(
                    [
                        ft.Container(total_gasto_txt, border=ft.border.all(1, rosa), padding=10, expand=True),
                        ft.Container(saldo_restante_txt, border=ft.border.all(1, rosa), padding=10, expand=True),
                    ],
                    alignment="center",
                ),
            ],
            horizontal_alignment="center",
        )
    )

    renderizar_tabela()


# ---------------------------------------------------
# TELA INICIAL + SISTEMA DE ROTAS
# ---------------------------------------------------
def main(page: ft.Page):

    rosa = "#ffb6c1"

    page.title = "Organizador Financeiro"
    page.theme_mode = "light"

    # ----------- SISTEMA DE ROTAS -----------  
    def route_change(e):
        page.views.clear()

        if page.route == "/":
            page.views.append(
                ft.View(
                    "/",
                    controls=[
                        ft.Column(
                            [
                                ft.Text("Organizador Financeiro", size=32, weight="bold", color=rosa),
                                ft.ElevatedButton(
                                    "Abrir anotações",
                                    bgcolor=rosa,
                                    color="white",
                                    width=220,
                                    on_click=lambda _: page.go("/gastos"),
                                )
                            ],
                            alignment="center",
                            horizontal_alignment="center",
                        )
                    ]
                )
            )

        elif page.route == "/gastos":
            page.views.append(
                ft.View(
                    "/gastos",
                    controls=[]
                )
            )
            tela_gastos(page)

        page.update()

    page.on_route_change = route_change
    page.go("/")


ft.app(target=main)
