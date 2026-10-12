# Frontier reference sheet, October 2026

The numbers quoted in the workshop's frontier module, with where each came from.
Researched 8 October 2026. Check the sources yourself; some will be out of date by the time you read this.

## Anthropic models

| Model | Positioned for | List price, $ per million tokens in / out |
|-------|----------------|-------------------------------------------|
| Fable 5.1 | demanding reasoning, long-horizon agentic work | 10 / 50 |
| Opus 5.5 | long-running agentic coding and knowledge work (recommended for most workloads) | 4 / 20 |
| Sonnet 5.5 | speed and intelligence balanced | 2 / 10 |
| Haiku 5.5 | high-volume, latency-sensitive tasks | from 0.10 / from 0.50 |

All four: 1M-token context, 128K output, reliable knowledge cutoff June 2026.
Source: https://platform.claude.com/docs/en/models/overview

Vendor benchmark figures (Anthropic model pages, Sep–Oct 2026):
- Opus 5.5: Terminal-Bench 4.0 66.4%; Humanity's Last Exam with tools 67.7%; Terminal-Bench-Science 0.1 58.7% (GPT-6 Astra 64.6%). https://www.anthropic.com/claude-opus-5-5
- Sonnet 5.5: Terminal-Bench 4.0 70.6%. https://www.anthropic.com/claude-sonnet-5-5

Availability: on 12 June 2026 a US export-control directive led Anthropic to suspend Fable 5 and Mythos 5; the controls were lifted on 30 June and access returned on 1 July. https://www.anthropic.com/news/fable-mythos-access and https://www.anthropic.com/news/redeploying-fable-5

## Other labs (from their own announcements)

- OpenAI: GPT-6 Astra; GPT-6 Sol and Luna. https://openai.com/index/gpt-6-astra/
- Google DeepMind: Gemini 4 Argon, staged access from 30 Sep 2026. https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-4-argon/
- xAI: Grok 4.7 (model card 21 Sep 2026).
- Mistral: Large 4 preview, 6 Oct 2026, weights promised by end of October. https://mistral.ai/news/mistral-large-4/
- DeepSeek: V4-Pro and V4-Flash previews with open weights, 24 Apr 2026. https://api-docs.deepseek.com/news/news260424/
- Alibaba: Qwen3.8-Max, 3 Aug 2026 (weight release not confirmed).
- Epoch Capabilities Index: GPT-6 Astra 166.3, Fable 5.1 164.5, intervals overlap. https://epoch.ai/data-insights/astra-eci-breakdown

## Measured capability and failure modes

- METR time horizon: doubling about every 89 days since 2024 (about 196 days over the full record); Claude Opus 4.5 about 5.3 h. https://metr.org/blog/2026-1-29-time-horizon-1-1/
- Claude Mythos Preview: at least 16 h, 95% interval 8.5–55 h (METR, May 2026).
- No published METR figure for Opus 5.5 or Fable 5.1 as of 8 Oct. https://metr.org/blog/2026-09-22-claude-opus-5-5/
- SWE-bench Verified retired as a headline benchmark (contamination, faulty tests). https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/
- About half of passing SWE-bench patches would not be merged. https://metr.org/notes/2026-03-10-many-swe-bench-passing-prs-would-not-be-merged-into-main/
- An estimated ~147,000 non-existent references in 2025 papers, from an audit of 111 million references. arXiv:2605.07723
- At least 16% of "successful" agent runs on tasks over 8 hours were illegitimate on review. https://metr.org/blog/2026-05-19-frontier-risk-report/

## AI in research

- Claude Science (beta, 30 Jun 2026): runs on HPC login nodes, connects to your cluster over SSH; figures carry their code and environment. https://www.anthropic.com/news/claude-science-ai-workbench
- DOE Genesis Mission commitment, 8 Oct 2026. https://www.anthropic.com/news/genesis-mission-commitment
- AI for Science credits and free Team seats for PIs, 27 Aug 2026. https://www.anthropic.com/news/expanding-support-for-scientists
- Canada: $10M CAD to eight institutions, July 2026. https://mila.quebec/en/news/mila-and-anthropic-announce-partnership-to-advance-ai-research-and-deep-tech-innovation-in

## Claude Code facts used in the labs

From https://code.claude.com/docs, read 8 Oct 2026: permission modes (`default`/Manual, `acceptEdits`, `plan`, `auto`, `dontAsk`, `bypassPermissions`); auto mode is the starting mode from v2.1.283; auto mode falls back to prompting after 3 consecutive or 20 total blocks; administrators disable it with `permissions.disableAutoMode`; model aliases `default`, `best`, `fable`, `opus`, `sonnet`, `haiku`, `opusplan`; effort levels `low` to `max` and `auto`.
