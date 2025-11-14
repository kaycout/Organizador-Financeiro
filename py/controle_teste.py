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
    return {"salario": 0.0, "limite": 0.0, "gastos": []}


def salvar_gastos(mes, dados):
    with open(caminho_arquivo(mes), "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


def main(page: ft.Page):
    page.title = "Organizador Financeiro"
    page.theme_mode = "light"
    page.window_width = 900
    page.window_height = 700

    rosa = "#ffb6c1"
    cinza = "#f8f8f8"

    MESES = [
        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
    ]

    current_month = MESES[datetime.now().month - 1]
    gastos_view = None

    # Drawer
    drawer = ft.NavigationDrawer(controls=[])
    page.drawer = drawer

    # Abre o drawer (compatível com Flet 0.28.3)
    def abrir_drawer(e=None):
        page.drawer = drawer
        page.drawer.open = True
        page.update()

    # Atualiza conteúdos do drawer
    def build_drawer():
        lst = [ft.Container(ft.Text("📅 Selecione um mês", size=16, weight="bold", color=rosa), padding=10)]
        for m in MESES:
            lst.append(ft.ListTile(title=ft.Text(m), on_click=lambda e, mm=m: selecionar_mes(mm)))
        drawer.controls = lst
        page.drawer = drawer
        page.update()

    # Selecionar mês no drawer
    def selecionar_mes(mes):
        nonlocal current_month, gastos_view
        current_month = mes

        if gastos_view is not None:
            try:
                page.views.remove(gastos_view)
            except:
                pass

        gv = ensure_gastos_view()
        page.views.append(gv)
        page.go(gv.route)

        page.drawer.open = False
        page.update()

    # Criar view de gastos
    def ensure_gastos_view():
        nonlocal gastos_view, current_month
        mes_atual = current_month
        dados = carregar_gastos(mes_atual)

        salario_input = ft.TextField(label="Salário mensal (R$)", width=240, value=str(dados.get("salario") or ""))
        limite_input = ft.TextField(label="Limite mensal (R$)", width=240, value=str(dados.get("limite") or ""))
        gasto_nome = ft.TextField(label="Nome do gasto", width=320)
        gasto_valor = ft.TextField(label="Valor (R$)", width=140)
        tabela = ft.Column(scroll="auto", expand=True)
        total_gasto_txt = ft.Text(size=16, weight="bold")
        saldo_restante_txt = ft.Text(size=16, weight="bold")

        # Atualizar totals
        def atualizar_resumo():
            total = sum(float(g["valor"]) for g in dados["gastos"]) if dados["gastos"] else 0
            total_gasto_txt.value = f"Total gasto: R$ {total:.2f}"

            salario_val = float(dados.get("salario") or 0)
            saldo = salario_val - total

            if saldo < 0:
                saldo_restante_txt.value = f"Saldo restante: -R$ {abs(saldo):.2f}"
                saldo_restante_txt.color = "red"
            else:
                saldo_restante_txt.value = f"Saldo restante: R$ {saldo:.2f}"
                saldo_restante_txt.color = "green"

            page.update()

        # Render tabela
        def renderizar_tabela():
            tabela.controls.clear()

            cabecalho = ft.Container(
                content=ft.Row(
                    [
                        ft.Container(ft.Text("ITEM", weight="bold"), expand=True),
                        ft.Container(ft.Text("VALOR (R$)", weight="bold"), width=140, alignment=ft.alignment.center),
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

            for i, g in enumerate(dados["gastos"]):
                linha = ft.Container(
                    content=ft.Row(
                        [
                            ft.Container(ft.Text(g["nome"]), expand=True),
                            ft.Container(ft.Text(f"R$ {float(g['valor']):.2f}"), width=140, alignment=ft.alignment.center),
                            ft.Container(
                                ft.TextButton("EXCLUIR", on_click=lambda e, ii=i: remover(ii)),
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

        # Remover gasto
        def remover(i):
            if 0 <= i < len(dados["gastos"]):
                del dados["gastos"][i]
                salvar_gastos(mes_atual, dados)
                renderizar_tabela()

        # Adicionar gasto
        def add_gasto(e):
            if not gasto_nome.value or not gasto_valor.value:
                page.snack_bar = ft.SnackBar(ft.Text("Preencha os campos"), bgcolor="red")
                page.snack_bar.open = True
                page.update()
                return

            try:
                valor = float(gasto_valor.value)
            except:
                page.snack_bar = ft.SnackBar(ft.Text("Valor inválido"), bgcolor="red")
                page.snack_bar.open = True
                page.update()
                return

            total = sum(float(g["valor"]) for g in dados["gastos"]) + valor
            limite = float(dados.get("limite") or 0)

            # Se ultrapassar o limite → pop-up
            if limite > 0 and total > limite:

                def continuar(ev):
                    dados["gastos"].append({"nome": gasto_nome.value, "valor": valor})
                    salvar_gastos(mes_atual, dados)
                    gasto_nome.value = ""
                    gasto_valor.value = ""
                    dialog.open = False
                    renderizar_tabela()
                    page.update()

                def cancelar(ev):
                    dialog.open = False
                    page.update()

                dialog = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("⚠️ Limite ultrapassado!", color="red"),
                    content=ft.Text(f"O limite de R$ {limite:.2f} foi ultrapassado. Continuar?"),
                    actions=[
                        ft.TextButton("Continuar", on_click=continuar),
                        ft.TextButton("Cancelar", on_click=cancelar),
                    ],
                )
                page.dialog = dialog
                dialog.open = True
                page.update()
                return

            dados["gastos"].append({"nome": gasto_nome.value, "valor": valor})
            salvar_gastos(mes_atual, dados)
            gasto_nome.value = ""
            gasto_valor.value = ""
            renderizar_tabela()

        # Salvar salário
        def salvar_salario(e):
            try:
                dados["salario"] = float(salario_input.value or 0)
                salvar_gastos(mes_atual, dados)
                atualizar_resumo()
            except:
                page.snack_bar = ft.SnackBar(ft.Text("Valor inválido"), bgcolor="red")
                page.snack_bar.open = True
                page.update()

        # Salvar limite
        def salvar_limite(e):
            try:
                dados["limite"] = float(limite_input.value or 0)
                salvar_gastos(mes_atual, dados)
                atualizar_resumo()
            except:
                page.snack_bar = ft.SnackBar(ft.Text("Valor inválido"), bgcolor="red")
                page.snack_bar.open = True
                page.update()

        build_drawer()

        view = ft.View(
            route="/gastos",
            appbar=ft.AppBar(
                leading=ft.IconButton(icon=ft.Icons.MENU, on_click=abrir_drawer),
                title=ft.Text("💸 Controle de Gastos", color=rosa),
                center_title=True,
                bgcolor="white",
            ),
            padding=20,
            controls=[
                ft.Column(
                    [
                        ft.Text(f"Mês atual: {mes_atual}", size=18, weight="bold", color=rosa),

                        ft.Row(
                            [salario_input, ft.ElevatedButton("Adicionar salário", on_click=salvar_salario, bgcolor=rosa, color="white")],
                            alignment="center"
                        ),

                        ft.Row(
                            [limite_input, ft.ElevatedButton("Adicionar limite", on_click=salvar_limite, bgcolor="#f48fb1", color="white")],
                            alignment="center"
                        ),

                        ft.Divider(),
                        ft.Text("Adicionar novo gasto", size=18, weight="bold"),

                        ft.Row(
                            [gasto_nome, gasto_valor,
                             ft.FloatingActionButton(icon=ft.Icons.ADD, bgcolor=rosa, on_click=add_gasto)],
                            alignment="center"
                        ),

                        ft.Divider(),
                        ft.Text("Lista de gastos", size=18, weight="bold"),
                        tabela,

                        ft.Row(
                            [
                                ft.Container(content=total_gasto_txt, border=ft.border.all(1, rosa),
                                             border_radius=12, padding=10, bgcolor=cinza, expand=True),
                                ft.Container(content=saldo_restante_txt, border=ft.border.all(1, rosa),
                                             border_radius=12, padding=10, bgcolor=cinza, expand=True),
                            ],
                            alignment="center"
                        ),
                    ],
                    alignment="center",
                    horizontal_alignment="center",
                )
            ],
        )

        renderizar_tabela()
        gastos_view = view
        return view

    # Tela de anotações
    def tela_anotacoes():
        rosa_claro = "#ffe4ec"
        anotacao_input = ft.TextField(label="Digite sua anotação", multiline=True)

        def abrir_popup(e):
            page.dialog = dialog
            dialog.open = True
            page.update()

        def salvar_popup(e):
            page.snack_bar = ft.SnackBar(ft.Text("Anotação salva!"), bgcolor=rosa)
            page.snack_bar.open = True
            page.update()

        def fechar_popup(e):
            dialog.open = False
            page.update()

        dialog = ft.AlertDialog(
            modal=True,
            content=ft.Column(
                [
                    ft.Row(
                        [ft.Text("Caderninho de Anotações", size=18, weight="bold"),
                         ft.IconButton(icon=ft.Icons.CLOSE, on_click=fechar_popup)],
                        alignment="spaceBetween",
                    ),
                    anotacao_input,
                    ft.Row(
                        [
                            ft.ElevatedButton("Salvar", on_click=salvar_popup),
                            ft.ElevatedButton("Fechar", on_click=fechar_popup),
                        ],
                        alignment="end"
                    )
                ]
            )
        )

        return ft.View(
            route="/anotacoes",
            bgcolor=rosa_claro,
            appbar=ft.AppBar(
                leading=ft.IconButton(icon=ft.Icons.MENU, on_click=abrir_drawer),
                title=ft.Text("Anotações"),
                center_title=True,
                bgcolor=rosa,
            ),
            controls=[
                ft.Container(
                    expand=True,
                    alignment=ft.alignment.center,
                    content=ft.FloatingActionButton(
                        icon=ft.Icons.ADD,
                        bgcolor=rosa,
                        width=70,
                        height=70,
                        on_click=abrir_popup,
                    )
                )
            ]
        )

    # Ir para anotações
    def ir_para_anotacoes(e):
        v = tela_anotacoes()
        page.views.append(v)
        page.go(v.route)
        page.update()

    botao_principal = ft.ElevatedButton(
        "Abrir Anotações",
        bgcolor=rosa,
        color="white",
        width=220,
        height=60,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=16)),
        on_click=ir_para_anotacoes
    )

    # 🔥 Primeira página com título e botão CENTRALIZADOS
    view_inicial = ft.View(
        route="/",
        controls=[
            ft.Container(
                expand=True,
                alignment=ft.alignment.center,
                content=ft.Column(
                    [
                        ft.Text(
                            "Organizador Financeiro",
                            size=32,
                            weight="bold",
                            color=rosa,
                            text_align="center",
                        ),
                        ft.Container(height=20),
                        botao_principal
                    ],
                    alignment="center",
                    horizontal_alignment="center"
                )
            )
        ]
    )

    build_drawer()

    page.views.append(view_inicial)
    page.go("/")

    def on_view_pop(route):
        if len(page.views) > 1:
            page.views.pop()
        page.update()

    page.on_view_pop = on_view_pop


ft.app(target=main)
