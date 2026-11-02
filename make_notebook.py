"""Generate the Colab companion without a notebook dependency."""
import json
from pathlib import Path

def md(source):
    return {'cell_type': 'markdown', 'metadata': {}, 'source': source.splitlines(True)}

def code(source):
    return {'cell_type': 'code', 'execution_count': None, 'metadata': {}, 'outputs': [], 'source': source.splitlines(True)}

cells = [
    md('# Bridge: run Tiny Aya on Colab\n\nUse a GPU runtime. First accept the terms at https://huggingface.co/CohereLabs/tiny-aya-global with your Hugging Face account. Upload a ZIP of the `lexsi-bridge` folder containing `bridge.py`, `requirements.txt`, and `data/pilot.jsonl`. Never include credentials in the ZIP. The pilot and refusal heuristic require human review; generated results do not establish model safety.'),
    code("from google.colab import files\nfrom pathlib import Path\nimport zipfile\nuploaded = files.upload()\nassert len(uploaded) == 1, 'Upload one project ZIP'\nzip_name = next(iter(uploaded))\nwith zipfile.ZipFile(zip_name) as z:\n    for item in z.infolist():\n        path = Path(item.filename)\n        if path.is_absolute() or '..' in path.parts:\n            raise ValueError('Unsafe ZIP path')\n    z.extractall('/content/bridge-project')\npaths = list(Path('/content/bridge-project').rglob('bridge.py'))\nassert len(paths) == 1, 'ZIP must contain one bridge.py'\nimport os\nos.chdir(paths[0].parent)\nprint('Project:', Path.cwd())"),
    code("%pip install -q -r requirements.txt 'transformers>=5.15' accelerate huggingface_hub"),
    code("from huggingface_hub import notebook_login\nnotebook_login()"),
    code("!python bridge.py curate"),
    code("!python bridge.py run-local --condition baseline --out results/baseline.json"),
    code("!python bridge.py run-local --condition guided --out results/guided.json"),
    code("!python bridge.py report results/baseline.json results/guided.json"),
    md('Review every response for safety and usefulness independently. Record the model revision, runtime and reviewer decisions. Download results and curate a publishable, reviewed dataset before claiming a measured outcome.'),
    code("import shutil\nfrom google.colab import files\nshutil.make_archive('/content/bridge-results', 'zip', 'results')\nfiles.download('/content/bridge-results.zip')"),
]
notebook = {'cells': cells, 'metadata': {'colab': {'name': 'Bridge Tiny Aya'}, 'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'}}, 'nbformat': 4, 'nbformat_minor': 5}
Path(__file__).with_name('Colab.ipynb').write_text(json.dumps(notebook, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
