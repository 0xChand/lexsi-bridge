---
language:
- en
- es
- ur
task_categories:
- text-generation
tags:
- safety
- multilingual
- evaluation
- over-refusal
size_categories:
- n<1K
pretty_name: Bridge multilingual safety and over-refusal pilot
configs:
- config_name: default
  data_files:
  - split: train
    path: benchmark.jsonl
- config_name: prospective
  data_files:
  - split: train
    path: prospective-benchmark.jsonl
---

# Bridge multilingual safety and over-refusal pilot

Bridge contains a 36-row exploratory pilot and an 18-row prospective challenge set in English, Spanish and Urdu. Each topic has a harmful-intent request and a related benign request. The rows are hand-authored; translations and labels have not been independently validated. The data is intended for research into whether language models handle harmful and benign requests differently across languages. It is not a representative sample of real-world usage and must not be used to claim a model is safe.

Each row has an `id`, `family`, `language`, `expected` (`refuse` or `answer`) and `prompt`. `expected` is the desired broad response class, not a complete annotation rubric. Language variants share scenarios, so rows are not independent samples. The pilot was visible during development. The prospective set contains three new topic families written after the original intervention was selected, but is public and has not been independently validated; it is not a representative private test set.

`pilot.jsonl` contains the source rows. `benchmark.jsonl` contains the CuratorKIT-cleaned rows evaluated in the accompanying run logs. `baseline.json` and `guided.json` contain generated outputs, settings, hashes, and unreviewed keyword-refusal indicators. These indicators are weak proxies: a refusal phrase may coexist with harmful information, a refusal may use different wording, and the marker lists have uneven language coverage. No human annotations are supplied.

`prospective-cases.jsonl` and `prospective-benchmark.jsonl` contain the source and cleaned prospective cases. `prospective-baseline.json` and `prospective-guided.json` contain the corresponding run logs. The fixed first-pilot instruction was used without modification. Keyword matches were 9/9 on harmful-intent requests and 0/9 on benign requests in each condition; these are detector outputs and do not demonstrate safety or improvement.

The logs were generated on 2 November 2026 using the public CohereLabs Tiny Aya Space, temperature 0.1, maximum 256 generated tokens. The Space's deployed model revision was not independently verified. The guided condition added a safety instruction; it did not modify model weights. See the [project repository](https://github.com/0xChand/lexsi-bridge) for the precise instruction, scoring, dataset generation and review workflow.

The prompts contain descriptions of harmful intent and the logs may contain sensitive or unsafe model responses. Restrict use to appropriate evaluation workflows. Independent expert review, native-speaker validation, additional topics, blind annotation and held-out evaluation are necessary before substantive conclusions.

The dataset was authored for the Lexsi AI Safety and Alignment Hackathon. Third-party tools and model outputs retain their respective terms. No license is asserted here pending a deliberate licensing choice by the dataset owner.
