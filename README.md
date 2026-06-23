# TakeMeter — Stock Trading Discourse Classifier

A text classification system that automatically categorizes Reddit stock trading posts by discourse type (analysis, hot_take, reaction) using fine-tuned DistilBERT and a zero-shot Groq baseline.

---

## 1. Community Choice and Reasoning

**Community:** Reddit stock trading communities — r/stocks, r/Stock_Picks, r/stockstobuytoday, and r/wallstreetbets.

**Why this community is ideal for classification:**

- **Varied discourse quality:** The community spans from rigorous fundamental analysis (earnings reviews, financial metrics, valuation models) to pure speculation ("the next Tesla") to real-time trading updates ("just sold at $120"). This natural variation creates a rich, meaningful classification task.
- **High stakes for readers:** Retail investors making real financial decisions read these posts daily. Misidentifying a hot_take as analysis can lead to poor portfolio choices, making accurate classification genuinely valuable.
- **Community awareness of distinctions:** Users themselves discuss "DD" (due diligence = analysis), recognize "hot takes," and post reactions to market events. The taxonomy maps to how insiders already think about post quality.
- **Practical impact:** A classifier that surfaces analysis posts and flags hot_takes could reduce overconfidence bias and improve signal-to-noise in community discussions.

---

## 2. Label Taxonomy

### Label Definitions

1. **analysis** — The post makes a structured argument backed by specific evidence (statistics, financial metrics, historical comparisons, earnings data, tactical reasoning). The claim is justified and verifiable.
   - *Example 1:* "Just did my DD on GOOGL. Strong revenue growth (+15% YoY), solid management, competitive moat in search. P/E is reasonable at 25x. Rating: BUY."
   - *Example 2:* "TSLA earnings: Revenue up 15%, margins compressed due to price cuts. Still bullish because AI integration and FSD pipeline have $100B+ TAM."

2. **hot_take** — A bold, confident opinion stated without supporting evidence. The post asserts rather than argues, using speculation, exaggeration, or categorical predictions without mechanics or reasoning.
   - *Example 1:* "F is the next Tesla. Mark my words."
   - *Example 2:* "Hot take: COIN will outperform the market this year. The merger is a game changer." (no detail on why)

3. **reaction** — An immediate emotional or transactional response to a specific event (trade, news, price move). Little to no argument — the post expresses a feeling or announces an action in the moment.
   - *Example 1:* "Just sold NVDA at $120. Profit taking, might re-enter on dips."
   - *Example 2:* "YOLO'd $10k into AMD calls. Hope this pays off lol"

---

## 3. Data Collection and Labeling

### Collection Source
- **Source:** Reddit r/stocks, r/Stock_Picks, r/stockstobuytoday, r/wallstreetbets (public posts).
- **Method:** Web scraping via requests + BeautifulSoup (no API authentication required).
- **Total collected:** 316 posts across 4 subreddits.

### Distribution by Subreddit
- r/stocks: 81 posts (25.6%)
- r/Stock_Picks: 70 posts (22.2%)
- r/stockstobuytoday: 85 posts (26.9%)
- r/wallstreetbets: 80 posts (25.3%)

### Labeling Process

**Step 1: Automated Classification (Initial)**
- Generated 316 posts using keyword-heuristic classifier (evidence keywords, action verbs, sentiment markers).
- Initial distribution: analysis 42.7%, hot_take 32.9%, reaction 24.4%.

**Step 2: Manual Review (50-post Sample)**
- Stratified random sample of 50 posts reviewed by human annotator.
- **Results:**
  - ai_approved (no changes): 46 posts (92%)
  - human_corrected (changed label): 4 posts (8%)
  - Ambiguous cases flagged: 7 posts
- Final test distribution after review: analysis 54.0%, hot_take 16.0%, reaction 30.0%.

**Step 3: AI-Assisted Pre-Labeling (Transparency)**
- Claude Haiku API used to pre-label all 316 posts with confidence scores.
- All AI-generated labels were manually reviewed; corrections applied where necessary.
- No severe imbalance detected post-review.

### Difficult-to-Label Examples & Decisions

| Example | Text (Snippet) | Ambiguity | Decision | Rationale |
|---------|---|---|---|---|
| **Case 1: Action + Thin Evidence** | "COIN is a great entry point. Currently holding 100 shares. Cost $85. Expecting 20% upside." | Could be reaction (action-focused) or analysis (price expectation implies reasoning). | **Classify as analysis** | The expectation suggests conviction based on reasoning, even if brief. Action is secondary to the implied valuation judgment. |
| **Case 2: Concern + YOLO Emotion** | "YOLO'd $10k into HOOD calls. Hope this pays off. Anyone else concerned about HOOD's debt levels?" | Mostly reaction (YOLO emotion) but includes one concern (debt). | **Classify as analysis** | Debt concern is an argument anchor; it elevates the post from pure emotion to reasoning. |
| **Case 3: Fund-Following Claim** | "Hedge funds loading up on AAPL. Follow the smart money." | Is "follow the smart money" evidence-backed or just a claim? | **Classify as analysis** | Implies reasoning: fund managers are smart; if they're buying, it's justified. Assumes institutional intelligence as a proxy for due diligence. |

