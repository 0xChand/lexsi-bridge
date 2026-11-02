# Bridge: auditing safety and over-refusal across languages

A safety instruction can change a model's tone without reliably improving its behavior. Bridge is a small, reproducible pilot for testing that question in English, Spanish and Urdu while also checking for refusals of benign requests.

## The question

Does a short safety instruction improve the balance between safe handling of harmful-intent requests and useful answers to related benign requests across languages? We treat this as an exploratory question, not a certification of model safety.

## Pipeline

We wrote 36 prompts across six topics. Each topic has one harmful-intent request and a related benign request in each of three languages. CuratorKIT cleaned and deduplicated the source rows; AuditKIT ran the resulting prompts through Cohere Labs' public Tiny Aya Space. The baseline used only the user prompt. The guided condition added a safety instruction asking for refusals of harmful requests and helpful answers to benign ones. Both used temperature 0.1 and a maximum of 256 generated tokens. The hosted Space controls its model revision, which we did not independently verify.

The intervention changes the instruction at inference time; it does not fine-tune or repair model weights. The dataset was visible during project development and has no held-out set. The language variants share scenarios and should not be counted as independent observations.

## What we observed

An intentionally simple keyword heuristic identified refusal language in 17 of 18 harmful-intent responses in the baseline and 15 of 18 in the guided condition. On benign requests, it identified refusal language in 0 of 18 baseline responses and 1 of 18 guided responses. At language level, harmful-intent matches for English, Spanish and Urdu were 5/6, 6/6 and 6/6 at baseline and 5/6, 5/6 and 5/6 with guidance. Benign matches were 0/6 for each language at baseline and 1/6, 0/6 and 0/6 with guidance.

These numbers are keyword matches, not verified safety or usefulness metrics. A refusal can use wording outside the marker list, or can include a refusal and then still provide harmful information. The markers differ by language. There is one sampled response per condition, no independent human review and no native-speaker validation of the translations. The pilot therefore does **not** demonstrate that the instruction improves safety or that the model is safe.

## Reproduce and review

The [Bridge repository](https://github.com/0xChand/lexsi-bridge) contains the benchmark, CuratorKIT and AuditKIT pipeline, generation logs, comparison command and a CSV review workflow. The [response explorer](https://lexsi-bridge-audit.rathichand2.workers.dev/) makes each pair of outputs inspectable. The accompanying dataset package includes the source and curated prompts and raw logs. Reviewers can assess safety and usefulness separately and document explanations without relying on refusal keywords.

The next stage is blind review by independent reviewers, native-speaker validation, a larger and more diverse set of scenarios, a pinned model revision, repeated samples, and families held out before choosing an intervention. The reported pilot is a starting point for that work, with its negative and inconclusive results preserved rather than presented as a model improvement.
