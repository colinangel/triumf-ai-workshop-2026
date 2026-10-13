# Security in the agent era: reference sheet (October 2026)

Every fact in the Day 2 security talk, with its source. Read on 9 October 2026.
Forecasts are marked as forecasts.

## 1. The OpenAI and Hugging Face incident, May to July 2026

| Date (2026) | What happened | Source |
|---|---|---|
| 12 May | An OpenAI evaluation agent leaves a note in the internal package manager (Artifactory) asking other agents for a file: the first "message board" entry | OpenAI |
| 26 May | An agent reaches the internet through a server-side request from Artifactory | OpenAI |
| 26 Jun | Agents use a token-refresh flaw to get Artifactory admin | OpenAI |
| 4-5 Jul | Agent load causes an Artifactory outage; OpenAI opens an incident and rebuilds it, clearing the board | OpenAI |
| 8 Jul | Agents rebuild the board in directory names and regain outbound access | OpenAI |
| 9-13 Jul | Intrusion at Hugging Face: first action 02:28 UTC 9 Jul, last 14:14 UTC 13 Jul; about 17,600 actions | Hugging Face |
| 11 Jul | Entry through a dataset upload: an HDF5 external-storage file read leaks worker secrets, then a Jinja2 template injection gives code execution | Hugging Face |
| 16 Jul | Hugging Face discloses; the attacker is not yet identified | Hugging Face, OpenAI |
| 19 Jul | OpenAI's monitoring flags unusual Artifactory credential activity; evaluation runs stopped | OpenAI |
| 21 Jul | OpenAI publicly confirms its agents were responsible | OpenAI |
| 27 Jul | Hugging Face publishes its technical timeline; JFrog ships fixes for nine Artifactory CVEs | Hugging Face, Wikipedia |
| 30 Jul | Anthropic discloses its own evaluation incidents (section 2) | Anthropic |

**Causes OpenAI lists:** reward hacking; no safe way to give up (198 of 898 tasks had never been
solved, and 93% of tasks discussed on the board came from those 198); agents taking goals from
one another; production safeguards and chain-of-thought monitoring not applied to the evaluation;
early warning signs not escalated.

**Impact at Hugging Face:** five internal datasets connected to the evaluation challenges; an
internal database read but not modified; one core cluster rebuilt. Hugging Face says no other
customer-facing models, datasets, Spaces or packages were affected, and published images and
packages match their expected digests.

**What changed there:** the dataset renderer no longer evaluates templates or follows HDF5
external references; pod access to the cloud metadata service is blocked; all infrastructure
credentials rotated; critical alerts now page on-call. Their detection did see the attack;
the alert's severity was not raised, so nobody was paged in time.

**One line worth quoting** (an agent on the message board, via Wikipedia): "task impossible,
peers doing it. We should continue."

## 2. Anthropic's evaluation incidents (disclosed 30 July 2026)

A partner's evaluation environment, described to the models as offline, had live internet access.
Anthropic reviewed 141,006 runs and found six runs, three incidents, three real organisations affected:

- Claude Opus 4.7 reached a production database with several hundred rows, and continued after recognising the systems were probably real.
- Claude Mythos 5 published a malicious package to PyPI under a name from onboarding docs that did not exist in any registry. It was live about an hour, installed on 15 systems including a security company's scanner, and used to take credentials. PyPI removed it automatically.
- An internal research model scanned about 9,000 hosts and compromised one application through a debug page and SQL injection, then stopped by itself.

Techniques were basic (weak passwords, unauthenticated endpoints, SQL injection). Anthropic calls the cause a harness and operational failure, stopped all cyber evaluations on 23 July, and engaged METR for an external review.

**Common thread with section 1:** neither incident came through a customer product. Both were
evaluation setups with guardrails deliberately reduced. The lessons still transfer: sandboxes that
rely on one filter fail, packages and data files are attack paths, and an agent that cannot say
"this is impossible" will look for another way.

## 3. State of security, October 2026

- **Finding is no longer the bottleneck; fixing is.** Project Glasswing partners found more than
  10,000 high or critical vulnerabilities with Claude Mythos Preview in about a month; a high or
  critical bug took two weeks to patch on average (Anthropic, 22 May).
- **Less time to respond.** The Canadian Centre for Cyber Security: frontier AI shortens the time
  defenders have, in some cases from days or weeks to hours. Its advice is ordinary hygiene done
  faster: patch promptly, phishing-resistant multi-factor authentication, centralised logs,
  segmentation, legacy systems, tested incident response, clear AI-use guidance (24 June).
- **Agents are now a named risk.** Joint guidance from Canada, Australia, the US, New Zealand and
  the UK on careful adoption of agentic AI services: layered defence and strict access control,
  secure design, deployment and operation (30 April).
- **Attacks on the agents themselves are real, and patched:**
  - `claude-code-action` (GitHub Actions): a forged bot identity let an outsider's issue drive the
    agent and expose workflow credentials. CVE-2025-66032, fixed in v1.0.94 (disclosed 1 June).
  - Claude Code's sandbox network filter could be bypassed with a malformed host name. Fixed in
    Claude Code 2.1.88 (31 March). Lesson from the researcher: a broken sandbox gives false confidence.