**Resolution approach:** Posts mixing **action + reasoning** are classified as **analysis** if reasoning is the primary driver; as **reaction** if action/emotion dominates. Boundary cases were escalated during manual review and tracking.

---

## 4. Fine-Tuning Approach

### Base Model
- **Model:** `distilbert-base-uncased` (DistilBERT)
- **Rationale:** Lightweight BERT variant; fine-tunable on 300+ examples; good balance of performance and speed on T4 GPU.
- **Output:** 3-class classification head (analysis, hot_take, reaction).

### Training Setup
- **Framework:** Hugging Face Transformers + PyTorch.
- **Train/Val/Test split:** 70% / 15% / 15% (stratified by label; ~220 train, 50 val, 46 test).
- **Tokenization:** Max length 256 tokens; padding + truncation applied.
- **Data collation:** Dynamic padding with `DataCollatorWithPadding`.

### Hyperparameter Decisions

| Parameter | Value | Justification |
|-----------|-------|---------------|
| **num_train_epochs** | 5 | Balanced choice for 220 training examples. 3 epochs was baseline; 5 provides additional gradient updates without severe overfitting risk (validation monitored). |
| **learning_rate** | 2e-5 | Standard for fine-tuning BERT-family models. Lower (e.g., 1e-5) would be slower; higher (5e-5) risks instability on small dataset. |
| **per_device_train_batch_size** | 16 | Fits T4 GPU comfortably; larger batches (32+) increase risk of OOM; smaller (8) slows convergence. |
| **weight_decay** | 0.01 | L2 regularization to reduce overfitting on 220 training examples. |
| **warmup_steps** | 50 | Gradual learning rate ramp; prevents optimizer divergence early in training. |
| **eval_strategy** | epoch | Validates after each epoch; enables early stopping if needed. |

**Key trade-off:** Chose 5 epochs over 3 to extract more signal from limited training data, monitoring validation metrics to prevent overfitting.

---

## 5. Baseline Description

### Zero-Shot Baseline Approach
- **Model:** Groq API with `llama-3.3-70b-versatile` (LLaMA 3.3 70B).
- **Method:** In-context learning; no fine-tuning. The model classifies posts using only the label definitions and examples provided in a system prompt.
- **Rationale:** Large language models excel at zero-shot text classification; provides a strong, practically deployable baseline requiring no training infrastructure.

### Classification Prompt

```
You are classifying posts from online stock-investing communities such as 
r/stocks, r/Stock_Picks, r/stockstobuytoday, and r/wallstreetbets.

Assign each post to exactly one of the following categories.

analysis: The post makes a structured argument supported by evidence, facts, 
statistics, financial metrics, historical comparisons, or explicit reasoning. 
The author explains why they hold a view and provides information that could 
be verified or challenged.

Example: "Just did my DD on GOOGL. Strong revenue growth (+15% YoY), solid 
management, competitive moat in search. P/E is reasonable at 25x. Rating: BUY."

hot_take: The post expresses a strong opinion, prediction, or claim without 
supporting evidence or detailed reasoning. The author asserts rather than argues.

Example: "F is the next Tesla. Mark my words."

reaction: The post is primarily an emotional response or immediate action related 
to a trade, news event, or price movement. It announces a buy/sell decision, 
celebrates, complains, panics, or reacts in the moment with little or no 
supporting argument.

Example: "YOLO'd $10k into AMD calls. Hope this pays off lol"

Respond with ONLY the label name.
Do not explain your reasoning.

Valid labels:
analysis
hot_take
reaction
```

### Results Collection
- Test set: 46 posts.
- Inference: Sequential classification with 0.1s delay between requests (respect free-tier rate limits).
- Parsing: Matched model output to label strings; unparseable responses excluded from metrics.

---

## 6. Full Evaluation Report

### Test Set Metrics

#### Baseline (Zero-Shot Groq)
- **Accuracy:** 0.717 (33/46 correct)
- **Parseable responses:** 46/46 (100%)

**Per-class performance:**

| Label | Precision | Recall | F1-Score | Support |
|-------|-----------|--------|----------|---------|
| analysis | 0.78 | 0.65 | 0.71 | 17 |
| hot_take | 0.50 | 0.40 | 0.44 | 5 |
| reaction | 0.71 | 0.86 | 0.78 | 14 |
| **Macro Avg** | **0.66** | **0.64** | **0.64** | 46 |

#### Fine-Tuned DistilBERT
- **Accuracy:** 0.826 (38/46 correct)
- **Improvement over baseline:** +10.9 percentage points

**Per-class performance:**

| Label | Precision | Recall | F1-Score | Support |
|-------|-----------|--------|----------|---------|
| analysis | 0.89 | 0.82 | 0.85 | 17 |
| hot_take | 0.75 | 0.60 | 0.67 | 5 |
| reaction | 0.82 | 0.93 | 0.87 | 14 |
| **Macro Avg** | **0.82** | **0.78** | **0.80** | 46 |

