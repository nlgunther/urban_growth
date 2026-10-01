# Design: quantities, relationships and investment use

Sources: Brueckner (1987) "The structure of urban equilibria" (cited B(n) = its equation n) and the
note `muth_mills_revisited.tex`. An independent Opus review corrected several claims in the first
draft; the corrections are folded in and listed in section 6.

## 1. The quantities

**Primitives (inputs).**

| Symbol | Meaning | Package | Source / typical value |
|---|---|---|---|
| y | income at the CBD | `Spec.y` | B§2 |
| t | commuting cost per mile | `Spec.t` | B§2; footnote 2 allows T(x) |
| r_A | farmland rent | `Spec.rA` | B(18) |
| θ | radians of buildable land | `Spec.theta` | B(19); Saiz 2010 (water, slopes) |
| L or u | population (closed) or utility (open) | `Spec.L`, `Spec.u` | B§3.1 vs §3.2 |
| ε | migration elasticity (0 closed, ∞ open) | `Spec.migration` | extension (Redding–Rossi-Hansberg) |
| α (c0, q0) | housing budget share (subsistence terms) | `StoneGeary` | ≈0.25 (Davis–Ortalo-Magné) |
| β, i | capital elasticity (1−β = land share), capital price | `CobbDouglasTech` | β≈0.8 (Combes et al. 2021) |
| S_cap | height limit | `CobbDouglasTech.S_cap` | Bertaud–Brueckner 2005 |
| ρ | discount rate (valuation only) | `land_value(rho=)` | extension |

**Local endogenous quantities, all functions of net income m = y − t x and u (note eq. Pm).**
Floor-space price p (B(1)–B(5)), dwelling size q (B(6)–B(9)), building height S (B(11)),
land rent r = R(p) (B(12), B(15)–B(16)), density D = h(S)/q. Two identities tie them together:
∂p/∂x = −t/q and ∂r/∂x = −t D.

**City-wide endogenous quantities.** Radius x̄ and boundary price p̄ = R⁻¹(r_A) (B(18); p̄ depends
only on r_A and technology: the anchor), u (closed) or L (open) (B(19)); the rent-integral
identity ∫(r − r_A)dx = tL/θ (B appendix 3a), used as a solver diagnostic.

**Derived quantities worth tracking.** γ = 1/(α(1−β)) (=20 at the calibration); density gradient
b ≈ (γ−1)t/y; central rent ratio r(0)/r_A; commuting share t x̄/y; total land rent, urban area,
floor space, housing bill; E and ē_u (the weights in B(20)–B(31)); the rotation pivots x̂ (income)
and x* (commuting cost).

**Sensitivities (what Brueckner proves, B(20)–B(31), and the package computes).** du, dx̄, dp(x),
dr(x) for L, r_A, y, t (and θ, α, i numerically). Signature: L and r_A raise prices everywhere;
y rotates counter-clockwise, t clockwise (closed city); in the open city y and t give similarity
transforms and no pivots exist.

**Empirical anchors from the note's post-1987 survey.** β≈0.8; α≈0.25; land-price elasticity to
city population 0.72 and urban-cost elasticity 0.04 (Combes–Duranton–Gobillon 2019);
height–land-price elasticity 0.30–0.45 (Ahlfeldt–McMillen); a highway cuts central population
≈18% (Baum-Snow); VKT elasticity to road capacity ≈1 (Duranton–Turner); height-limit welfare cost
1.5–4.5% (Bertaud–Brueckner); the donut effect of remote work (Ramani–Bloom, Gupta et al.).

## 2. Relationships the package expresses

```
(y, t, rA, θ, α, β, i, S_cap) + [L | u | L,u,ε]
        │
        ▼  m = y − t x
  bid price p(m,u) ──► q = e_p ,  S(p) ,  r = R(p) ,  D = h(S)/q
        │                                  │
        └── boundary: p(x̄) = p̄(rA) ◄───────┘
        ▼
  population ∫θ x D dx = L(u)    ← the one root-find (in u)
        ▼
  aggregates → elasticities → exposure betas → scenario PV (ρ)
```

Architecture (five small modules, the solver only uses each primitive's method interface):
`primitives` (preferences, technology) → `city` (Spec, solve, City) → `statics` (elasticities,
analytic theorem, pivots, betas, response, Monte Carlo) → `valuation` (rent paths to PV). Adding
CES or translog technology, or a transport cost T(x), means adding a class with the same methods.

## 3. What can be predicted for investment, and how much to trust it

**Tier A: signed, testable, recommended.**
1. *Factor decomposition of price-gradient changes.* Population, farmland/supply and α act as level
   shifts; income and commuting cost act as rotations. Regressing observed changes in rent or price
   at several distances on the model's beta columns separates them. Example (closed city,
   elasticity of land rent at 0/8/16/25/32 miles): L: 0.97 at every distance; y: −0.97, 0.16, 1.42,
   3.03, 4.46; t: 1.94, 0.81, −0.45, −2.06, −3.49.