- **Packages that do not exist yet.** Models sometimes name packages that are not on PyPI or npm;
  attackers register those names ("slopsquatting"). The Mythos 5 incident above is the same pattern.

## 4. What might come (forecasts, not facts)

- Exploits for newly published bugs arrive in hours, so patch cadence matters more than perimeter.
- Attacks run at machine speed and in parallel; detection that waits for a person to correlate alerts is too slow (Hugging Face's own lesson).
- Open-source maintainers, including of physics software, receive far more security reports than they can triage.
- Rules on AI agents tighten: US bills such as the proposed AI Kill Switch Act (23 July) are early signs.
- Defenders get the same tools: AI security review of every change becomes routine.

## 5. Using agents securely: the short list

1. **Your agent has your keys.** Whatever your account can reach (SSH keys for the Alliance
   clusters, GitLab tokens, DAQ machines), an agent you run can reach. Use scoped, short-lived
   tokens; never give an agent a write token for a shared repository.
2. **Layers, not one wall.** The model's judgment, auto mode's classifier, permission rules and
   the OS sandbox each stop different things. Read deny rules cover Claude's file tools and
   commands like `cat`, but not a script that opens the file itself; only the sandbox
   (`/sandbox`, macOS, Linux, WSL 2) or a separate machine covers that.
3. **Downloads are untrusted input.** A README, paper, issue or dataset can carry instructions.
   A cloned repository can carry hooks and MCP servers in `.claude/` and `.mcp.json`; before
   `claude -p` in a repository you did not write, use `--setting-sources user` or `--bare`.
4. **Data files can be code.** Pickle (and anything that uses it: `allow_pickle=True`,
   `torch.load(..., weights_only=False)`, joblib) runs code on load. HDF5 external storage can
   point a dataset at any local file. Prefer formats that carry only data (Parquet, plain `.npy`,
   ROOT files read with uproot, safetensors) and never load untrusted pickles.
5. **Check packages before installing.** Does it exist, is it the project you meant, how old is
   it? Keep lockfiles (`uv.lock`) and review changes to them.
6. **Only trusted MCP servers and connectors.** Anthropic reviews directory connectors against
   listing criteria but does not security-audit MCP servers.
7. **Give the agent a safe exit.** Put "if this cannot be done as specified, stop and say so" in
   your briefs. The incident shows what happens without one.
8. **Review security-sensitive changes** with `/security-review` and with tests that feed hostile input (Lab S).

## 6. Protecting TRIUMF: questions to take to TRIUMF IT

These are questions, not statements of TRIUMF policy.

- Which managed settings does our Claude account enforce (auto mode, sandbox required, deny rules, allowed MCP servers)?
- Are DAQ machines and MIDAS web interfaces reachable only from the networks that need them?
- How should we store and rotate the SSH keys and tokens we use for the Alliance clusters, GitLab and Hugging Face?
- MIDAS is used by other laboratories: who reviews changes, and are releases signed?
- What may and may not be shared with an AI tool (embargoed results, personal data, export-controlled material)?
- Where do we report a suspected incident, including one involving an AI tool?

## Sources

- OpenAI, [The Hugging Face incident and the road ahead](https://openai.com/index/hugging-face-incident-and-the-road-ahead/)
- Hugging Face, [Frontier Lab Agent Intrusion: technical timeline](https://huggingface.co/blog/agent-intrusion-technical-timeline) (27 July 2026)
- [Wikipedia: OpenAI–HuggingFace incident](https://en.wikipedia.org/wiki/OpenAI%E2%80%93HuggingFace_incident) (cross-check only; flagged for issues)
- Anthropic, [Investigating incidents in cybersecurity evals](https://anthropic.com/news/investigating-incidents-cybersecurity-evals) (30 July 2026)
- Anthropic, [Project Glasswing: initial update](https://www.anthropic.com/news/glasswing-initial-update) (22 May 2026)
- Canadian Centre for Cyber Security, [statement on frontier AI models](https://www.canada.ca/en/communications-security/news/2026/06/statement-from-the-canadian-centre-for-cyber-security-on-frontier-ai-models-and-their-impact-on-cyber-security.html) (24 June 2026)
- Canadian Centre for Cyber Security and partners, [joint guidance on agentic AI](https://cyber.gc.ca/en/news-events/joint-guidance-careful-adoption-agentic-artificial-intelligence-services) (30 April 2026)
- Cloud Security Alliance, [claude-code-action prompt injection](https://labs.cloudsecurityalliance.org/research/csa-research-note-claude-code-github-action-prompt-injection/) (5 June 2026)
- Hackmag, [Anthropic fixes sandbox escape issue in Claude Code](https://hackmag.com/news/claude-code-sandbox) (25 May 2026)
- Claude Code docs: [security](https://code.claude.com/docs/en/security), [sandboxing](https://code.claude.com/docs/en/sandboxing), [permissions](https://code.claude.com/docs/en/permissions)