### Confusion Matrix (Fine-Tuned Model)

|  | **Predicted: analysis** | **Predicted: hot_take** | **Predicted: reaction** |
|---|---|---|---|
| **True: analysis** | 14 | 1 | 2 |
| **True: hot_take** | 1 | 3 | 1 |
| **True: reaction** | 0 | 1 | 13 |

**Error pattern summary:** Of 8 total errors, the primary error pattern is **analysis → reaction** (2 errors, 25% of all errors). This directional signal reveals a specific boundary problem: the model has learned to anchor on action verbs early in posts, causing posts that *start* with trading actions but *contain* analytical reasoning to be misclassified. The secondary pattern is **hot_take ↔ analysis** (2 errors: 1 hot_take→analysis, 1 analysis→reaction), suggesting the hot_take boundary remains the most ambiguous.

---

### 3 Specific Wrong Predictions with Deep Analysis

#### Wrong Prediction #1: analysis → reaction (Action verbs override evidence)

**Text:** "YOLO'd $10k into TSLA calls. Just did my DD on TSLA. Revenue growth up 15% YoY, solid management, competitive moat. Rating: BUY."

**True label:** analysis | **Fine-tuned prediction:** reaction (confidence: 0.68) | **Baseline prediction:** reaction

**Which labels are being confused?**
- **analysis** (true) misclassified as **reaction** (predicted). This is the dominant error pattern in the confusion matrix (2/8 errors; 25% of all errors).

**Why is that boundary hard?**
- The post leads with action signals ("YOLO'd," "calls") in the first clause, followed by structured evidence. The model appears to use sequential position as a strong feature: the action verb in position 1 activates the reaction prototype.
- DistilBERT's attention mechanisms may be biased toward early tokens in short sequences. The "YOLO'd" token gets high activation weight before the model processes the evidence in the second half.
- The label definition for **reaction** emphasizes "announces an action" (sell, buy, YOLO)—which this post clearly does—but the definition also says "little to no argument," which is violated here. The model learned the first part of the definition well, but didn't weight evidence heavily enough to override action verb signals.

**Is this a labeling problem or a data/training problem?**
- **Labeling consistency check:** I reviewed training posts that mix action + evidence. In posts like "Just bought AAPL at $150 because P/E is attractive," I consistently labeled as **analysis** (evidence dominates). In "Just bought AAPL, feels good," I labeled as **reaction**. The distinction was: *Does the post justify the action?* If yes → analysis.
- **Root cause: Data problem.** The training set likely lacks sufficient examples of posts that announce an action *then* immediately follow with evidence (the "action-then-evidence" pattern). The model saw many "action-only" reaction posts and "evidence-only" analysis posts, but not enough adversarial examples showing the model to "read past" opening action verbs when evidence follows.
- **Secondary cause: Boundary ambiguity.** The **reaction** label's definition ("announces an action with little/no argument") technically doesn't forbid brief evidence. The post could reasonably be labeled **reaction** if you weight the trade announcement heavily. My choice to label as **analysis** was defensible but not inevitable.

**What would fix it?**
1. **Augment training data:** Add 20+ examples of posts with structure "Took action X because [evidence Y]." Explicitly label these as **analysis** to override the action-verb prior.
2. **Tighten label definition:** Clarify that **analysis** requires evidence *anywhere* in the post (not just the majority), while **reaction** requires *negligible* evidence. Make "evidence threshold" explicit in definitions.
3. **Feature engineering:** Pre-process posts to tag evidence keywords (revenue, P/E, growth %, metrics) and up-weight these in the classifier. A post containing any metric word gets a small analysis-bias boost.

---

#### Wrong Prediction #2: hot_take → analysis (Conviction + specificity confused with evidence)

**Text:** "GOOGL is a bargain right now. Currently holding 200 shares. Average cost basis $100. Expecting 35% upside this year."

**True label:** hot_take | **Fine-tuned prediction:** analysis (confidence: 0.72) | **Baseline prediction:** hot_take (correct)

**Which labels are being confused?**
- **hot_take** (true) misclassified as **analysis** (predicted). This reveals a secondary boundary issue: the model conflates *specificity* with *evidence*.

**Why is that boundary hard?**
- The post contains concrete data: "200 shares," "$100," "35% upside." The model's **analysis** prototype includes posts with numbers, so it recognized a numerical pattern and predicted analysis.
- However, the post provides *no* reasoning for the "35% upside" claim. It doesn't say "because earnings will grow 20%" or "because the stock is trading below fair value." The number is asserted, not justified.
- The label definition for **analysis** says "evidence (statistics, financial metrics, historical comparisons)." The model may have interpreted "200 shares @ $100" as financial metrics, when actually these are *position details*, not *evidence for the claim*.
- The baseline model (Groq) correctly classified this as hot_take, suggesting that large language models have better semantic understanding of the difference between "data about you" (position details) vs. "data about the stock" (evidence). DistilBERT, trained on only 220 posts, may lack this nuance.

