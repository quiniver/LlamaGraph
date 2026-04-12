# LlamaGraph

A visualizer for `llama-bench` results from llama.cpp.

I built this tool because I kept running into the same problem: Most optimizers (like [llama-optimus](https://github.com/BrunoArsioli/llama-optimus)) do a great job at maximizing tokens per second (TG), but often destroy prompt processing speed (PP) in the process. After optimization the model sometimes feels painfully slow until the first token appears — especially on mid-range cards like the RTX 3060.

So I wanted a way to **see both PP and TG at the same time**, together with all the other parameters I’m testing (`--n-gpu-layers`, `--batch-size`, `--ubatch-size`, etc.), and easily compare different runs.

That’s what LlamaGraph does.

![LlamaGraph](banner800.jpg)

### What it does

- Loads one or more `llama-bench` CSV files
- Shows 2D and 3D plots of any parameters against performance
- Has a **right sidebar** where you can filter any dimension that is not currently shown on the axes (this turned out to be surprisingly powerful, especially in 2D)
- Lets you toggle PP / TG per file, normalize values, switch between different Z-modes, etc.
- Keeps the full 3D surface rendering with subdivision, error bars and projections from the old version

The interface is meant to be mostly self-explanatory after a bit of clicking around. A proper user guide will come later.

### Current status

This isn’t even a release yet. These are the first commits of the project.
It’s already working very well in my daily workflow and makes it much easier to find good compromises between PP and TG, rather than simply chasing the highest TG score.

### Future plans (maybe, no promises)

- Direct integration with `llama-optimizer` and `llama-optimus` so you can start new benchmark runs directly from LlamaGraph
- Smarter ways to fill data gaps with fewer total runs
- Support for other llama-bench output formats (JSON, JSONL, markdown, maybe SQL later)
- Better support for comparing PR performance improvements (many llama.cpp contributors already use llama-bench for that)