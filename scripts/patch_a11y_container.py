path = '/pretix/src/pretix/control/templates/pretixcontrol/auth/base.html'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

target = '<img src="{% static "pretixbase/img/pretix-logo.svg" %}" class="logo"/>'
replacement = '<img src="{% static "pretixbase/img/pretix-logo.svg" %}" class="logo" alt="pretix official logo" role="img"/>'

if 'alt="pretix official logo"' not in c:
    assert target in c, "Target not found in template"
    c = c.replace(target, replacement)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(c)
    print('Template patched successfully with durable accessibility fix!')
else:
    print('Template already has durable accessibility fix!')