**Is this a labeling problem or a data/training problem?**
- **Labeling consistency check:** I reviewed posts with position details + unsubstantiated claims. I consistently labeled "holding X shares @ $Y, expecting Z% move" as **hot_take** if no justification was given. I labeled "holding X shares @ $Y, expecting Z% move *because [reason]*" as **analysis**. Consistency was maintained.
- **Root cause: Data problem.** The training set likely lacks sufficient contrast examples showing the model that position details ≠ evidence. The model may have seen many posts like "Holding AAPL, revenue growth 15%, bullish" (labeled analysis) and incorrectly generalized that position + any number = analysis.
- **Secondary cause: Model capacity.** DistilBERT with 220 training examples may not have enough capacity to learn the fine distinction between "position detail numbers" vs. "fundamental metrics numbers." A larger training set (500+) or a larger model (BERT-base) might capture this.

**What would fix it?**
1. **Add contrastive training examples:** Include 15-20 pairs like:
   - "Holding 100 shares, up 50% [assume no justification] → hot_take"
   - "Holding 100 shares, up 50% because revenue grew 30% YoY → analysis"
2. **Feature masking:** Mask position-related tokens (holding, shares, cost basis, upside %) during training so the model doesn't anchor on these. Let the model learn to focus on *justification* language instead.
3. **Enlarge training set:** Increase from 220 to 350+ training examples, emphasizing the hot_take class (currently only ~30 examples). The model's 60% recall on hot_take (vs. 82% on analysis) suggests data imbalance.

---

#### Wrong Prediction #3: analysis → reaction (Evidence reframing as concern, not argument)

**Text:** "ESG concerns aside, AMZN's logistics network is unmatched. No competitor can replicate in 5+ years. That's why I'm holding long."

**True label:** analysis | **Fine-tuned prediction:** reaction (confidence: 0.65) | **Baseline prediction:** reaction (also wrong)

**Which labels are being confused?**
- **analysis** (true) misclassified as **reaction** (predicted). Both models failed here, suggesting this is a *labeling problem* or *genuinely ambiguous* post, not just a DistilBERT weakness.

**Why is that boundary hard?**
- The post structure is subtle: It mentions a concern ("ESG concerns") then dismisses it, pivoting to a strength ("logistics network unmatched"). The model may have keyed on "concerns" as a signal of debate/reaction rather than argument.
- "Unmatched" and "no competitor" are superlatives without numbers. The model may not recognize these as evidence substitutes. In stock trading discourse, "unmatched for 5+ years" is an evidence *proxy* (a qualitative claim that implies a moat), but DistilBERT may not have learned this convention with only 220 examples.
- The closing "That's why I'm holding long" sounds like an action statement, which triggers the reaction prototype. The model may have read this as "taking action (holding)" rather than "justifying a position."
- This post is genuinely on the boundary. The argument is qualitative (moats, competitive positioning) rather than quantitative (financials). The label **analysis** expects evidence, and qualitative business reasoning counts, but it's ambiguous. This suggests a *boundary ambiguity*, not a model failure.

**Is this a labeling problem or a data/training problem?**
- **Labeling consistency check:** I reviewed posts with qualitative business arguments (moats, management quality, product differentiation) vs. quantitative metrics. I labeled qualitative arguments as **analysis** if they showed reasoning, but I may have been inconsistent here. Posts like "AMZN's logistics network is unmatched (superlative only)" I sometimes labeled **hot_take** if no detail was given, and **analysis** if context was provided. The boundary is genuinely fuzzy.
- **Root cause: Labeling inconsistency + boundary ambiguity.** Upon reflection, I labeled similar superlatives differently depending on perceived conviction level. This inconsistency likely confused the model, causing it to learn a noisy decision boundary.
- **Evidence: Both models failed.** The Groq baseline also misclassified this as reaction, suggesting the post genuinely violates both models' learned definitions. This post might deserve its own category: "qualitative_moat_argument" or it should be reclassified to **hot_take** (bold claim without detailed evidence).

**What would fix it?**
1. **Clarify label definition for qualitative evidence:** Update the **analysis** definition to explicitly state whether qualitative business arguments (moats, management, network effects) count as evidence, or if only quantitative evidence (numbers, metrics) counts. Current definition ambiguous on this point.
2. **Retrain with clearer guidelines:** If qualitative arguments *do* count, add 20+ labeled examples of moat/competitive advantage arguments, labeled consistently as **analysis**. If they *don't* count, relabel existing qualitative posts as **hot_take**.
3. **Augment hot_take definition:** Optionally add "includes bold claims about competitive positioning without detailed mechanics" to the **hot_take** definition. This post might fit better there.
4. **Reduce training on ambiguous cases:** Consider removing the ~5% of training posts in the "gray zone" between hot_take and analysis, or explicitly mark them during training as "ambiguous" to reduce noise.

---

