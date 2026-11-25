"""
Durable server-side accessibility remediation script run inside the pretix container.
Patches pretixcontrol/auth/base.html, pretixcontrol/auth/login.html, and pretixpresale/base.html
so WCAG 2.1 AA fixes are served directly by Django (no client JS style injection).
"""
from pathlib import Path

AUTH_BASE = Path("/pretix/src/pretix/control/templates/pretixcontrol/auth/base.html")
AUTH_LOGIN = Path("/pretix/src/pretix/control/templates/pretixcontrol/auth/login.html")
PRESALE_BASE = Path("/pretix/src/pretix/presale/templates/pretixpresale/base.html")


def patch_auth_base():
    text = AUTH_BASE.read_text(encoding="utf-8")

    # 1. HTML lang attribute (WCAG 3.1.1 / axe html-has-lang)
    text = text.replace(
        "<html{% if rtl %}",
        '<html lang="en"{% if rtl %}',
    ) if '<html lang="en"' not in text else text

    # 2. SEO / context meta description
    meta_tag = '    <meta name="description" content="{{ django_settings.PRETIX_INSTANCE_NAME }} Control Panel Authentication">\n'
    if 'name="description"' not in text:
        text = text.replace(
            '    <meta name="viewport" content="width=device-width, initial-scale=1">',
            '    <meta name="viewport" content="width=device-width, initial-scale=1">\n' + meta_tag.rstrip("\n"),
        )

    # 3. Accessible logo alt text
    target_img = '<img src="{% static "pretixbase/img/pretix-logo.svg" %}" class="logo"/>'
    repl_img = '<img src="{% static "pretixbase/img/pretix-logo.svg" %}" class="logo" alt="pretix official logo" role="img"/>'
    if 'alt="pretix official logo"' not in text and target_img in text:
        text = text.replace(target_img, repl_img)

    # 4. Semantic landmarks (<header role="banner">, <main role="main">, <footer>)
    target_logo_anchor = (
        '<div class="container">\n'
        '    <a href="{% url "control:auth.login" %}">\n'
        '        <img src="{% static "pretixbase/img/pretix-logo.svg" %}" class="logo" alt="pretix official logo" role="img"/>\n'
        '    </a>'
    )
    repl_logo_anchor = (
        '<div class="container">\n'
        '    <header role="banner">\n'
        '        <a href="{% url "control:auth.login" %}">\n'
        '            <img src="{% static "pretixbase/img/pretix-logo.svg" %}" class="logo" alt="pretix official logo" role="img"/>\n'
        '        </a>\n'
        '    </header>\n'
        '    <main role="main" id="main-content">'
    )
    if '<main role="main"' not in text:
        assert target_logo_anchor in text, "Expected container + logo anchor block in auth/base.html"
        text = text.replace(target_logo_anchor, repl_logo_anchor, 1)
        assert "    <footer>" in text, "Expected <footer> in auth/base.html"
        text = text.replace("    <footer>", "    </main>\n    <footer>", 1)

    AUTH_BASE.write_text(text, encoding="utf-8")


def patch_auth_login():
    text = AUTH_LOGIN.read_text(encoding="utf-8")
    heading = '    <h1 class="sr-only">{% trans "Log in" %} — {{ django_settings.PRETIX_INSTANCE_NAME }}</h1>\n'
    if "<h1" not in text:
        text = text.replace(
            "{% block content %}\n",
            "{% block content %}\n" + heading,
            1,
        )
    AUTH_LOGIN.write_text(text, encoding="utf-8")


def patch_presale_base():
    text = PRESALE_BASE.read_text(encoding="utf-8")
    style_block = (
        '    <style id="sqe-a11y-contrast-patch">\n'
        '      .text-muted, .help-block { color: #4a4a4a !important; }\n'
        '      a:focus-visible, button:focus-visible, input:focus-visible, select:focus-visible {\n'
        '        outline: 3px solid #ff9900 !important;\n'
        '        outline-offset: 2px !important;\n'
        '      }\n'
        '    </style>\n'
        '</head>'
    )
    if 'id="sqe-a11y-contrast-patch"' not in text:
        assert "</head>" in text, "Expected </head> in pretixpresale/base.html"
        text = text.replace("</head>", style_block, 1)
    if 'name="description"' not in text:
        meta_desc = '    <meta name="description" content="Event Ticket Registration and Storefront">\n</head>'
        text = text.replace("</head>", meta_desc, 1)
    PRESALE_BASE.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    patch_auth_base()
    patch_auth_login()
    patch_presale_base()
    print("Durable server-side accessibility remediation patches applied cleanly.")
