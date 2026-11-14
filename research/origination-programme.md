# Origination programme: how to build a line that is worth pricing against

This is the plan for originating lines rather than following them, written so that each
step produces something falsifiable. It covers singles, parlays and player-prop
combinations, and it says plainly which of them this repository can support today and
which it cannot.

Everything below is a **hypothesis until a gate passes**. Nothing here is a pick, and no
figure in this file is a forecast. Where a number is quoted it comes from a committed
dataset and the file says which.

---

## 1. The economics we are trying to beat

A point-spread or total bet at standard **−110** prices needs a **52.38%** win rate to
break even: `1 / (1 + 100/110) = 0.5238`. A winning bet returns 0.909 units, a loser
costs 1.0.

That single number sets the size of the prize. A model that is right 53% of the time
makes about 1.3% per bet before any error in its own probability estimate; a model that
is right 52% loses money. The gap between a good season and a losing one is roughly one
correct bet in a hundred, which is why every gate in this repository is about sample size
and calibration before it is about accuracy.

**Originating is not the same as predicting.** A prediction can be wrong and still be
well priced if it disagrees with the market in the right places. The measurable target is
not "did the favourite win" but "was the price we would have taken better than the price
at the close". That is closing-line value, and section 6 explains why this repository
cannot measure it yet.

---

## 2. The markets, in the order they must be built

The order is a dependency chain, not a preference. Each market consumes the one before
it.

### 2.1 The side (spread)

The only quantity estimated from team strength. The current model (`S = PF/g − PA/g`,
opponent-adjusted) is a baseline; the programme's job is to earn each added term.

| Candidate term | Why it might carry signal | What would falsify it | Status |
|---|---|---|---|
| Opponent-adjusted scoring rate | Already the baseline; correlates 0.87 with win percentage (n = 32) at team level | If the adjustment does not beat raw scoring on out-of-sample spread error | **In the baseline** |
| Availability, priced by depth slot | The model's largest blind spot: 9 of 13 Week-11 lines sit more than 5 points from the market | If pricing the depth slot does not shrink the median gap | **Blocked** on a snap-count source (E2) |
| Rest differential | Short weeks are a known coaching constraint | If a rest term's coefficient is indistinguishable from zero out of sample | **Not started** — needs a verified rest-day source, derivable from the feed |
| Travel and time-zone shift | The international and west-coast-to-east games are natural experiments | If the term adds nothing once rest is controlled | **Not started** — the feed has the dates, not the venues |
| Home-field edge | Currently measured at **+0.07 points**, interval **[−3.59, +3.74]** over 54 games | Already fails: the interval spans zero, so the term cannot be distinguished from none | **Measured, rejected** |
| Market movement (open → current) | The market's own adjustment is information our line does not use | If using the open-to-current move does not improve out-of-sample error on the close | **Not started** — the store now makes it possible |

The home-field row is the model of how this table should behave. The term was measured,
its interval spanned zero, and it was published as a rejection rather than quietly kept
because it is conventional. Every other row must earn the same treatment.

### 2.2 The total

Estimated from scoring and conceding rates, and independent of the side in construction.
The one correlation worth carrying here is that **margin and total are negatively
dependent**: r = −0.31 on n = 57, interval excludes zero. That matters for the parlay
work in section 4 and it does not matter for pricing either single.

### 2.3 The moneyline

**Not a third model.** The moneyline is the side converted through the same distribution,
with σ = 13.47 points measured from 57 official games. Publishing it as an independent
opinion would count one signal twice. It is built last because it is derived last.

Its error mode is σ, not the line. If σ is wrong, the win probability is wrong at every
price, and that shows up as a calibration failure rather than a line failure — which is
why the calibration gate, not the accuracy gate, governs this market.

---

## 3. Signals worth testing, and how each is falsified

Each signal is stated as a claim, with the test that could kill it, pre-registered here
before any result is looked at. This ordering is the whole protection against fitting a
story to a result.

