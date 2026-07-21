from shared import formatear_texto_para_reportlab


def test_heading_markdown_is_parsed():
    elementos = formatear_texto_para_reportlab("### Zona Norte")

    assert elementos[0][0] == "heading"
    assert elementos[0][1][0] == 3
    assert elementos[0][1][1] == "Zona Norte"


def test_bold_markdown_is_preserved():
    elementos = formatear_texto_para_reportlab("**Oportunidad clave**")

    assert elementos[0][0] == "paragraph"
    assert "<b>Oportunidad clave</b>" in elementos[0][1]
