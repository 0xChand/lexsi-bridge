# Submission notes

**Status: research pilot; registration and final submission are not yet verified.**

- Track: AI Red Teaming, Safety and Alignment, specifically a multilingual safety and over-refusal benchmark.
- Code and reproduction: https://github.com/0xChand/lexsi-bridge
- Public response explorer: https://lexsi-bridge-audit.rathichand2.workers.dev/
- Dataset and raw logs: https://huggingface.co/datasets/0xChand/bridge-multilingual-safety-pilot
- Write-up hosted on Hugging Face: https://huggingface.co/datasets/0xChand/bridge-multilingual-safety-pilot/blob/main/ARTICLE.md
- Lexsi tools used together: CuratorKIT for cleaning and deduplication, AuditKIT for model evaluation and predictions.
- Model: Cohere's hosted Tiny Aya Space; its exact deployed revision was not independently confirmed.

The run includes 36 prompts in three languages, each evaluated under baseline and guided conditions. Refusal-keyword counts and their limitations are documented in [RESULTS.md](RESULTS.md). **No model safety improvement has been demonstrated.** The data is a small exploratory pilot, it was not held out during development, and it has not been independently annotated or validated by native speakers. These limitations must accompany any submission.

The organizers request a Hugging Face Article. The account's native blog editor returned HTTP 403, so the write-up is hosted as a Markdown file in the dataset repository. Whether that satisfies the organizers' exact requirement is unconfirmed. The organizers also ask for evidence of meaningful improvement; the current pilot does not establish it. Registration, organizer acceptance, and final submission must be verified separately.