| # | Signal | The claim | The falsification test | Sample needed |
|---|---|---|---|---|
| H1 | Availability shock | A starter-out at depth slot ≥2 shifts the fair line toward the opponent by more than the current model does | Compare the model gap against the market in games with a slot-≥2 absence vs games without; if the difference in gaps is indistinguishable from zero, the claim dies | ≥200 graded games |
| H2 | Line movement | The open-to-current move contains information the model can use | Add the move as a feature in a walk-forward test; if out-of-sample spread error does not improve, it dies | ≥100 graded games |
| H3 | Total drift | Large open-to-close total moves (like the 7-point move in Week 10) are followed by further drift | Measure the close-to-result residual against the size of the move; if uncorrelated, it dies | ≥150 settled games |
| H4 | Rest differential | A short-week team underperforms its line | Same test as H1 with rest as the split | ≥150 games |
| H5 | Correlation-aware parlays | Joint pricing by the measured margin/total dependence beats pricing legs as independent | Compare the model's joint probability with the settled joint frequency, out of sample | ≥100 settled parlays |
| H6 | Prop correlation | Two props on the same team are positively dependent and the joint is mispriced | Compare the model's joint with the settled joint frequency for legs on the same team | ≥200 settled props |

**H6 is not currently testable** and is published anyway, because a pre-registered
hypothesis that cannot be tested yet is honest and a hypothesis invented after seeing the
data is not. It is blocked on the paired player-log source (register B5).

---

## 4. Parlays, same-game combinations and prop combinations

### 4.1 Why a parlay is usually a worse bet than it looks

A two-leg parlay of two −110 legs has a *fair* decimal price of **3.645** — two
independent 52.38% legs multiplied and inverted. A book offering **2.6:1** (decimal 3.60)
is therefore charging only a little over a fair price, and the extra margin is small
compared with what correlation does. That second effect is where the real damage is, and
it is not a margin at all: it is a mispriced probability. Add positive correlation between
legs and the true joint is worse than the product, so a payout that looks close to fair
against an independence assumption can be badly short against the real joint.

The only defensible parlay is one where the model's **joint** probability exceeds the
payout's break-even, and the joint can only be computed from a measured dependence
structure. Section 5 of the integrity note already shows the one pair that is
measurably dependent: **margin and total, r = −0.31**. Two consequences:

- **Favourite + over** has legs that pull against each other. The true joint is **below**
  the product, so an independence-priced payout is worse than it looks.
- **Underdog + under** has legs that pull **with** each other. The true joint is **above**
  the product, which is the only structural reason a parlay could ever be good value.

Neither of those is a recommendation. Both are the direction the measured dependence
gives, and the size of the effect has to be calibrated before either is priced.

### 4.2 Same-game parlays

Same-game parlays have more legs and more correlation than they advertise, and the
provider prices that in. The programme's position: **no same-game parlay is priceable
until H5 clears.** Publishing a joint probability from an assumed independence structure
is exactly the error the correlation gate exists to catch.

### 4.3 Player-prop combinations

Requires three things this repository does not have:

1. an official, machine-readable per-player game log (register B5),
2. a measured correlation between the specific props being combined (register F4), and
3. the offered joint price at stake time (register F6).

Until all three exist, prop combinations are **out of scope by evidence, not by
preference**. The prop *prices* are obtainable — the odds feed carries per-player targets
with open and current numbers — but a price without a probability model is not a signal.

---

## 5. Validation gates: what a strategy must clear to be called a strategy

These are pre-registered thresholds. The first five already exist in the strategy lab;
the last three are new and close the gaps this programme exposes.