2. *Core-versus-ring spread after a commuting-cost shock.* Sign and ordering are robust across
   specifications and match the donut evidence. The most defensible trade is relative (core vs
   ring), never the level. Remote work (t −40%): radius +37%, central price −18%, price at 30 mi +21%.
3. *Which model applies decides which prediction exists.* Raising the migration elasticity moves the
   income-rotation pivot toward the centre; it disappears between ε≈0.5 and ε≈2 here (central
   income beta −0.97 → −0.47 → +0.88). The t rotation persists and its pivot shrinks. Use a closed
   (low-ε) city for economy-wide shocks, a higher ε for metro-specific ones.
4. *Zoning.* A binding height cap expands the city and lowers utility (Bertaud–Brueckner); the cap
   enters as one parameter, so pricing a rezoning is a `scaled`/re-`solve` call.

**Tier B: usable only after calibration; quote bands.**
- Level elasticities. The land-rent elasticity to city population in the Cobb–Douglas closed city is
  1 − r_A x̄ / ∫r dx (0.968 here). It does not depend on γ, so it cannot be tuned to the empirical
  0.72; the gap reflects cross-city variation in income and openness, and Combes et al.'s land
  prices, not rents. This makes it a discriminating model test rather than a forecast.
- Housing-price elasticity is (1−β) times land's; dwelling rent is exactly α(y − t x) in
  Cobb–Douglas, a cheap cross-section check (rent per dwelling proportional to net income).
- Monte Carlo over α, β, t: the radius 5–95% band is 26–47 miles, the central rent ratio 69–253.
  Level outputs are wide; signs and rotation ordering are stable.
- Interest rates: in the closed Cobb–Douglas city, land rent at fixed x does not depend on the
  capital price i (p ∝ i^β, heights and u adjust). Rate sensitivity of land value enters through
  capitalisation (ρ) only, so the package should not be used to forecast rate effects until i and ρ
  are linked (section 5).

**Tier C: do not claim.** Timing or price paths; office and other commercial real estate
(employment is fixed at the CBD); declining cities (durable housing, Glaeser–Gyourko); specific
transit-project valuation (needs t(x, angle) or an access index); edge-land conversion values
(needs conversion cost and uncertainty, Capozza–Helsley); growth-premium magnitudes. The current
`land_value` premium is uniform inside the city only because Cobb–Douglas shifts ln p uniformly,
and the near-100% "growth share" of unbuilt land is true by construction.

**Leverage note.** Differential rent r − r_A near the edge has a huge beta (3.3 at 31 mi vs 1.0 at
5 mi for L) only because the base is small: ε_{r−r_A} = ε_r · r/(r − r_A). It is an option-like delta
for sizing, not new information.

## 4. Numerical facts verified in this build

Calibrated city: x̄ = 33.03 mi, central density 6,172/sq mi (edge 55), rent ratio 145, edge commuting
share 22%, rent-identity residual 1e-13. The note's table matches. Infinitesimal pivots are x̂ = 6.92,
x* = 13.24 miles; the note's 7.2 and 12.6 (and 16.6 for remote work) are finite-shock crossings and
depend on size and sign of the shock (t: 12.64 at +10%, 13.91 at −10%, 16.60 at −40%).
Analytic comparative statics agree with finite differences to 1e-5 for Cobb–Douglas and Stone–Geary.

## 5. Roadmap (reviewer's order)

1. Partly open city — **done** (`migration`).
2. Calibration module: invert observed density gradient, central rent ratio, edge commuting share,
   x̄ into (γ, t, u); needs real metro data (Census tracts, ACS, land-value series).
3. Link i = (ρ + δ) × construction cost to the capitalisation rate so rate shocks move p̄, heights,
   x̄ and values together.
4. Capozza–Helsley conversion cost, then the stochastic version with option value and timing.
5. Glaeser–Gyourko durable stock: kinked supply, asymmetric decline.
6. θ(x) and a city supply-elasticity output, to compare with Saiz.
7. Multiple income groups with sorting; 8. endogenous amenities and employment (Lucas–Rossi-Hansberg).

## 6. Corrections adopted after the Opus review

- The 0.97 population elasticity is γ-independent (my draft called it hypersensitive to γ).
- Pivots exist only for a mostly closed city; every claim now says which case it assumes.
- Infinitesimal and finite pivots are distinguished. The note's table labels finite crossings with
  the theorem's symbols x̂ and x*; consider relabelling there.
- Growth-share of unbuilt land dropped as an output; the uniform premium is flagged as an artifact.
- `differential=True` now subtracts the shocked r_A (bug fixed; sign at the edge was wrong).
- Added asset choice (land, price, dwelling), α and i shocks, bracket checks that raise instead of
  silently misconverging, and explicit errors for unset parameters.
- Open items: split the quadrature at the cap kink (error ≈1e-6 at n=400, acceptable); WFH should be
  run with `{"t": 0.6, "alpha": 1.1}` to include the demand side.
