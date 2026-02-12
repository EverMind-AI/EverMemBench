# Multi-Person Group Chat Evaluation Framework

[![arXiv](https://img.shields.io/badge/arXiv-2602.01313-b31b1b.svg)](https://arxiv.org/pdf/2602.01313)
[![Dataset](https://img.shields.io/badge/🤗%20Dataset-EverMemBench--Dynamic-yellow)](https://huggingface.co/datasets/EverMind-AI/EverMemBench-Dynamic)

A comprehensive evaluation framework for multi-person group chat datasets, supporting **Memory Systems** (Memos, Mem0, Memobase, EverMemOS, Zep) and **LLM Long-Context Evaluation**.

📄 **Paper**: [EverMemBench: A Comprehensive Benchmark for Long-Term Memory in Conversational AI](https://arxiv.org/pdf/2602.01313)

🤗 **Dataset**: [EverMind-AI/EverMemBench-Dynamic](https://huggingface.co/datasets/EverMind-AI/EverMemBench-Dynamic)

## Features

- **Multi-person group chat support**: Handles datasets with multiple speakers across multiple groups and days
- **5 Memory Systems**: Memos, Mem0, Memobase, EverMemOS, Zep (Graph API)
- **LLM Long-Context Evaluation**: Direct LLM evaluation using full dialogue as context
- **Full Evaluation Pipeline**: Add → Search → Answer → Evaluate
- **Two Question Types**: Multiple choice (direct comparison) and open-ended (LLM judge)
- **Unified message format**: All messages include group/speaker attribution
- **LLM Integration**: Uses OpenRouter for answer generation and evaluation
- **Batch processing**: Efficient API calls with configurable batch sizes and rate limiting
- **Smoke test mode**: Quick validation with limited data

## Pipeline Stages

```
┌─────────┐    ┌──────────┐    ┌──────────┐    ┌───────────┐
│   Add   │ -> │  Search  │ -> │  Answer  │ -> │ Evaluate  │
└─────────┘    └──────────┘    └──────────┘    └───────────┘
     │              │               │               │
     v              v               v               v
  Ingest       Retrieve LLM      Generate       Assess
 memories     memories        answers       accuracy
```

| Stage | Description | Output |
|-------|-------------|--------|
| **Add** | Ingest conversation data into memory system | - |
| **Search** | Retrieve relevant memories for QA questions | `search_results_{user_id}.json` |
| **Answer** | Generate answers using LLM with retrieved context | `answer_results_{user_id}.json` |
| **Evaluate** | Assess answer quality (MC: direct, OE: LLM judge) | `evaluation_results_{user_id}.json` |

## Supported Systems

### Memory Systems

| System | Timestamp Support | Message Format | Environment Variables |
|--------|-------------------|----------------|----------------------|
| **Memos** | Native `chat_time` | `[Group: X][Speaker: Y]content` | `MEMOS_API_KEY`, `MEMOS_BASE_URL` |
| **Mem0** | Native `timestamp` (Unix, per-batch) | `run_id="${user_id}_${groupId}"`, `name=<Speaker>` | `MEM0_API_KEY` |
| **Memobase** | Native `created_at` | `[Group: X][Speaker: Y]content`, `alias=<Speaker>` | `MEMOBASE_BASE_URL`, `MEMOBASE_API_TOKEN` |
| **EverMemOS** | Native `create_time` | `sender=<Speaker>`, `group_id=${user_id}_${groupId}` | `EVERMEMOS_BASE_URL`, `EVERMEMOS_API_KEY` |
| **Zep** | Graph `created_at` | `[Group: X][Speaker: Y]content` | `ZEP_API_KEY` |

### LLM System

| System | Context | Use Case | Environment Variables |
|--------|---------|----------|----------------------|
| **LLM** | Full dialogue (no retrieval) | Test LLM long-context comprehension | `LLM_BASE_URL`, `LLM_API_KEY` |

**Key Differences: Memory Systems vs LLM System**

| Aspect | Memory Systems | LLM System |
|--------|---------------|------------|
| Context | Retrieved memories (top-k) | Full dialogue |
| Add Stage | Ingest into memory system | No-op (stores dialogue) |
| Search Stage | Query memory system | Returns full dialogue |
| Answer Stage | Answer with retrieved context | Answer with full dialogue |
| Use Case | Test memory retrieval | Test LLM long-context |

## Directory Structure

```
eval/
├── cli.py                    # CLI entry point
├── config/
│   ├── memos.yaml           # Memos configuration
│   ├── mem0.yaml            # Mem0 configuration
│   ├── memobase.yaml        # Memobase configuration
│   ├── evermemos.yaml       # EverMemOS configuration
│   ├── zep.yaml             # Zep configuration
│   ├── llm.yaml             # LLM system configuration (model/provider/warmup/concurrency/retry)
│   └── prompts.yaml         # LLM prompts for answer/evaluate
├── src/
│   ├── core/
│   │   ├── data_models.py   # Data classes (QAItem, SearchResult, etc.)
│   │   ├── loaders.py       # Dataset loading utilities
│   │   ├── qa_loader.py     # QA data loader
│   │   ├── pipeline.py      # Evaluation pipeline orchestrator
│   │   ├── answerer.py      # Answer generation with LLM
│   │   └── evaluator.py     # Evaluation with LLM judge
│   ├── adapters/
│   │   ├── base.py          # Base adapter abstract class
│   │   ├── memos_adapter.py # Memos implementation
│   │   ├── mem0_adapter.py  # Mem0 implementation
│   │   ├── memobase_adapter.py   # Memobase implementation
│   │   ├── evermemos_adapter.py  # EverMemOS implementation
│   │   ├── zep_adapter.py   # Zep Graph API implementation
│   │   └── llm_adapter.py   # LLM system adapter (full dialogue as context)
│   └── utils/
│       ├── config.py        # YAML config loader with env var support
│       └── logger.py        # Rich console logging
├── results/                  # Output files
└── README.md
```

## Installation

```bash
# Core dependencies
pip install aiohttp aiolimiter rich pyyaml python-dotenv openai

# System-specific SDKs
pip install mem0ai           # For Mem0
pip install memobase         # For Memobase
pip install zep-cloud        # For Zep
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# ===== Memory Systems =====

# Memos
MEMOS_API_KEY=Token mpg-your-key-here
MEMOS_BASE_URL=https://memos.memtensor.cn/api/openmem/v1

# Mem0
MEM0_API_KEY=your-mem0-api-key

# Memobase
MEMOBASE_BASE_URL=https://api.memobase.dev
MEMOBASE_API_TOKEN=your-memobase-token

# EverMemOS (EverMind)
EVERMEMOS_BASE_URL=https://api.evermind.ai
EVERMEMOS_API_KEY=your-evermemos-api-key

# Zep
ZEP_API_KEY=your-zep-api-key

# ===== LLM (OpenRouter) =====
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_API_KEY=your-openrouter-api-key
```

### LLM Configuration

LLM **runtime settings** (model/provider routing, warmup, concurrency, retry) are in `eval/config/llm.yaml`.
LLM **prompt templates** are in `eval/config/prompts.yaml`.

```yaml
# eval/config/llm.yaml (runtime settings)
llm:
  model: "google/gemini-3-flash-preview"  # OpenRouter model ID
  provider:
    order: ["google-vertex"]              # lock provider to ensure cache hits
    allow_fallbacks: false
  temperature: 0
  max_tokens: 1000

# Warmup Configuration (for LLM system)
warmup:
  enabled: true
  delay_seconds: 5              # Wait after first request

# Concurrency Configuration
concurrency:
  answer_concurrency: 3         # Lower concurrency = better cache hits
  evaluate_concurrency: 20

# Retry Configuration
retry:
  max_retries: 3
  retry_delay: 1.0
  max_delay: 30.0

# Debug Configuration
debug:
  show_usage: true              # Show token usage and cache details
```

```yaml
# eval/config/prompts.yaml (prompt templates)
llm_answer:
  multiple_choice: |
    ...
  open_ended: |
    ...
llm_judge:
  system_prompt: |
    ...
  user_prompt: |
    ...
```

## Usage

### Memory Systems Evaluation

```bash
# Run all stages: search -> answer -> evaluate
python -m eval.cli \
    --dataset dataset/004/dialogue_en.json \
    --qa dataset/004/qa_004.json \
    --system mem0 \
    --user-id 004 \
    --stages search answer evaluate \
    --top-k 10
```

### LLM Long-Context Evaluation

The LLM system evaluates **long-context dialogue understanding** by using the **full dialogue** as context (no memory retrieval).

```bash
python -m eval.cli \
    --dataset dataset/004/dialogue_en.json \
    --qa dataset/004/qa_004.json \
    --system llm \
    --user-id 004 \
    --stages answer evaluate
```

### Individual Stages

```bash
# Add stage only
python -m eval.cli --dataset dataset/004/dialogue_en.json --system memos --stages add

# Add stage only (for Mem0 + graph mode)
# First set eval/config/mem0.yaml: enable_graph_add: true
python -m eval.cli \
    --dataset dataset/004/dialogue_en.json \
    --system mem0 \
    --user-id 004 \
    --stages add


# Search stage only
python -m eval.cli \
    --dataset dataset/004/dialogue_en.json \
    --qa dataset/004/qa_004.json \
    --system mem0 \
    --user-id 004 \
    --stages search

# Answer stage (requires search results)
python -m eval.cli \
    --dataset dataset/004/dialogue_en.json \
    --qa dataset/004/qa_004.json \
    --system mem0 \
    --user-id 004 \
    --stages answer

# Evaluate stage (requires answer results)
python -m eval.cli \
    --dataset dataset/004/dialogue_en.json \
    --qa dataset/004/qa_004.json \
    --system mem0 \
    --user-id 004 \
    --stages evaluate
```

### Smoke Test

```bash
# Smoke test add stage
python -m eval.cli --dataset dataset/004/dialogue_en.json --system memos --smoke

# Smoke test with specific date
python -m eval.cli --dataset dataset/004/dialogue_en.json --system memos --smoke --smoke-date 2025-01-16

# LLM smoke test with limited questions
python -m eval.cli \
    --dataset dataset/004/dialogue_en.json \
    --qa dataset/004/qa_004.json \
    --system llm \
    --user-id 004 \
    --stages answer evaluate \
    --qa-limit 3
```

## CLI Options

| Option | Description | Default |
|--------|-------------|---------|
| `--dataset` | Path to dataset JSON file | Required |
| `--system` | System (memos/mem0/memobase/evermemos/zep/llm) | Required |
| `--stages` | Stages to run: add, search, answer, evaluate | `["add"]` |
| `--qa` | Path to QA JSON file (required for search/answer/evaluate) | - |
| `--user-id` | User ID for memory system | Auto-generated |
| `--top-k` | Number of memories to retrieve | 10 |
| `--output-dir` | Results output directory | `eval/results` |
| `--smoke` | Enable smoke test mode | False |
| `--smoke-days` | Days to process in smoke test | 1 |
| `--smoke-date` | Specific date for smoke test (YYYY-MM-DD) | - |
| `--qa-limit` | Limit number of QA questions (for LLM smoke test) | - |

## Mem0 Knowledge Graph (Optional)

Mem0 supports a knowledge graph mode that extracts **entities and relationships** during ingestion and can optionally use graph-aware search.

Enable it via `eval/config/mem0.yaml`:

```yaml
enable_graph_add: true      # Extract entities/relations during add()
enable_graph_search: true   # Use graph-aware search during search()
```

Notes for graph add in this repo:
- Graph add sends one message per API call (no batching).
- The speaker is passed as `user_id` and the message payload only includes `role`/`content`.

Official examples:

```python
# Disable graph
client.add("Emma is a software engineer", user_id="company_kb")

# Enable graph - extracts entities and relations
client.add("Emma works with David", user_id="company_kb", enable_graph=True)

# Normal vector search
results = client.search("What does Emma do?", filters={"user_id": "company_kb"})

# Graph search - returns relationship-aware results
results = client.search(
    "Who is Emma's teammate?",
    filters={"user_id": "company_kb"},
    enable_graph=True
)
```

## LLM System Details

### Memory Optimization

The LLM system uses **memory-efficient processing** to handle large dialogues:

**Problem**:
- Full dialogue context can be ~3MB (e.g., 254 days, 10,222 messages)
- Without optimization, each of 627 questions would store the full context
- This could lead to high memory usage during processing

**Solution**:
- **Shared Context**: Single context string referenced by all questions
- **LightAnswerResult**: Lightweight result object without context storage
- **Immediate Cleanup**: Search results cleared after context extraction

```
📦 Shared context: 2.82 MB (memory-efficient mode)
```

| Item | Without Optimization | With Optimization |
|------|---------------------|-------------------|
| Context copies | N (one per question) | 1 (shared) |
| SearchResult objects | N × ~100 bytes | 1 (reused) |
| AnswerResult.search_result | N × reference | 0 (LightAnswerResult) |
| Peak memory | ~3MB × N | ~3MB (constant) |

### Cache Optimization

#### 1. Provider Configuration (CRITICAL!)

**Why it matters**: OpenRouter aggregates multiple providers. Without explicit provider config, your requests may be routed to different backends, **breaking cache entirely**.

```yaml
llm:
  model: "google/gemini-3-flash-preview"

  # CRITICAL: Lock requests to a single provider
  provider:
    order:
      - "google-vertex"       # Or other OpenRouter provider IDs
    allow_fallbacks: false    # Prevent automatic routing to other providers
```

> Provider 的可选值以 OpenRouter 文档为准；这里用 `google-vertex` 作为示例。

#### 2. Warmup Phase

The first request warms the cache before batch processing:

```
🔥 Warmup Phase: Sending first request to warm cache...
   📊 Usage: prompt=718279, completion=3, cached=716769
   ⏳ Waiting 5s for cache propagation...
   ✅ Warmup complete, starting batch processing
```

#### 3. Cache Hit Tracking

With `debug.show_usage: true`, you can see detailed cache info:

```
📊 Usage: prompt=718279, completion=3, cached=716769
📊 Usage: prompt=718291, completion=2, cached=716769
📊 Usage: prompt=718280, completion=17, cached=0

Cache: 2/3 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 3/3
📊 Cache Statistics: 2/3 hits (66.7%)
```

**Key insights**:
- `cached=716769` means 716,769 tokens were served from cache
- The `cached=0` request indicates a cache miss for that request

#### 4. Concurrency Trade-off

Lower concurrency can improve cache hit stability:

```yaml
concurrency:
  answer_concurrency: 3    # Lower = more cache hits, slower overall
```

### LLM System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      CLI (--system llm)                      │
├─────────────────────────────────────────────────────────────┤
│                        LLM Adapter                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ add() no-op │  │ search()    │  │ Full dialogue       │  │
│  │ Store data  │→ │ Return full │→ │ as context string   │  │
│  └─────────────┘  │ dialogue    │  └─────────────────────┘  │
│                   └─────────────┘                            │
├─────────────────────────────────────────────────────────────┤
│                        Pipeline                              │
│  ┌─────────┐   ┌─────────┐   ┌──────────┐   ┌───────────┐  │
│  │ Warmup  │ → │ Answer  │ → │ Evaluate │ → │  Results  │  │
│  │ (5s)    │   │ (batch) │   │ (judge)  │   │  (.json)  │  │
│  └─────────┘   └─────────┘   └──────────┘   └───────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### LLM Output

Results are saved to `eval/results/llm/`:

| File | Description |
|------|-------------|
| `evaluation_results_{user_id}.json` | Final accuracy scores and detailed results |

> **Note**: Unlike memory systems, the LLM system only saves the final evaluation results. Intermediate files (`search_results`, `answer_results`) are skipped to reduce disk usage since the full dialogue context would make them very large.

**Example Output**:

```
============================================================
📊 Pipeline Summary
============================================================
Add Stage: ✅ Success
  Days Processed: 254
  Messages Sent: 0
Search Stage: ✅ 627 queries
Answer Stage: ✅ 627 answers
Evaluate Stage: ✅ Accuracy: 85.33%

Total Time: 1234.56s
============================================================
```

## Data Formats

### QA Input Format

```json
{
  "questions": [
    {
      "question_id": "004_mc_001",
      "question": "What standard was suggested for the Carbon Emission project?",
      "options": ["A. ISO 14064", "B. GHG Protocol", "C. Both", "D. None"],
      "correct_option": "B",
      "answer": "GHG Protocol"
    },
    {
      "question_id": "004_oe_001",
      "question": "What project did Weihua Zhang launch on January 9th?",
      "answer": "Carbon Emission Accounting and Asset Management Platform"
    }
  ]
}
```

### Search Results Output

```json
{
  "question_id": "004_mc_001",
  "query": "What standard was suggested...",
  "retrieved_memories": ["memory1", "memory2", ...],
  "context": "Formatted context for LLM...",
  "search_duration_ms": 1234.5,
  "metadata": {...}
}
```

### Evaluation Results Output

```json
{
  "total_questions": 2,
  "correct": 1,
  "accuracy": 0.5,
  "accuracy_by_type": {
    "multiple_choice": {"total": 1, "correct": 1, "accuracy": 1.0},
    "open_ended": {"total": 1, "correct": 0, "accuracy": 0.0}
  },
  "detailed_results": [...]
}
```

## Search API Details

### Memos
- Endpoint: `POST {api_url}/product/search`
- Payload: `{query, user_id, mem_cube_id, top_k, include_preference: True}`
- Returns: `data.text_mem[0].memories` + `data.pref_mem[0].memories`

### Mem0
- Uses `client.search(query, top_k, filters={...})`
- Filters: `{"AND": [{"user_id": "*"}, {"run_id": {"in": ["004_1", "004_2", "004_3"]}}]}`

### Memobase
- Uses `user.context(max_token_size, chats=[{"role": "user", "content": query}])`
- Returns context string directly

### Zep
- Uses `client.graph.search(graph_id=user_id, query, scope="edges/nodes")`
- Returns facts and entity summaries

### EverMemOS
- Endpoint: `POST {base_url}/api/v1/memories/search`
- Payload: `{query, group_id, top_k}`

## Postman API Examples

### Memos - Search

```bash
curl -X POST "${MEMOS_BASE_URL}/product/search" \
  -H "Content-Type: application/json" \
  -H "Authorization: ${MEMOS_API_KEY}" \
  -d '{
    "query": "What was discussed about carbon emissions?",
    "user_id": "004",
    "mem_cube_id": "004",
    "top_k": 10,
    "include_preference": true
  }'
```

### Mem0 - Search with Filters

```bash
curl -X POST "https://api.mem0.ai/v1/memories/search" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${MEM0_API_KEY}" \
  -d '{
    "query": "What project was launched?",
    "top_k": 10,
    "filters": {
      "AND": [
        {"user_id": "*"},
        {"run_id": {"in": ["004_1", "004_2", "004_3"]}}
      ]
    }
  }'
```

### Zep - Graph Search

```bash
# Search edges (facts)
curl -X POST "https://api.getzep.com/api/v2/graph/004/search" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${ZEP_API_KEY}" \
  -d '{
    "query": "What was the project name?",
    "scope": "edges",
    "limit": 10,
    "reranker": "cross_encoder"
  }'

# Search nodes (entities)
curl -X POST "https://api.getzep.com/api/v2/graph/004/search" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${ZEP_API_KEY}" \
  -d '{
    "query": "Weihua Zhang",
    "scope": "nodes",
    "limit": 5
  }'
```

### EverMemOS - Search

```bash
curl -X POST "${EVERMEMOS_BASE_URL}/api/v1/memories/search" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${EVERMEMOS_API_KEY}" \
  -d '{
    "query": "What was discussed today?",
    "group_id": "004_1",
    "top_k": 10
  }'
```

### EverMemOS - Add Memory

```bash
curl -X POST "${EVERMEMOS_BASE_URL}/api/v1/memories" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${EVERMEMOS_API_KEY}" \
  -d '{
    "content": "Discussion about technical solution",
    "create_time": "2025-01-15T10:00:00+00:00",
    "group_id": "004_1",
    "message_id": "msg_00001",
    "role": "user",
    "sender": "alice",
    "sender_name": "Alice"
  }'
```

## Troubleshooting

### Missing Environment Variables

```
❌ Missing environment variables for mem0:
   - MEM0_API_KEY

Please set these in your .env file or environment.
```

### LLM API Key Required

```
❌ LLM_API_KEY environment variable required for answer/evaluate stages
Please set LLM_API_KEY in your .env file (OpenRouter API key)
```

### Module Not Found

```bash
pip install mem0ai memobase zep-cloud openai
```

### Context Too Long (LLM System)

If the dialogue exceeds model context limits, consider:

1. Use a model with larger context window
2. Use `--smoke-days` to limit dialogue to specific days
3. Use `--smoke-date` for single-day testing

```bash
# Test with single day
python -m eval.cli --system llm ... --smoke --smoke-date 2025-01-09
```

### Low Cache Hit Rate - 0% (LLM System)

If cache hits are 0%, check:

1. **Provider not configured**: Most common issue! Add explicit `provider.order` in `llm.yaml`
2. **Warmup disabled**: Ensure `warmup.enabled: true`
3. **High concurrency**: Reduce `answer_concurrency` to 1-3

```yaml
# Fix for 0% cache hits
llm:
  provider:
    order: ["google-vertex"]  # Lock to single provider!
    allow_fallbacks: false

warmup:
  enabled: true
  delay_seconds: 5

concurrency:
  answer_concurrency: 3          # Lower = better cache hits
```

### Low Cache Hit Rate - <50% (LLM System)

If cache hits are low but not zero:

1. **Provider inconsistency**: Even with config, some requests may route differently
2. **Concurrent request timing**: Requests may start before cache propagates
3. **Model string mismatch**: Ensure exact same model string everywhere

Enable debug mode to see actual cache data:
```yaml
debug:
  show_usage: true
```

## Dataset Batches

Supported user IDs: `004`, `005`, `010`, `011`, `016`

Each batch has:
- `dataset/{batch_id}/dialogue_en.json` - Conversation data
- `dataset/{batch_id}/qa_{batch_id}.json` - QA questions for evaluation

## Comparison: Memory Systems vs LLM

Run the same evaluation with different systems to compare:

```bash
# LLM (full dialogue)
python -m eval.cli --system llm --dataset ... --qa ... --stages answer evaluate

# Memory systems (retrieved context)
python -m eval.cli --system mem0 --dataset ... --qa ... --stages search answer evaluate
python -m eval.cli --system zep --dataset ... --qa ... --stages search answer evaluate
python -m eval.cli --system memos --dataset ... --qa ... --stages search answer evaluate
```
