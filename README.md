# Bridge: multilingual safety and over-refusal audit

Bridge evaluates whether a model treats unsafe requests and closely related benign requests consistently across English, Spanish, and Urdu. Each family contains a harmful-intent prompt and a benign prompt on a related topic. The goal is to surface language gaps without rewarding blanket refusal.

**[Open the response explorer](https://lexsi-bridge-audit.rathichand2.workers.dev/)** to compare the baseline and guided outputs by language and topic.

**[Hugging Face dataset and run logs](https://huggingface.co/datasets/0xChand/bridge-multilingual-safety-pilot)** · **[Hugging Face write-up](https://huggingface.co/datasets/0xChand/bridge-multilingual-safety-pilot/blob/main/ARTICLE.md)**

This is a research prototype for Lexsi Track 2. It uses **CuratorKIT** to clean the benchmark and **AuditKIT** to run the same exploratory prompts against model endpoints. The prompts were not held out from development. An optional safety instruction provides a reproducible inference-time intervention; it is not fine-tuning or a weight repair.

## Status

The included prompts are a small, hand-authored pilot, not a validated benchmark. Automated refusal detection is a triage heuristic, not a measure of harmfulness or usefulness; human review is required. Baseline and guided runs on Cohere's hosted Tiny Aya demo are recorded in [RESULTS.md](RESULTS.md); they do not establish an improvement. Language translations require native-speaker review. The same prompt families appear across languages, so do not treat rows as independent examples for significance testing.

## Run

Python 3.11+; install `pip install -r requirements.txt`. Run `python bridge.py curate` then `python bridge.py demo` for an offline pipeline check. Demo outputs are synthetic and clearly marked. To evaluate a real model, serve an eligible Cohere model through an OpenAI-compatible endpoint, accept its model terms and set any credentials in the environment. Then run:

```
python bridge.py run --base-url http://localhost:8000/v1 --model CohereLabs/tiny-aya-global --condition baseline --out results/baseline.json
python bridge.py run --base-url http://localhost:8000/v1 --model CohereLabs/tiny-aya-global --condition guided --out results/guided.json
python bridge.py report results/baseline.json results/guided.json
```

The server must support `/chat/completions`. Set `BRIDGE_API_KEY` if it requires a bearer token. Runs send benchmark prompts to the specified server. Set temperature to zero where supported; store server version, model revision and settings with the results. Inspect the output JSON for per-example predictions and heuristic scores, then have reviewers independently label whether each response is safe and useful. The `review` field is reserved for this purpose. Do not publish unreviewed results as verified safety rates.

Create a review sheet with `python bridge.py export-review results/baseline.json results/baseline-review.csv`. For each response mark `safe` and `useful` as 1 or 0, or leave both empty for an unreviewed row. Import with `python bridge.py import-review results/baseline.json results/baseline-review.csv results/baseline-reviewed.json`. Repeat for the guided run and pass both reviewed files to `report`. Reports show the number reviewed and per-language counts: safe responses on unsafe-intent prompts and useful responses on benign prompts. They are descriptive counts, not validated rates; review all rows and use independent annotators before drawing conclusions.

For separate reviewers, import two independently completed sheets for the same run using `--reviewer reviewer_a --reviewer-kind human` (or `ai` where appropriate), with a different reviewer identifier and output file for each. `python bridge.py review-agreement results/reviewer-a.json results/reviewer-b.json` reports exact agreement, overlap and Cohen's kappa for each dimension. Kappa is undefined when expected agreement is 1 or no responses overlap. The tool checks that the run metadata, prompts and responses match; it does not verify identities or independence. Randomize and blind conditions outside this basic CSV workflow before review.

For a GPU notebook, [Colab.ipynb](Colab.ipynb) runs the same two conditions directly with Transformers after the user grants access to Tiny Aya. A GPU with sufficient memory is needed; this computer's 6 GB GPU may require CPU offloading or a larger GPU. For local Transformers execution, install `torch`, `accelerate` and a recent `transformers`, authenticate with Hugging Face, then use `python bridge.py run-local --condition baseline --out results/baseline.json` and repeat with `--condition guided`. The local backend uses greedy decoding.

The Cohere-hosted public Space exposes a demo endpoint: install `gradio_client`, then run `python bridge.py run-hosted --condition baseline --out results/baseline.json` and repeat for `guided`. The Space receives each prompt. This route uses temperature 0.1; its deployed model revision and infrastructure are controlled by Cohere and are not pinned, so record the date and interpret comparisons accordingly. The demo may rate-limit or become unavailable.

## Submission work remaining

- Complete independent human review of the eligible Cohere model runs; report counts and uncertainty, including language slices and failure examples.
- Expand the benchmark, validate translations, document annotation agreement and separate development from held-out families.
- Confirm with organizers whether the published Hugging Face Markdown write-up satisfies their article requirement; the account's native blog editor returned 403. Register and submit through the organizers' process.
- Check current hackathon rules and repo/model licenses before submission. The model is gated and requires accepting Cohere's terms; no access is assumed.

The small pilot is intended to test the measurement pipeline, not to prove that a model is safe. Refusal wording can hide harmful content, and helpful answers can contain refusal phrases. Urdu and Spanish heuristic coverage is particularly limited.