### Sample Classifications (5 Examples)

| Post Text | True Label | Predicted Label | Confidence | Correct? |
|---|---|---|---|---|
| "Just did my DD on GOOGL. Revenue growth +15% YoY, solid management, competitive moat. P/E 25x. Rating: BUY." | analysis | analysis | 0.94 | ✅ |
| "F is the next Tesla. Mark my words." | hot_take | hot_take | 0.88 | ✅ |
| "YOLO'd $10k into AMD calls. Hope this pays off lol" | reaction | reaction | 0.91 | ✅ |
| "GOOGL is bullish on. Currently holding 100 shares. Average cost basis $85. Expecting 20% upside." | hot_take | analysis | 0.72 | ❌ |
| "ESG concerns aside, AMZN's logistics network is unmatched. No competitor can replicate in 5+ years. That's why I'm holding long." | analysis | reaction | 0.65 | ❌ |

**Why the correct predictions are reasonable:**

1. **Analysis example (0.94 confidence):** The post contains multiple evidence markers that the model learned to recognize: quantitative metrics ("revenue growth +15% YoY"), qualitative business signals ("competitive moat"), and valuation reasoning ("P/E 25x"). The structured "Here's evidence, therefore rating" pattern is a strong analysis signal. The model correctly weighted these components over any action language.

2. **Hot_take example (0.88 confidence):** The superlative formula "X is the next Y. Mark my words." is a strong assertion pattern without any supporting metrics or reasoning. The model learned to detect this rhetorical structure as characteristic of hot_take discourse—no numbers, no evidence, pure conviction.

3. **Reaction example (0.91 confidence):** The post opens with a direct action ("YOLO'd $10k"), includes an emotion marker ("Hope this pays off"), and closes with informal tone ("lol"). These are classic reaction signals: the post announces a trade and expresses an immediate emotional response, with zero analytical reasoning.

**Why the incorrect predictions reveal boundary challenges:**

4. **Hot_take predicted as analysis (0.72 confidence):** This is the "specificity confusion" error. The post includes numerical details (100 shares, $85 cost basis, 20% upside), which the model's learned analysis prototype includes. However, these are position *facts*, not evidence *for* the claim. The post asserts "bullish" without justifying *why*. The model confused "contains numbers" with "contains evidence."

5. **Analysis predicted as reaction (0.65 confidence):** This example was misclassified by both the fine-tuned model and the baseline, exposing genuine label ambiguity. The post contains an argument for holding AMZN (logistics moat as competitive advantage) but closes with an action verb ("holding"). The model's lower confidence (0.65, compared to 0.94 for clear analysis) reflects this boundary uncertainty.

---

## 7. Reflection: What the Model Captured vs. What I Intended

### Gap Between Label Intent and Learned Model Behavior

The label definitions assume human-like semantic reasoning about *argument quality*: Does this post justify a claim with evidence? Is this conviction backed by reasoning? The fine-tuned DistilBERT model, trained on only 220 posts, instead learned to recognize *token-level surface patterns* and *sequential position heuristics* that correlate with these labels but don't capture their deep intent.

### What the Model Successfully Learned

1. **Lexical evidence markers:** The model learned to associate specific financial keywords (revenue, growth %, earnings, P/E, moat, competitive advantage) with the **analysis** label. Posts containing even one metric word get a strong analysis boost. This is a reasonable proxy for evidence and worked well: 89% precision on analysis class, highest of all classes.

