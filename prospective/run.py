"""Run a separate challenge set using the frozen first-pilot intervention."""
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
import bridge

experiment = root / 'prospective'
bridge.ROOT = experiment
bridge.SOURCE = experiment / 'cases.jsonl'
bridge.CURATED = experiment / 'curated' / 'benchmark.jsonl'
bridge.curate()
paths = []
for condition in ('baseline', 'guided'):
    out = experiment / 'results' / f'{condition}.json'
    bridge.run(bridge.hosted_space(condition), 'CohereLabs/tiny-aya-global (official hosted Space)',
               condition, out, generation={'temperature': 0.1, 'max_tokens': 256,
                                           'backend': 'CohereLabs/tiny-aya Space /generate'})
    paths.append(out)
bridge.report(paths)
