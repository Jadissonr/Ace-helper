"""
Detecta a GPU NVIDIA instalada, verifica se existe um driver mais
recente disponível e, se houver, baixa e instala silenciosamente.

Usa o nvidia-smi (nativo de qualquer instalação de driver NVIDIA) pra
detectar a GPU e a versão atual, e um endpoint da NVIDIA não
documentado oficialmente — mas usado publicamente há anos por várias
ferramentas open-source de atualização de driver (ex:
https://github.com/ZenitH-AT/nvidia-update) — pra consultar a versão
mais recente disponível.

AVISO: por depender de uma API não-oficial, esse módulo pode parar de
funcionar se a NVIDIA mudar o formato sem aviso. Também: atualizar
driver de GPU tem um risco pequeno, mas real, de causar problemas de
tela — por isso sempre criamos um ponto de restauração antes.
"""

import os
import subprocess
import tempfile
import platform
import xml.etree.ElementTree as ET
import requests

from core.logger import log

_NO_WINDOW_FLAGS = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

LOOKUP_GPU_URL = "https://www.nvidia.com/Download/API/lookupValueSearch.aspx?TypeID=3"
DRIVER_SERVICE_URL = "https://gfwsl.geforce.com/services_toolkit/services/com/nvidia/services/AjaxDriverService.php"


def _run(args, timeout=15):
    try:
        result = subprocess.run(
            args, capture_output=True, text=True, timeout=timeout,
            creationflags=_NO_WINDOW_FLAGS
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except FileNotFoundError:
        return -1, "", "nvidia-smi não encontrado."
    except subprocess.TimeoutExpired:
        return -1, "", "Tempo esgotado."


def get_gpu_info():
    """
    Retorna (nome_gpu, versao_driver_atual) usando o nvidia-smi.
    Retorna (None, None) se não achar uma GPU NVIDIA ou o nvidia-smi
    (o que também significa: não é uma máquina com placa NVIDIA, ou
    não tem driver nenhum instalado ainda).
    """
    code, out, _err = _run(["nvidia-smi", "--query-gpu=name,driver_version", "--format=csv,noheader"])
    if code != 0 or not out:
        return None, None
    primeira_linha = out.splitlines()[0]
    partes = [p.strip() for p in primeira_linha.split(",")]
    if len(partes) < 2:
        return None, None
    return partes[0], partes[1]


def _get_os_id():
    """Windows 11 usa osID 135, Windows 10 usa 57 (ambos variante 64-bit).
    Detecta pelo build number; assume Windows 10 se não conseguir."""
    try:
        build = int(platform.version().split(".")[-1])
        return 135 if build >= 22000 else 57
    except Exception:
        return 57


def _find_pfid(gpu_name: str):
    """Consulta a lista de GPUs da NVIDIA e acha o pfid (ID do produto)
    correspondente ao nome da GPU detectada."""
    try:
        resp = requests.get(LOOKUP_GPU_URL, timeout=15)
        root = ET.fromstring(resp.content)
        gpu_name_clean = gpu_name.replace("NVIDIA", "").strip().lower()

        melhor_pfid = None
        for value in root.iter("LookupValue"):
            nome = (value.findtext("Name") or "").strip()
            value_id = (value.findtext("Value") or "").strip()
            if not nome or not value_id:
                continue
            nome_clean = nome.replace("NVIDIA", "").strip().lower()
            if nome_clean == gpu_name_clean:
                return int(value_id)
            if gpu_name_clean and (gpu_name_clean in nome_clean or nome_clean in gpu_name_clean):
                melhor_pfid = int(value_id)

        return melhor_pfid
    except Exception as e:
        log(f"Erro ao consultar lista de GPUs da NVIDIA: {e}")
        return None


def _check_latest_driver(pfid: int, timeout: int = 15):
    """Consulta o driver mais recente disponível pra esse pfid.
    Retorna dict com 'version'/'download_url'/'file_size', ou None."""
    params = {
        "func": "DriverManualLookup",
        "pfid": pfid,
        "osID": _get_os_id(),
        "languageCode": 1033,
        "beta": 0,
        "isWHQL": 0,
        "dltype": -1,
        "dch": 1,
        "upCRD": 0,
        "qnf": 0,
        "sort1": 0,
        "numberOfResults": 1,
    }
    try:
        resp = requests.get(DRIVER_SERVICE_URL, params=params, timeout=timeout)
        data = resp.json()
        ids = data.get("IDS", [])
        if not ids:
            return None
        info = ids[0]["downloadInfo"]
        return {
            "version": info.get("Version"),
            "download_url": info.get("DownloadURL"),
            "file_size": info.get("DownloadURLFileSize"),
        }
    except Exception as e:
        log(f"Erro ao consultar driver mais recente: {e}")
        return None


def check_for_update():
    """
    Fluxo completo: detecta a GPU, a versão atual, e compara com a
    versão mais recente disponível. Retorna um dict sempre com a
    chave 'error' (None se deu tudo certo) e as demais informações.
    """
    gpu_name, current_version = get_gpu_info()
    if not gpu_name:
        return {"error": "Nenhuma GPU NVIDIA detectada (ou nvidia-smi não encontrado nesta máquina)."}

    pfid = _find_pfid(gpu_name)
    if not pfid:
        return {"error": f"Não foi possível identificar '{gpu_name}' na base de dados da NVIDIA."}

    latest = _check_latest_driver(pfid)
    if not latest or not latest.get("version"):
        return {"error": "Não foi possível consultar o driver mais recente da NVIDIA agora."}

    try:
        tem_atualizacao = float(latest["version"]) > float(current_version)
    except (TypeError, ValueError):
        tem_atualizacao = latest["version"] != current_version

    return {
        "error": None,
        "gpu_name": gpu_name,
        "current_version": current_version,
        "latest_version": latest["version"],
        "download_url": latest["download_url"],
        "file_size": latest["file_size"],
        "has_update": tem_atualizacao,
    }


def download_and_install(download_url: str, progress_callback=None):
    """
    Baixa o instalador do driver e roda de forma silenciosa (sem
    janelas do instalador da NVIDIA aparecendo). Retorna (sucesso, mensagem).
    progress_callback(bytes_baixados, bytes_totais) é chamado durante o download.
    """
    if not download_url:
        return False, "URL de download inválida."

    try:
        dest = os.path.join(tempfile.gettempdir(), "ace_helper_nvidia_driver.exe")

        log(f"Baixando driver NVIDIA de {download_url}")
        with requests.get(download_url, stream=True, timeout=60) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            baixado = 0
            with open(dest, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    if not chunk:
                        continue
                    f.write(chunk)
                    baixado += len(chunk)
                    if progress_callback and total:
                        progress_callback(baixado, total)

        log("Download concluído, iniciando instalação silenciosa do driver...")
        result = subprocess.run(
            [dest, "-s", "-noreboot"],
            timeout=1800,
            creationflags=_NO_WINDOW_FLAGS
        )

        if result.returncode == 0:
            log("Driver NVIDIA instalado com sucesso.")
            return True, "Driver NVIDIA instalado com sucesso. Pode ser necessário reiniciar o PC."
        else:
            msg = f"Instalador do driver retornou código {result.returncode}."
            log(msg)
            return False, msg

    except FileNotFoundError:
        return False, "Não foi possível rodar o instalador (arquivo não encontrado)."
    except Exception as e:
        log(f"Erro ao baixar/instalar driver NVIDIA: {e}")
        return False, f"Erro ao baixar/instalar driver NVIDIA: {e}"
