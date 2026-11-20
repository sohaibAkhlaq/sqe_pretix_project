import os
import sys
import shutil
import subprocess

def get_tokens():
    docker_bin = shutil.which("docker")
    if not docker_bin:
        for c in [
            os.path.expanduser(r"~\AppData\Local\Programs\DockerDesktop\resources\bin\docker.exe"),
            r"C:\Program Files\Docker\Docker\resources\bin\docker.exe",
        ]:
            if os.path.isfile(c):
                docker_bin = c
                break
    if not docker_bin:
        docker_bin = "docker"

    code = (
        "import os, django; "
        "os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pretix.settings'); "
        "django.setup(); "
        "from pretix.base.models import TeamAPIToken; "
        "tokens = {t.name: t.token for t in TeamAPIToken.objects.all()}; "
        "print('TOKENS_JSON:' + str(tokens))"
    )
    cmd = [docker_bin, "exec", "pretix_web", "python3", "-c", code]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Failed to fetch tokens: {res.stderr}")
    for line in res.stdout.splitlines():
        if line.startswith("TOKENS_JSON:"):
            import ast
            return ast.literal_eval(line.replace("TOKENS_JSON:", ""))
    raise ValueError(f"Could not parse tokens from output: {res.stdout}")

if __name__ == "__main__":
    t = get_tokens()
    print("Fetched tokens:", t)
