# Run the local RAG critique

The critique CLI can search a collection of sources before sending evidence to Qwen3-4B through MLX. On ten answerable synthetic cases, MiniLM retrieved every labeled source in the top two for all ten. Lexical retrieval did so for nine. The Qwen verdicts favored lexical retrieval on this set.

## Setup and demo

Run these commands from the repository root on Apple Silicon macOS with [uv](https://docs.astral.sh/uv/getting-started/installation/) installed. The setup script creates a separate Python 3.12 environment in `runs/rag-venv`, installs the hash-locked dependencies, and prepares both pinned public models. First setup requires internet access. Use `./scripts/setup_rag.sh --offline` when the Python interpreter, packages, and both snapshots are cached.

```sh
./scripts/setup_rag.sh
rag_python=runs/rag-venv/bin/python

HF_HUB_OFFLINE=1 "$rag_python" -m writing_ftm \
  --input examples/rag-request.json --retriever semantic --retrieve-k 2 \
  --chunk-size 160 --chunk-overlap 32 --output runs/rag/my-semantic.json

HF_HUB_OFFLINE=1 "$rag_python" -m writing_ftm \
  --input examples/rag-request.json --retrieve-k 2 --output runs/rag/my-lexical.json
```

Choose a new output path for each run. Without `--retrieve-k`, the CLI passes all supplied sources to the critique engine. With `--retrieve-k`, it defaults to lexical search. The semantic demo retrieved `workshop` first. Qwen cited the voluntary attendance survey and recommended changing “caused” to “was associated with.” It also cited an unrelated tutorial. Inspect the saved event’s `retrieval`, `provider`, and `critique.evidence` fields. [Recorded live CLI event](../research/results/semantic-rag/live-demo.json)

## How a citation survives retrieval

LangChain splits each source with its original ID and character offset. MiniLM embeds the chunks on CPU into 384 dimensions. LangChain’s in-memory vector store ranks them by cosine similarity. Each document takes the score of its best chunk. Qwen receives the original passage and the full text of each selected document, once per ID. This lets it quote across a chunk boundary. The validator resolves each unique quote to a Python character range in that source and rejects unknown IDs, absent quotes, and ambiguous matches.

The index lives for one CLI request. The local JSON event records the query, ranked parents, matched chunks, model revisions, and quote offsets. For passages longer than MiniLM’s 256-token limit, supply a short `--retrieval-query`. To handle an oversized chunk, reduce `--chunk-size` and its overlap. The default parent context limit is 16,000 characters. An optional `--semantic-min-score` rejects weak cosine matches. The benchmark uses no threshold.

Setup checks ten files against pinned SHA-256 digests. The earlier failure came from expecting two modules in MiniLM’s manifest. Its third module, Normalize, has no weights of its own. The pinned manifest covers all three. For a checksum mismatch, run `runs/rag-venv/bin/python -m scripts.download_embeddings --force-download`. [Pinned MiniLM module manifest](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/blob/1110a243fdf4706b3f48f1d95db1a4f5529b4d41/modules.json)

## Retrieval results

Both methods used the passage as the query over the same ten fictional documents. The semantic index contained 15 chunks at 160 characters with up to 32 characters of overlap. The index contained source text only. Eight answerable passages required one source and two required two. A separate passage had no relevant source. [Synthetic corpus](../examples/rag-request.json) · [Passages and labels](../examples/rag-cases.json)

| Retrieval on answerable passages | Lexical | Semantic |
|---|---:|---:|
| Mean recall@1 | 0.70 | 0.90 |
| Mean recall@2 | 0.90 | 1.00 |
| All labeled sources in top two | 9/10 | 10/10 |

Recall is the fraction of each passage’s labeled sources retrieved, averaged across passages. A single result can recover at most half the evidence for each two-source passage. Lexical search missed the library ledger on the paraphrase about loan returns. MiniLM ranked it first. On the separate meteorite passage, lexical search returned zero sources. MiniLM returned two water studies with cosine scores around 0.11.

## Live critique results

With the top two documents, the same greedy Qwen model produced structurally valid, exact-quote critiques on all ten answerable passages in both conditions. Verdicts matched the authored labels for **9/10 lexical** and **8/10 semantic**. On the meteorite passage, lexical search stopped before generation. Qwen saw the two water studies under semantic retrieval and issued a `revise` verdict. We excluded this case from recall and verdict accuracy.

Both conditions missed the library verdict. With the ledger present, Qwen read “once” as a causal claim. On K71, only the semantic condition included the neighboring K17 report. Qwen challenged whether a shorter ride meant earlier arrival including wait time. The label treats the passage as describing the ride. These wording judgments limit what verdict accuracy can establish. The cases are small, synthetic, and lack independent review. [Per-case rankings, citations, verdicts, and rationales](../research/results/semantic-rag/paired.json)

## Reproduce the comparison

```sh
rag_python=runs/rag-venv/bin/python
HF_HUB_OFFLINE=1 "$rag_python" -m scripts.benchmark_rag --output runs/rag/my-rankings.json
HF_HUB_OFFLINE=1 "$rag_python" -m scripts.benchmark_rag --live --output runs/rag/my-paired.json
make test PYTHON="$rag_python"
```

The live report records the fixture hashes, chunking parameters, embedding and generator revisions, generation settings, and per-case prompt hashes. A fresh Python 3.12.14 environment rebuilt from the lock and local caches on an 18 GB M3 Pro reproduced the demo’s rankings, raw Qwen response, and citation offsets.
