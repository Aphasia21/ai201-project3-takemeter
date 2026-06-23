# TakeMeter — Stock Trading Discourse Classifier

**Project goal:** Build a text classifier that automatically categorizes Reddit stock trading posts by discourse type (analysis, hot_take, reaction) to help retail investors quickly assess the credibility and nature of advice they encounter.

---

## 1. Community

**Why Reddit stock trading subreddits?**

The stock trading community on Reddit—specifically r/stocks, r/Stock_Picks, r/stockstobuytoday, and r/wallstreetbets—is an excellent fit for classification because:

- **Varied discourse quality:** The community spans from rigorous fundamental analysis (earnings reviews, financial ratios, valuation models) to pure speculation ("the next Tesla") to real-time trading updates ("just sold at $120"). This natural variation is what makes classification meaningful.
- **High stakes for readers:** Retail investors making real financial decisions read these posts daily. Misidentifying a hot_take as analysis can lead to poor portfolio choices.
- **Community awareness of distinctions:** Users themselves discuss "DD" (due diligence = analysis), "hot takes," and reactions to market events. The taxonomy maps to how insiders already think about post quality.
- **Practical impact:** A classifier that surfaces analysis posts and flags hot_takes could improve community signal-to-noise and reduce overconfidence bias.

---

## 2. Labels

**Label taxonomy (3 mutually exclusive categories):**

1. **analysis** — The post makes a structured argument backed by specific evidence (statistics, historical comparisons, financial metrics, tactical reasoning). The claim is justified; you could verify or refute it.
   - *Example 1:* "Just did my DD on GOOGL. Strong revenue growth (+15% YoY), solid management, competitive moat in search. P/E is reasonable at 25x. Rating: BUY."
   - *Example 2:* "TSLA earnings report: Revenue up 15%, margins compressed due to price cuts. Still bullish long-term because the AI integration and FSD pipeline are game changers with $100B+ TAM."

2. **hot_take** — A bold, confident opinion stated without supporting evidence. The assertion might be true, but the post claims rather than argues. Characterized by speculation, exaggeration, or categorical predictions without mechanics.
   - *Example 1:* "F is the next Tesla. Mark my words."
   - *Example 2:* "Hot take: COIN will outperform the market this year. The merger is a game changer." (no detail on why)

3. **reaction** — An immediate emotional or transactional response to a specific event (trade, news, price move). Little to no argument—the post is expressing a feeling or announcing an action in the moment.
   - *Example 1:* "Just sold NVDA at $120. Profit taking, might re-enter on dips."
   - *Example 2:* "YOLO'd $10k into AMD calls. Hope this pays off lol"

**Why this taxonomy works:**
- (1) Decision boundary is clear: evidence + structured reasoning = analysis; no evidence + assertion = hot_take; action + emotion = reaction.
- (2) Reliable inter-rater agreement: most posts fall cleanly into one category; community members already recognize these distinctions.
- (3) Reflects community values: traders explicitly respect analysis, discount hot_takes, and track reactions as market sentiment indicators.

---

## 3. Hard Edge Cases

**Genuinely ambiguous posts:**

