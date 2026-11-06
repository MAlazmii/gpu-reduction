#!/usr/bin/env python3
"""Plot recorded A100 measurements. Requires matplotlib; never overwrites outputs.
Usage: python3 scripts/plot_results.py NEW_DIRECTORY
"""
import json
from pathlib import Path
import statistics
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

ROOT = Path(__file__).resolve().parents[1]


def main():
    if len(sys.argv) != 2:
        raise SystemExit('Usage: plot_results.py NEW_DIRECTORY')
    output = Path(sys.argv[1])
    output.mkdir(parents=True, exist_ok=False)
    record = json.loads((ROOT / 'results/a100-validation.json').read_text())
    series = [('cpu', 'cpu_seconds', 'CPU · one thread', '#aebcca'),
              ('cuda', 'resident_seconds', 'GPU resident', '#57d9c2'),
              ('cuda', 'transfer_seconds', 'GPU + transfers', '#ffcc80')]
    sizes = record['checks']['benchmark']['sizes']
    values = {}
    for backend, field, _, _ in series:
        rows = []
        for n in sizes:
            run = next(r for r in record['measurements'] if r['raw']['backend'] == backend and r['raw']['n'] == n)
            samples = [s[field] for s in run['raw']['samples']]
            if len(samples) != 5 or any(v <= 0 for v in samples):
                raise ValueError('Expected five strictly positive measured samples')
            actual = (min(samples), statistics.median(samples), max(samples))
            saved = run['summary'][field]
            if actual != (saved['min'], saved['median'], saved['max']):
                raise ValueError('Stored summary does not match raw data')
            if any(s['sum'] != run['raw']['expected'] or
                   (backend == 'cuda' and s['transfer_sum'] != run['raw']['expected'])
                   for s in run['raw']['samples']):
                raise ValueError('Numerically invalid measurement')
            rows.append([v * 1000 for v in samples])
        values[field] = rows

    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 12,
                         'svg.hashsalt': 'gpu-reduction-a100-v1'})
    bg, ink, muted = '#111c26', '#f2f3eb', '#aebcca'
    fig = plt.figure(figsize=(12, 7.2), facecolor=bg)
    fig.text(.065, .93, 'GPU REDUCTION', color=ink, fontsize=29, weight='bold')
    fig.text(.065, .878, 'Transfers change the picture.', color=muted, fontsize=18)
    fig.text(.065, .821, 'NVIDIA A100 40 GB  /  observed timings, 6 November 2026', color='#57d9c2', fontsize=12)
    ax = fig.add_axes([.09, .235, .54, .5], facecolor=bg)
    for j, (_, field, label, color) in enumerate(series):
        rows = values[field]
        xs = [i + (j - 1) * .15 for i in range(len(sizes))]
        medians = [statistics.median(r) for r in rows]
        lower = [m - min(r) for m, r in zip(medians, rows)]
        upper = [max(r) - m for m, r in zip(medians, rows)]
        ax.errorbar(xs, medians, yerr=[lower, upper], fmt='o', markersize=7,
                    capsize=5, linewidth=1.7, color=color, label=label, zorder=3)
        for x, row in zip(xs, rows):
            ax.scatter([x + (k - 2) * .012 for k in range(len(row))], row,
                       s=13, color=color, alpha=.45, zorder=2)
    ax.set_yscale('log')
    ax.set_ylim(.008, 8)
    ax.set_xlim(-.4, 2.4)
    ax.set_xticks(range(len(sizes)), [f'{n:,}' for n in sizes])
    ax.set_xlabel('Array length', color=muted, labelpad=12)
    ax.set_ylabel('Elapsed time · ms · log scale', color=muted, labelpad=12)
    ax.set_yticks([.01, .1, 1, 5])
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f'{value:g}'))
    ax.tick_params(colors=muted, which='both')
    for side in ax.spines.values(): side.set_color('#394752')
    ax.grid(axis='y', which='major', color='#394752', alpha=.7)
    ax.legend(loc='upper left', frameon=False, labelcolor=ink, fontsize=10)

    fig.text(.70, .71, f'{sizes[-1]:,} values', color=ink, fontsize=17, weight='bold')
    fig.text(.70, .667, 'Median of five repetitions', color=muted, fontsize=11)
    for y, (_, field, label, color) in zip([.57, .445, .32], series):
        median = statistics.median(values[field][-1])
        fig.text(.70, y, f'{median:.3f} ms', color=color, fontsize=25, weight='bold')
        fig.text(.70, y - .038, label, color=muted, fontsize=12)

    fig.text(.065, .133, 'Large markers: median   ·   Whiskers: min–max   ·   Small dots: raw repetitions', color=ink, fontsize=10)
    fig.text(.065, .094, 'Float32 inputs / float64 sums. Setup and allocation excluded; transfers use pageable host memory.', color=muted, fontsize=9)
    fig.text(.065, .064, 'One recorded run; CPU model and clock/contention controls not captured. No general speedup claim.', color=muted, fontsize=9)
    fig.text(.065, .034, 'Source: results/a100-validation.json   ·   implementation 71a3fe7', color=muted, fontsize=9)
    fig.savefig(output / 'a100-timings.png', dpi=170, facecolor=bg)
    fig.savefig(output / 'a100-timings.svg', facecolor=bg, metadata={'Date': None})
    plt.close(fig)
    print(output / 'a100-timings.png')


if __name__ == '__main__':
    main()