| Gate | Test | Threshold | Rationale |
|---|---|---|---|
| G1 data integrity | Every input has a source URL and a capture time, and is knowable before the bet | no exceptions | A number that cannot be dated cannot be used |
| G2 out-of-sample | Walk-forward only, no random splits | every fold | Fitting and testing on the same rows is the most common way to manufacture skill |
| G3 sample size | Settled bets per market | ≥100 | Below this, a 60% hit rate is routine noise |
| **G4 independent signals** *(new)* | Count the number of *uncorrelated* signals, not the number of rows | effective n, not raw n | Nine models correlating 0.92–0.999 are one signal; counting them nine times is how luck gets a job |
| G5 calibration | Brier score and calibration bands on the probability, not the pick | Brier < 0.25 and no band off by more than 0.12 | A model can pick winners and be badly priced |
| G6 economic | Net return **after** the price at stake time | 95% interval lower bound > 0 | Before costs every model looks profitable |
| G7 close-beating | Share of bets with positive closing-line value | ≥55% on ≥100 bets | The only test that does not depend on the scoreboard |
| **G8 survival** *(new)* | Maximum drawdown under the pre-registered staking rule | ≤20% of peak | A strategy that cannot survive its own variance is a strategy only on paper |
| **G9 multiplicity** *(new)* | Every hypothesis ever tested is counted; the α is corrected for all of them | Bonferroni or FDR, stated in advance | Testing twenty ideas and reporting the one that worked is not a signal, it is a search |

**G4 is the gate this project most needs and least wants.** It is the one that says nine
correlated strategies are one strategy, which halves the apparent evidence in the lab
overnight.

---

## 6. Why closing-line value is the target and why it is blocked

Results are noisy. A model can be right for the wrong reason and win, or right for the
right reason and lose, and at a hundred bets the noise dwarfs the signal. Beating the
close is different: it asks whether the price we took was better than the price at the
end, which is a fact about the market rather than about the scoreboard, and it converges
much faster.

It is also **currently unmeasurable here**, because this project has never taken a price.
The price store that now exists starts at 2026-11-14T19:17Z and records what the market
was, not what we got. The honest statement is therefore:

> Closing-line value is the metric this programme is designed around, it is measured as
> **blocked**, and it becomes measurable the first time a row is written before a
> kick-off.

Back-filling it from the store would be reconstructing a price that was never taken, and
that is the one thing this repository has consistently refused to do.

---

## 7. The competition structure, and how not to reward luck

The leaderboard is split into a **signal board** and a **staking board** and the two are
never combined. Rewards attach to the signal board. The mechanism is deliberately boring:

1. **Pre-registration.** Each strategy's rules, thresholds and staking are written down
   before evaluation. Changing them resets its sample.
2. **Paper first.** Every strategy starts in paper mode. Demo and paper returns may be
   published; they may not be paid.
3. **Minimum sample.** No strategy is ranked until it has the sample in G3 and G7.
4. **Public gate results.** Every gate, pass or fail, is published per strategy. A failing
   gate is information, not a verdict. Testing twenty could still produce a lucky pass,
   which is what G9 is for.
5. **Demotion.** A live strategy that trips D1–D5 returns to paper with its sample
   intact, so it can come back.
6. **No reward on bankroll.** Simulation in the integrity note shows identical edges
   producing a 178-unit gain and a 16.79-unit loss under two staking rules. Paying on
   bankroll pays for the rule, not the skill.

**Reward amounts are blank on purpose.** No figure is published anywhere in this
repository because a reward pool is a business decision, and inventing one would be a
fabricated input in the one document whose job is not to have any.

---

## 8. What this programme needs, in dependency order

| Order | Need | Unblocks | Status |
|---|---|---|---|
| 1 | A pre-kickoff capture job | CLV, G7, G8, demotion D1/D5 | **Open** |
| 2 | Weeks 1–9 settled from the reconciling feed | G3, G4, meaningful Brier | **Open** |
| 3 | An official snap-count or playing-time source | E2, H1, the availability term in 2.1 | **Blocked** — no verified source |
| 4 | A ruling on the two conflicting absence windows (F-04) | E3, and the depth table's availability assumption | **Blocked** — human decision |
| 5 | Paired player game logs | F4, H6, every prop combination | **Blocked** — no verified source |
| 6 | The offered joint price for parlays | F5, F6, H5 | **Open** — extend the capture |
| 7 | A written staking rule | D2, G8, every ROI comparison | **Open** — policy decision |

The first two are cheap and unlock the most. The third and fifth are the two genuine
research dependencies, and neither can be replaced with an estimate.