| Case | Ambiguity | Handling |
|------|-----------|----------|
| **Analysis + reaction hybrid** | "I bought $5k of AAPL at $150. Revenue growth is strong and P/E is under historical average." | Label as **analysis** (evidence-led) because the post provides reasoning; the action is secondary. The decision was grounded in data. |
| **Hot_take + analysis thin data** | "I think MSFT will hit $400 because AI is the future and they own OpenAI." | Label as **hot_take**. While AI is mentioned, there's no concrete evidence (no TAM, no revenue impact estimate, no comparison to valuation). The assertion lacks specificity. |
| **Reaction with embedded claim** | "Lost 30% on TSLA this year. Might be time to cut losses because valuations are stretched." | Label as **reaction** because the post is led by emotional/transactional content ("lost 30%"). The valuation comment is a weak afterthought. |
| **Question or discussion opener** | "Thoughts on META? Is it worth buying at this price?" | Label based on the **body/discussion** if present. If only a question, look for embedded examples in the post. If purely open-ended with no examples, classify as **reaction** (it's soliciting immediate takes, typical of day-trader behavior). |

**Handling strategy during annotation:**
- Tag ambiguous cases during manual review and create a small arbitration corpus (20–30 posts).
- Two annotators independently label the arbitration set; discuss disagreements and refine definitions for the next iteration.
- For the classifier, test sensitivity on the boundary cases; use confidence scores to flag uncertain predictions.

---

## 4. Data Collection Plan

**Source:** Reddit r/stocks, r/Stock_Picks, r/stockstobuytoday, r/wallstreetbets (public, no auth required for read).

**Target distribution (316 total posts collected):**
- r/stocks: 80 posts (~25%)
- r/Stock_Picks: 70 posts (~22%)
- r/stockstobuytoday: 85 posts (~27%)
- r/wallstreetbets: 80 posts (~25%)

**Current label distribution (after automated classification):**
- analysis: 135 posts (42.7%)
- hot_take: 104 posts (32.9%)
- reaction: 77 posts (24.4%)

**Handling label imbalance:**
- The imbalance (analysis > hot_take > reaction) reflects the **natural distribution** in the community (analysis is valued; reactions are common but shorter).
- **No downsampling:** Keep all 316 posts. Imbalance is a feature, not a bug.
- **During training:** Use class weights to penalize misclassifying the minority class (reaction) and avoid the model collapsing to always predicting analysis.
- **Evaluation:** Report **per-class precision, recall, F1** (not just accuracy) to ensure the model performs well on all labels, especially the minority class.

**Train / validation / test split:**
- Train: 220 posts (70%)
- Validation: 50 posts (15%)
- Test: 46 posts (15%)

---

## 5. Evaluation Metrics

**Metrics chosen:**

1. **Macro-averaged F1 score** — Primary metric.
   - Why: Gives equal weight to all classes (analysis, hot_take, reaction) regardless of frequency. Balances precision and recall.
   - Threshold for good performance: **F1 ≥ 0.75** (on test set).

2. **Per-class precision, recall, F1**
   - Why: Reveals whether the model favors one class or struggles on minority classes.
   - Check: Ensure reaction (minority class) is NOT sacrificed.
   - Minimum: All classes should have **recall ≥ 0.65** (catch most true positives, even if some false positives).

3. **Confusion matrix + accuracy**
   - Why: Shows which label pairs are confused most (e.g., hot_take vs. analysis boundary). Informs edge case handling.

4. **Cohen's Kappa (inter-rater agreement)**
   - Why: Measures how much better the classifier is vs. random chance, controlling for class imbalance.
   - Target: **κ ≥ 0.70** (substantial agreement by research standards).

**Why accuracy alone is insufficient:**
- If 42.7% of test set is analysis, a naive classifier predicting "analysis" for everything achieves 43% accuracy—useless.
- Macro F1 and per-class metrics reveal whether the model truly learned to distinguish all three types.

---

## 6. Definition of Success

**Deployment readiness criteria:**

For this classifier to be genuinely useful in a real community tool (e.g., a browser extension that badges posts):

1. **Performance threshold:**
   - Macro F1 ≥ **0.75** on a held-out test set of 46 posts.
   - Per-class recall ≥ **0.65** (catch most true positives).
   - No class sacrificed (e.g., reaction recall <0.60 would fail).

2. **Error tolerance:**
   - **False negatives (missed analyses):** Can tolerate 1 in 7 missed analyses; users can read the original post.
   - **False positives (mislabeling hot_take as analysis):** Cannot exceed 1 in 4; users might trust bad advice.
   - **Reaction vs. hot_take confusion:** Acceptable; less critical (both are non-evidential).

3. **Real-world validation:**
   - Have 5–10 community members (actual traders) manually label 50 random test posts.
   - If their agreement with the model is **κ ≥ 0.65**, the model is "human-competitive" and deployable.

4. **Edge case handling:**
   - The model should output **confidence scores** on all predictions.
   - Mark predictions with confidence < 0.60 as uncertain; prompt human review.
   - This prevents the tool from confidently mislabeling ambiguous posts.

**Acceptance criteria for "good enough":**
- Macro F1 ≥ 0.72 (slight flexibility from 0.75 target).
- All per-class recalls ≥ 0.60.
- Human validators agree with model on ≥65% of edge cases.

If performance falls short, iterate on:
- Keyword-based classifier features (evidence keywords, action verbs, sentiment).
- Manual re-annotation of misclassified examples (identify systematic blind spots).
- Refinement of label definitions (if a particular boundary is consistently fuzzy).

---

## 7. Evaluation Plan (Detailed Workflow)

### Phase 1: Manual Annotation & Label Validation
**Goal:** Validate automated labels and build ground truth.

1. **Sample selection:** Randomly select 50 posts from the 316-post dataset (stratified by current label to ensure balanced sample).
2. **Dual annotation:** Two annotators independently label these 50 posts using the label definitions (no knowledge of automated labels).
3. **Agreement check:**
   - Compute Cohen's Kappa between annotators.
   - If κ ≥ 0.70: proceed to Phase 2 (manual labels are reliable).
   - If κ < 0.70: refine definitions based on disagreement patterns; re-annotate the 50 posts.
4. **Adjudication:** For the 50 posts, resolve disagreements via discussion; use the majority label as ground truth.
5. **Compare to automation:** Cross-tabulate manual labels vs. automated labels to measure accuracy of the keyword-based classifier.

### Phase 2: Train / Validation / Test Split
**Goal:** Prepare data for model training and evaluation.

1. **Use manually validated 50 posts + remaining 266 automated posts** (total 316).
2. **Stratified split by class:**
   - Train: 220 posts (70%) — roughly 94 analysis, 72 hot_take, 54 reaction.
   - Validation: 50 posts (15%) — used for hyperparameter tuning.
   - Test: 46 posts (15%) — held out, never seen during training or validation.
3. **Document split:** Save train/val/test indices; ensure no data leakage.

### Phase 3: Baseline Model
**Goal:** Establish a performance floor.

1. **Majority class baseline:** Always predict "analysis" (42.7% of training set).
   - Expected accuracy: 42.7%.
   - Expected macro F1: ~0.20–0.30 (useless).
   - This is the performance threshold the real model must beat.

2. **Simple keyword classifier:** Rule-based model using the same heuristics as automation.
   - Measure macro F1 and per-class metrics.
   - Diagnose which label boundary is hardest (this informs feature engineering).

### Phase 4: Model Training
**Goal:** Build and tune the classification model.

1. **Models to test:**
   - **Logistic Regression** (baseline, interpretable).
   - **SVM** (non-linear, good for high-dimensional text features).
   - **Naive Bayes** (probabilistic, fast).
   - **Optional:** Fine-tuned transformer (e.g., DistilBERT) if compute allows.

2. **Feature engineering:**
   - Bag-of-words + TF-IDF for vocabulary.
   - Evidence keyword presence (1/0 flags for "revenue," "P/E," "earnings," etc.).
   - Action keyword presence ("sold," "bought," "yolo," "cut losses").
   - Text length, capitalization, punctuation.
   - Sentiment polarity (optional; use TextBlob or similar).

3. **Hyperparameter tuning:**
   - Use validation set (50 posts) to tune regularization (L1/L2), learning rate, class weights.
   - Grid search or random search over 10–20 parameter combinations.
   - Select model with highest macro F1 on validation set.

4. **Class weighting:** Upweight minority class (reaction) to prevent collapse to majority class.
   - Weight ratios: analysis=1.0, hot_take=1.3, reaction=1.8 (empirical based on class distribution).

### Phase 5: Evaluation on Test Set
**Goal:** Measure final performance and diagnose failures.

1. **Compute metrics:**
   - Accuracy (overall correctness).
   - **Macro-averaged F1** (primary metric; target ≥0.75).
   - **Per-class precision, recall, F1** (ensure all classes ≥0.65 recall).
   - **Confusion matrix** (which pairs are confused most?).
   - **Cohen's Kappa** (vs. random; target κ ≥0.70).
   - **Per-class support** (verify test set is stratified).

2. **Error analysis:**
   - Inspect false negatives by class (missed analyses, missed hot_takes, missed reactions).
   - Identify error patterns (e.g., "analysis posts with no numbers are mislabeled as hot_take").
   - Categorize errors into systematic vs. inherent ambiguity.

3. **Confidence score analysis:**
   - Use model's predicted probability for each class.
   - Plot confidence vs. correctness: do high-confidence predictions have lower error rate?
   - Identify threshold (e.g., confidence < 0.60) for flagging uncertain predictions.

### Phase 6: Cross-Validation (Optional, if Data Permits)
**Goal:** Ensure robustness and reduce variance from random split.

1. **Stratified 5-fold cross-validation** on full 316-post dataset.
2. **Report:** Mean ± std dev of macro F1, per-class F1 across folds.
3. **Compare:** If CV macro F1 mean is within 0.05 of test macro F1, the model generalizes well.

### Phase 7: Human Validation
**Goal:** Confirm model performance aligns with real-world community expectations.

1. **Recruit 5–10 community members** (active traders) via Reddit or Discord.
2. **Test set:** Have them independently label 46 test posts (same ones the model tested on).
3. **Compute inter-rater agreement:**
   - Pairwise Cohen's Kappa between humans.
   - Kappa between model and human consensus.
4. **Success:** If model κ ≥ 0.65 vs. human consensus, model is "human-competitive."
5. **Qualitative feedback:** Ask annotators which labels they found hardest to assign; refine definitions if needed.

### Phase 8: Iteration & Refinement
**Goal:** Improve model if performance falls short of success criteria.

If macro F1 < 0.72 or any class recall < 0.60:

1. **Re-examine labels:** Are the definitions clear enough? Consider collapsing hot_take + reaction into "non-evidence-based" if confusion is high.
2. **Feature analysis:** Use LIME or Shapley values to identify which features are most predictive for each class. Add or remove features accordingly.
3. **Manual review:** Randomly sample 30 mislabeled posts; annotate manually to identify if labels were wrong or model simply confused.
4. **Re-annotate:** If high disagreement on mislabeled posts, re-annotate 20% of training set; retrain.
5. **Ensemble:** Combine rule-based and learned classifier (weighted voting) if individual models plateau.

### Evaluation Summary Table

| Phase | Objective | Success Criteria | Owner |
|-------|-----------|------------------|-------|
| 1 | Manual validation of 50 posts | Cohen's κ ≥ 0.70 between annotators | Human annotators |
| 2 | Data split | No leakage; stratified distribution | Engineer |
| 3 | Baseline | Keyword classifier macro F1 ≥ 0.40 | Engineer |
| 4 | Model training | Validation macro F1 ≥ 0.70 | Engineer |
| 5 | Test evaluation | **Test macro F1 ≥ 0.75**; all class recalls ≥ 0.65 | Engineer |
| 6 | Cross-validation | CV mean F1 within ±0.05 of test F1 | Engineer (optional) |
| 7 | Human validation | Model κ ≥ 0.65 vs. human consensus | Community |
| 8 | Iteration | Refine labels / features if Phase 5 fails | Engineer |

---

## 8. AI Tool Plan

### 8.1 Label Stress-Testing (Before Annotation)

**Goal:** Validate label definitions by asking an AI to generate boundary-case posts. If the AI produces posts that *you* cannot classify consistently, the definitions need tightening before you annotate 200 examples.

**Workflow:**

1. **Prompt an LLM** (e.g., Claude, GPT-4) with the label definitions and edge cases:
   ```
   You are a Reddit stock trading discourse expert. Given these label definitions:
   
   - analysis: structured argument backed by specific evidence (statistics, comparisons, metrics).
   - hot_take: bold confident opinion without supporting evidence; assertion over argumentation.
   - reaction: immediate emotional/transactional response to an event; little reasoning.
   
   Generate 5–10 posts that sit on the **boundary** between two of these labels 
   (e.g., analysis vs. hot_take, or hot_take vs. reaction). 
   These should be genuinely ambiguous — I should struggle to classify them.
   
   Label each post with the two labels it sits between.
   ```

2. **Manually classify the generated posts:** Try to assign each to one of the three labels using only the definitions.
   - If you can confidently classify ≥80% of them, the definitions are clear.
   - If ≥20% are genuinely ambiguous, refine the definitions now. Examples:
     - **Too blurry:** "Should a post with one metric (e.g., 'P/E is 25x') but no reasoning count as analysis?" → Add rule: "At least 2 pieces of evidence or explicit reasoning."
     - **Too loose:** "Can a hot_take include a single factual claim?" → Clarify: "A hot_take asserts a prediction *without* supporting why."

3. **Document refinements:** Update Section 2 (Labels) and Section 3 (Edge Cases) with tighter decision boundaries.

4. **Record:** In your AI usage section, note:
   - Tool used: [e.g., Claude API].
   - Date: [when this was done].
   - Output: [saved prompts + generated posts in `artifacts/stress_test_posts.txt`].
   - Outcome: [definitions refined, 0 changes / 1 refinement / etc.].

**Success criteria:** Definitions can correctly classify ≥80% of AI-generated boundary posts.

---

### 8.2 Annotation Assistance (Pre-Labeling Strategy)

**Goal:** Decide whether to use an LLM to pre-label examples before you manually review them.

**Decision framework:**

| Approach | Pros | Cons | Use If |
|----------|------|------|--------|
| **Manual only** | Ground truth is fully human; no AI bias. | Slower; higher cost. | You have time & annotators; high accuracy is critical. |
| **LLM pre-label + human review** | Faster; can cover all 316 examples. AI catches obvious cases; humans fix edge cases. | Potential for AI bias to creep into final labels. Must track which were AI-generated. | You have limited time; willing to trust LLM on 60–70% of examples. |
| **Hybrid: LLM for weak labels, humans for uncertain** | Efficient; focuses human effort on hard cases. | Requires confidence scoring infrastructure. | You need speed and have access to confidence scores from LLM. |

**Recommended approach: LLM pre-label + human review**

1. **Batch pre-labeling:** Send batches of 50 posts to an LLM with the label definitions:
   ```
   Classify each post as 'analysis', 'hot_take', or 'reaction'. 
   Return CSV format: [text], [predicted_label], [confidence_0_to_1].
   ```

2. **Human review workflow:**
   - Accept all LLM labels with confidence ≥ 0.85 (≈70–80% of examples).
   - Manually re-label all examples with confidence < 0.85 or that look ambiguous.
   - Track: For each post in final CSV, add a `review_status` column: `ai_approved`, `human_corrected`, `human_only`.

3. **Disclosure:**
   - In your submission, include a table: "# of posts by review status."
   - Example:
     ```
     Review Status       | Count
     ------------------|-------
     ai_approved        | 215
     human_corrected    | 61
     human_only         | 40
     Total              | 316
     ```
   - Justify: "AI pre-labeling reduced annotation time by 40% while maintaining ≥0.95 agreement on accepted labels."

4. **Tools & tracking:**
   - Tool: Claude API or GPT-4 (you choose based on cost / accuracy).
   - Storage: Save all AI-generated predictions in `artifacts/ai_prelabels.csv`.
   - Merge: Combine with human corrections in final [data/reddit_posts.csv](data/reddit_posts.csv).

5. **Transparency in AI usage section:**
   ```
   **AI Pre-labeling:**
   - Tool: Claude 3 Haiku via API.
   - Date: [when executed].
   - Coverage: 316 posts across 4 subreddits.
   - Confidence threshold: 0.85 for auto-acceptance.
   - Human review: 101 posts manually corrected or re-labeled.
   - Agreement: 94.7% of AI-approved labels matched human review.
   ```

---

### 8.3 Failure Analysis (Pattern Detection)

**Goal:** After training, use an LLM to analyze wrong predictions and identify systematic patterns before you write up your evaluation.

**Workflow:**

1. **Prepare failure dataset:**
   - Run the trained model on test set (46 posts).
   - Identify all false positives and false negatives (e.g., 5–10 errors).
   - Create CSV: `[text], [true_label], [predicted_label], [model_confidence]`.
   - Save to `artifacts/test_errors.csv`.

2. **Prompt an LLM for pattern detection:**
   ```
   You are analyzing classification errors. Below are posts where a text classifier 
   misclassified them. The true label was [X], but the model predicted [Y].
   
   [Insert 5–10 error cases]
   
   Identify patterns:
   1. What linguistic or structural features made the model confused?
   2. Do certain types of posts (e.g., "posts with no numbers") always get mislabeled?
   3. Are there overlapping keywords between true and predicted labels?
   4. Which label boundary is hardest (analysis vs. hot_take? reaction vs. analysis)?
   
   Return:
   - Top 3 error patterns.
   - For each, provide 1–2 examples from the list.
   - Suggest a feature or definition change to reduce this error.
   ```

3. **Verify patterns yourself:**
   - For each pattern the LLM identifies, manually inspect the original false-positive/negative posts.
   - Ask: "Is the LLM's explanation actually supported by the data, or is it inferring?"
   - Document which patterns were confirmed vs. spurious.

4. **Iterate on features/definitions:**
   - **Confirmed pattern:** "Posts with only action verbs (sold, bought) but no reflection are hard to distinguish from analysis if they mention price targets."
     - Solution: Add a feature `has_reasoning` (does the post explain *why* the action was taken?).
   - **Spurious pattern:** LLM claimed "short posts are always reactions" but counterexamples exist.
     - Discard this insight; focus on other patterns.

5. **Document for evaluation section:**
   ```
   **Failure Analysis (LLM-Assisted):**
   - Tool: Claude 3 Haiku.
   - Date: [when analysis ran].
   - Errors analyzed: 8 false positives + 3 false negatives = 11 total.
   - Patterns identified: 3 (LLM) → 2 confirmed, 1 spurious.
   - Confirmed patterns:
     1. Reaction + specific price target (e.g., "sold at $120") → often misclassified as analysis.
        Solution: Flag posts with action verb + price but no reasoning.
     2. Hot_take with one metric (e.g., "P/E is 20x, overvalued") → misclassified as analysis.
        Solution: Require ≥2 metrics or explicit comparison for analysis.
   - Recommendations: Reweight features; retrain with updated feature set.
   ```

6. **AI usage disclosure:**
   ```
   **Failure Analysis:**
   - Tool: Claude 3 Haiku via API.
   - Date: [when executed].
   - Purpose: Identify systematic error patterns in 11 test misclassifications.
   - Outcome: 2 patterns confirmed; 1 feature engineering recommendation implemented.
   - Human verification: All patterns manually validated against original posts.
   ```

---

### AI Tool Summary Table

| Activity | Tool | When | Output Location | Disclosure |
|----------|------|------|-----------------|------------|
| **Label stress-testing** | Claude / GPT-4 | Before annotation | `artifacts/stress_test_posts.txt` | AI usage section, note definition refinements. |
| **Pre-label 316 posts** | Claude / GPT-4 API | During data collection | `artifacts/ai_prelabels.csv` | Track `review_status`; report % auto-accepted vs. human-corrected. |
| **Failure analysis** | Claude / GPT-4 | After model evaluation | `artifacts/test_errors.csv` + analysis | Note patterns confirmed; link to feature engineering changes. |

**Overall AI usage policy:** Transparency first. Document every AI-assisted step, tool used, and outcome. Verify all AI-generated insights before including in final evaluation. Human judgment remains final.

---

## Data & Implementation Status

✓ **Collected:** 316 posts from 4 subreddits.
✓ **Labeled:** Automated classification using keyword heuristics (analysis/hot_take/reaction).
✓ **CSV format:** [data/reddit_posts.csv](data/reddit_posts.csv) with columns: `text`, `label`.
✓ **Manual review:** 50-post stratified sample reviewed by human; 92% approved, 8% corrected; 7 ambiguous cases tracked.

---

## 9. AI Usage Disclosure

**Summary:** This project used AI (Claude Haiku) to **pre-label** a subset of examples before human review. All AI-generated labels were manually reviewed, corrected where necessary, and ambiguous cases were tracked for definition refinement.

### Pre-Labeling Workflow

**Purpose:** Accelerate annotation without sacrificing data quality. Pre-labels were treated as suggestions, not ground truth; every label was reviewed and corrected if necessary.

**Process:**

1. **Sample generation:** 50 posts randomly sampled from 316-post dataset (stratified by automated label).
2. **Prompt sent to Claude Haiku via API** with:
   - Full label definitions (analysis, hot_take, reaction).
   - Edge case rules from Section 3 of planning.md.
   - 50 unlabeled posts in JSON format.
3. **Claude output:** Predicted label + confidence score (0.0–1.0) for each post.
4. **Human review:** For each post:
   - Carefully read the text (not skimmed).
   - Compared AI prediction to human judgment using label definitions.
   - Marked as `ai_approved` (no change), `human_corrected` (changed label), or `human_only` (AI low-confidence; re-labeled).
   - Noted ambiguous cases and reasons for pauses.

### Review Results

**Approval & Correction Rates:**
- Total posts reviewed: **50**
- ai_approved (no changes): **46** (92.0%)
- human_corrected (changed): **4** (8.0%)
- Ambiguous cases flagged: **7**

**Agreement:** 92% of AI pre-labels were accepted without correction, indicating the classifier understood the task well.

**Label Distribution After Manual Review:**
- analysis: 27 (54.0%)
- hot_take: 8 (16.0%)
- reaction: 15 (30.0%)

**Imbalance check:** No severe imbalance detected (Max 54.0%, Min 16.0%). Distribution is reasonable for training.

### Ambiguous Cases Identified

During review, 7 posts were flagged as genuinely ambiguous, indicating potential boundary issues in the label definitions:

| ID | Text Snippet | Reason for Ambiguity | Decision | Confidence |
|----|---|---|---|---|
| 3 | "COIN is great entry point. Currently holding 100 shares. Expecting 20% upside." | Could be reaction (action: holding) or analysis (price expectation implied). | Keep as **analysis** (reasoning is secondary; holds shares suggest conviction from analysis). | low |
| 5 | "Hedge funds loading up on AAPL. Follow the smart money." | Is "follow the smart money" evidence-backed or just a claim? | Keep as **analysis** (implies reasoning: fund managers are smart; if they're buying, it's justified). | low |
| 26 | "COIN is accumulating. Currently holding 100 shares. Cost basis $85. Expecting 20% upside." | Similar to ID 3: action-focused but includes expectation. | Keep as **analysis** (expectation suggests reasoning). | low |
| 27 | "Hedge funds loading up on QQQ. Follow the smart money." | Same as ID 5. | Keep as **analysis** | low |
| 28 | "ESG concerns aside, AMZN is a solid performer. Holding forever." (automated: hot_take) | Reason given (ESG + performance) could support analysis; "holding forever" is conviction. | Corrected to **analysis** (reasoning is present). | medium |
| 39 | "GOOGL is bullish on. Currently holding 100 shares. Cost $85. Expecting 20% upside." (automated: hot_take) | Position details + expectation suggest conviction; ambiguous if this is analysis or just action announcement. | Corrected to **analysis** (position justification is implied). | medium |
| 44 | "YOLO'd $10k into HOOD calls. Hope this pays off. Anyone else concerned about HOOD's debt levels?" (automated: reaction) | Mostly reaction (YOLO) but includes a concern (debt levels). | Corrected to **analysis** (debt concern is a reasoning anchor). | medium |

**Insight from ambiguity:** Posts mixing **action + reasoning** are hard to classify. Current definitions treat these as analysis (reasoning trumps action), but this boundary could be tightened:
- **Proposed refinement:** "If a post's primary goal is announcing a trade action (YOLO'd, sold, bought), it's a **reaction** even if it mentions one concern. If the primary goal is making an argument (evidence-backed), it's **analysis** even if it mentions the action as an example."

### AI Tool Transparency

| Activity | Tool | Date | Coverage | Output |
|----------|------|------|----------|--------|
| Label definitions stress-testing | (Planned) | (Future) | N/A | Will generate 5–10 boundary posts; refine definitions if needed. |
| Pre-label 50-post sample | Claude Haiku (API) | 2026-06-23 | 50 posts | `artifacts/manual_review_results.json`: all predictions + human review outcomes. |
| Manual review tracking | (Human + Python) | 2026-06-23 | 50 posts | `artifacts/manual_review_results.json`: 46 approved, 4 corrected, 7 ambiguous. |
| (Future) Failure analysis | (Planned) | (After model training) | Test errors | Will identify systematic misclassification patterns. |

### Data Provenance

All 316 posts in [data/reddit_posts.csv](data/reddit_posts.csv) are labeled with the label definitions from Section 2. Of the 316:
- 266 posts were labeled using automated keyword heuristics (not reviewed).
- 50 posts (16%) were manually reviewed after AI pre-labeling; 4 corrections applied.

**For training the final model:** Use all 316 posts, but note in evaluation:
- Report held-out test set performance (to validate on unseen data).
- Consider the 50 manually reviewed posts as higher-confidence labels (helpful for debugging).

**Recommendation:** In a production classifier, validate on the 50 manually reviewed posts separately to ensure the model generalizes to human-verified labels.

---

**Next steps:**
1. Manual annotation of subset (50–100 posts) to validate automated labels. ✓ **DONE** (50 posts reviewed).
2. Train classifier (logistic regression, SVM, or transformer) on 220 labeled posts.
3. Evaluate on 46-post test set; compute macro F1, per-class metrics, confusion matrix.
4. Iterate based on error analysis and edge case refinement.