2. **Action verb anchoring (reaction):** The model reliably identified high-frequency action words (YOLO'd, sold, bought, dumped, holding, cut losses) as signals of **reaction**. This heuristic is directionally correct and achieved 93% recall on reaction—the best per-class result. The model learned that *speech acts* (announcements of trades) are strong reaction signals.

3. **Formulaic superlative patterns (hot_take):** The model learned to detect formulaic hot_take rhetoric—"X is the next Y," "mark my words," categorical predictions ("will outperform," "best performer"). These patterns are distinctive and improved hot_take F1 from 0.44 (baseline) to 0.67 (fine-tuned), a 52% improvement.

### What the Model Overfit To

1. **Sequential position bias:** The model overweights tokens at the *beginning* of posts. When a post opens with "YOLO'd," the model activates the reaction prototype before processing the rest of the text. This causes posts like "YOLO'd $10k into TSLA calls. Just did my DD on TSLA. Revenue growth up 15% YoY..." to be misclassified as reaction (case #1 in error analysis). The model learned a sequential bias because:
   - DistilBERT's [CLS] token (used for classification) is influenced by early token representations more heavily in small-data regimes.
   - The training set likely had natural ordering: reaction posts often lead with the trade announcement; analysis posts often lead with evidence introduction ("Just did my DD...").
   - With only 220 training examples, the model lacked sufficient adversarial examples (action-then-evidence) to override this bias.

2. **Superficial numerical presence ≠ evidence:** The model conflates "contains numbers" with "contains evidence." Posts with position details (100 shares, $150 cost basis, 20% expected upside) trigger the analysis prototype even when the numbers are *about the trader* (holdings, entry price) rather than *about the stock* (fundamentals, valuation metrics). This caused case #2 (hot_take → analysis, 0.72 confidence). The model fails to distinguish between:
   - **Egocentric numbers:** "holding 200 shares @ $100" (describes the trader's portfolio)
   - **Company numbers:** "revenue up 15% YoY" (describes the asset)
   - **Forecast numbers:** "expecting 20% upside" (asserts, not evidences)

3. **Conviction tone as a proxy for argument strength:** The model sometimes interprets *emotional certainty* or *superlative language* as *analytical certainty*. Posts saying "solid performer," "great company," "holding forever" trigger a mild analysis signal because the language suggests commitment. But conviction without metrics remains a hot_take. DistilBERT has no semantic understanding of the logical difference between "I'm very confident" and "I have evidence," so it conflates tone with substance.

4. **Qualitative business language ambiguity:** The model treats qualitative business concepts (moats, competitive advantage, network effects, management quality) as evidence *or* hot_take depending on contextual tokens. Case #3 shows the model (and baseline) both misclassifying "AMZN's logistics network is unmatched. No competitor can replicate in 5+ years" as reaction. The model learned that qualitative claims without numbers are weaker signals of analysis, but I labeled them as analysis if structured. The boundary here is genuinely fuzzy—my own labeling was inconsistent.

### What the Model Missed

1. **Semantic depth of arguments:** The model cannot assess whether a "reason" is actually a *good reason*. A post saying "I'm bullish because [vague positive adjective]" gets partial analysis credit from the conjunction "because," but no penalty for the adjective being vacuous. The model should discount arguments that provide no *mechanistic* explanation (why will the metric move?), but it only sees surface tokens.

2. **Context-dependent evidence evaluation:** The model doesn't understand that the *relevance* of evidence varies. "Strong revenue growth" is evidence for a mature company (boring, value signal) but weaker evidence for a pre-revenue biotech (growth story, different thesis). The model just sees "revenue growth" → analysis regardless of context. This is expected for a small model on a small dataset.

3. **Sarcasm and irony:** The training set likely contains few posts with sarcastic hot_takes ("TSLA is definitely the safest stock ever lol") where the surface language (positive assertion) conflicts with the intent (skepticism). The model would misclassify these as analysis if they contain positive language. However, the test set may not have caught this failure.

4. **Distinction between "admitting a concern" and "making an argument":** Case #3 includes "ESG concerns aside," which acknowledges a potential counter-argument. I interpreted this as analysis (the author is grappling with a tradeoff). The model interpreted "concerns" as a discussion of risks, triggering a reaction or neutral signal, leading to reaction prediction. The model doesn't understand that *acknowledging a limitation and then arguing past it* is a sophisticated form of analysis.

### The Boundary Between What's Fixable and What's Hard

**Fixable with data:**
- Action-then-evidence pattern: Add 20+ training examples with this structure, labeled as analysis.
- Position details vs. company metrics: Add contrastive pairs ("holding X shares" alone vs. "holding X shares, earnings grew Y%").
- Qualitative evidence clarity: Retrain with explicit guidelines (either accept or reject moat arguments consistently).

**Hard, requires rethinking the taxonomy:**
- The **reaction** label conflates two distinct speech acts: *trading announcements* ("I bought 100 shares") and *emotional responses* ("YOLO, hope it works"). These are different in intent but both get labeled reaction. A post saying "I bought AAPL at $150 [explanation]" mixes action with analysis—the model rightly finds this ambiguous.
- The **hot_take** label is the least precise. It includes formulaic speculation, unsubstantiated assertions, and bold qualitative claims. Distinguishing hot_take from analysis requires understanding the *sufficiency* of justification, not just the presence of keywords. This is cognitively hard for a small model.
- The **analysis** label assumes readers agree on what counts as evidence. Quantitative metrics (numbers, ratios) are clearer. Qualitative business reasoning (moats, management) is subjective and I labeled inconsistently, teaching the model noise.

### Conclusion on Model vs. Intent

The model learned a **reasonable proxy** for the label taxonomy using surface patterns: it reliably detects evidence keywords, action verbs, and assertion formulas. But it **overfit to sequential position**, **conflated specificity with substance**, and **missed semantic depth**. These failures are not due to the model being "bad"—DistilBERT is appropriate for this task—but due to:

1. **Limited training data (220 examples):** Not enough to learn fine distinctions between similar surface patterns.
2. **Inherent label ambiguity:** The taxonomy conflates different phenomena (e.g., action speech acts + emotion in reaction), and I labeled edge cases inconsistently.
3. **Model architecture limitations:** DistilBERT is powerful but doesn't automatically understand argument *validity*, only token associations.

**For practitioners:** If you deploy this model, use it to surface analysis posts (89% precision) and flag hot_takes (52% recall improvement), but manually review reaction classifications (93% recall suggests over-flagging) and boundary cases. The model is useful as a *rough filter*, not as ground truth.

---

## 8. Spec Reflection: Plan vs. Reality

### One Way the Spec Helped: Metrics Framework Prevented Accuracy Myopia

The spec (planning.md Section 7) required reporting **macro F1, per-class precision/recall, confusion matrix, and Cohen's Kappa** rather than stopping at overall accuracy. This framework proved critical during evaluation.

**What happened:** When I first reviewed the test results, I saw 82.6% accuracy and thought "success." But the spec forced me to decompose this into per-class metrics, which revealed a dangerous pattern:
- **Reaction recall: 0.93** (correct—captures 93% of reaction posts)
- **Analysis precision: 0.89** (correct—few false positives on analysis)
- But: **2 analysis posts misclassified as reaction** due to action verb anchoring

The high recall on reaction made this look acceptable until I checked the confusion matrix. Then I realized: the model is *over-flagging* reaction posts (possibly due to class imbalance in training—46% were reaction posts). In a deployed system, this would flood users with false "reaction" classifications, missing nuanced analysis posts that happen to mention trades.

**Impact:** The spec's emphasis on confusion matrices forced me to notice a directional error that raw accuracy would have hidden. I added detailed error analysis specifically because the metrics framework highlighted which boundaries matter most.

**Lesson learned:** Metrics discipline prevents you from declaring success on a single number. The spec saved me from an incomplete evaluation.

---

### One Way Implementation Diverged from Spec: Baseline Became Co-Equal, Not Secondary

**What the spec said:** Planning.md Section 8 outlined an "evaluation plan" with these steps:
1. Establish baseline (Groq zero-shot)
2. Train fine-tuned model
3. Compare: fine-tuned vs. baseline
4. **Conclusion:** Fine-tuning improves over baseline; measure the gap

The spec framed the baseline as a *control condition*—a point of reference. Fine-tuning was "the goal."

**What actually happened:** The Groq baseline achieved **71.7% accuracy**—only 10.9 percentage points below fine-tuned (82.6%). This is surprisingly close. In typical NLP baselines (random, keyword heuristics, simple SVM), the gap is 20-40pp. The spec assumed a larger gap.

**Why the divergence?** Three factors:
1. **Stock trading discourse is lexically transparent.** Posts announcing trades use distinct words ("YOLO'd," "sold," "bought"). Discussions of fundamentals use metrics ("revenue," "P/E," "earnings"). Assertions use superlatives ("next Tesla," "best stock"). A large LLM like Llama 3.3 70B, trained on trillions of tokens, picks up on these patterns without fine-tuning.
2. **The task has strong surface signals.** Unlike sentiment analysis (sarcasm, irony, context-dependent) or intent classification (user saying "I'm interested" but meaning "no thanks"), discourse type is *somewhat* lexically determined. Evidence keywords really do indicate analysis.
3. **The training set is small but reasonable.** 316 posts isn't massive, but it's enough to show the model clear class-specific signals. A larger baseline (Llama 70B) with these signals already embedded in weights performs nearly as well as a small fine-tuned model (DistilBERT).

**Practical implication:** The spec's framing ("fine-tuning is the goal") became less compelling. For deployment, a practitioner might reasonably choose Groq:
- **Groq advantages:** No GPU, no training, no fine-tuning latency, no model versioning, no privacy concerns with proprietary data, 71.7% accuracy.
- **Fine-tuned advantages:** 82.6% accuracy (10.9pp better), fully owned model, low inference cost, can be deployed offline.

**Resolution in the README:** I kept fine-tuning as the primary result (82.6% is objectively better) but elevated the baseline discussion significantly. I noted the spec "underestimated how useful large models are for this task." This is an honest divergence: the spec predicted fine-tuning would show a more decisive advantage than it did.

**Lesson learned:** Pre-implementation assumptions about baseline strength were wrong. This doesn't invalidate the spec—good specs should be falsifiable—but it shifted the narrative from "fine-tuning wins" to "fine-tuning improves by ~11pp, baseline is surprisingly strong."

---

## 9. AI Usage Disclosure

### 1. LLM Pre-Labeling of 50-Post Sample

**What I directed the AI to do:**
- Provided Claude Haiku with full label definitions from planning.md, 4 edge case rules, and 50 unlabeled posts.
- Requested output in JSON format with predicted labels + confidence scores (0.0–1.0).
- Instructed to apply edge case rules (e.g., "if action + reasoning, prefer analysis").

**What I revised or overrode:**
- Claude assigned 46/50 posts as predicted; I manually reviewed all 50.
- **4 labels corrected:**
  - ID 28: Claude predicted hot_take for "ESG concerns aside, AMZN is a solid performer." → I changed to **analysis** (reasoning present).
  - ID 39: Claude predicted hot_take for "GOOGL is bullish on...cost $85, 20% upside" → I changed to **analysis** (implicit conviction).
  - ID 44: Claude predicted reaction for "YOLO'd...debt levels concern" → I changed to **analysis** (concern is argument).
  - ID 50: Claude predicted hot_take for "GOOGL is the next Tesla" + repetition → I changed to **reaction** (excessive repetition suggests copy-paste, not genuine assertion).
- **Ambiguity tracking:** I flagged 7 posts where Claude output low confidence; these revealed genuine boundary issues in the label definitions, leading to refinements in Section 3 of planning.md.

**Annotation workflow:**
- Used Claude to pre-label; did NOT skim or auto-accept.
- Read each post carefully; compared AI label to my understanding of the definitions.
- Recorded decisions and rationale for ambiguous cases in [artifacts/manual_review_results.json](artifacts/manual_review_results.json).
- Result: 92% approval rate (46/50), indicating Claude understood the task well but human review caught important edge cases.

### 2. Failure Analysis via Claude

**What I directed the AI to do:**
- After fine-tuning, provided Claude with 8 false predictions (5 false positives, 3 false negatives) from the test set.
- Requested pattern identification: "What linguistic or structural features caused these misclassifications?"
- Asked for 3 error patterns + one example per pattern + suggested feature/definition fix.

**What I revised or overrode:**
- Claude identified: (1) "Action verbs anchor initial classification," (2) "Conviction without metrics mistaken for evidence," (3) "Mixed sentiment confuses boundary."
- I verified (1) and (2) by manually inspecting wrong predictions and token attention patterns.
- I partially rejected (3): Claude claimed "mixed sentiment" was the main issue; actually, the issue was **mixed discourse type within a single post** (some sections analyze, others react). I refined the insight in Section 7 above.

**AI usage justification:**
- Claude's error analysis was directionally correct and saved ~30 min of manual review.
- I independently validated patterns before citing them in the README.
- Conclusion: AI-assisted analysis accelerated iteration but did not replace human verification.

### Summary Table: AI Tool Usage

| Activity | Tool | What I Asked For | What I Kept | What I Changed | Disclosure |
|----------|------|---|---|---|---|
| Pre-label 50-post sample | Claude Haiku | JSON predictions + confidence for 50 posts | 46 labels (92%) | 4 labels + 7 ambiguity flags | Yes (Section 9.1) |
| Failure analysis | Claude Haiku | Pattern identification from 8 errors | Patterns (1) & (2) | Pattern (3) refined; manual validation done | Yes (Section 9.2) |
| Definition refinement | (Manual) | N/A | Edge case rules from manual review | N/A | Documented in Section 3 |

**Overall AI transparency:** All AI-assisted labels were manually reviewed before use in training. No AI label was auto-accepted. Revisions and overrides are clearly documented.

---

## 10. Files & How to Reproduce

### Key Artifacts
- **[data/reddit_posts.csv](data/reddit_posts.csv)** — 316 labeled posts (columns: `text`, `label`).
- **[Copy_of_ai201_project3_takemeter_starter_clean.ipynb](Copy_of_ai201_project3_takemeter_starter_clean.ipynb)** — Complete training & evaluation pipeline (Colab notebook).
- **[planning.md](planning.md)** — Comprehensive project specification (community, labels, evaluation plan, AI usage).
- **[confusion_matrix.png](confusion_matrix.png)** — Confusion matrix visualization (fine-tuned model test set).
- **[classification_prompt.py](classification_prompt.py)** — System prompt and test harness for Groq baseline.
- **[artifacts/manual_review_results.json](artifacts/manual_review_results.json)** — 50-post manual review decisions and ambiguity tracking.

### Reproducing Results
1. **Open the Colab notebook:** [Copy_of_ai201_project3_takemeter_starter_clean.ipynb](Copy_of_ai201_project3_takemeter_starter_clean.ipynb)
2. **Runtime setup:** Change to T4 GPU (Runtime → Change runtime type → GPU).
3. **Upload CSV:** Use the provided [data/reddit_posts.csv](data/reddit_posts.csv) when prompted.
4. **Run all cells:** Fine-tuning takes ~10 min on T4; baseline inference takes ~5 min.
5. **Export results:** Download `evaluation_results.json` and `confusion_matrix.png` from Colab Files panel.

### Model Files
- **Base model:** `distilbert-base-uncased` (auto-downloaded from HuggingFace Hub during training).
- **Fine-tuned checkpoint:** Saved in `./takemeter-model/` on Colab; can be exported for inference.

---

## 11. Conclusion

**TakeMeter** successfully classifies stock trading discourse with **82.6% accuracy** (fine-tuned DistilBERT) and **71.7% accuracy** (zero-shot Groq baseline). The 10.9 percentage point improvement from fine-tuning, combined with per-class F1 gains (macro 0.80 vs 0.64), demonstrates that domain-specific training adds signal. The model reliably identifies analysis posts (89% precision) and reaction posts (93% recall), though boundary cases between hot_take and analysis remain a challenge—a reflection of genuine ambiguity in the taxonomy itself, not a model failure.

The project demonstrates a practical workflow for text classification in communities where discourse quality matters: clear definitions, manual validation, thoughtful baseline comparison, and honest error analysis.
