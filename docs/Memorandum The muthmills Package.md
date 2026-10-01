# Memorandum: The muthmills Package

Sep 30, 2026 · @Ken

## Purpose and summary

`muthmills` is a tested Python package that turns the Muth–Mills monocentric-city model, as restated in our technical note on Brueckner (1987), into numbers you can shock. It is best used to predict the signed spatial pattern of price, rent and density changes, not levels or timing.

Given income, commuting cost, farmland rent, housing technology and population (or utility), it solves the city and reports, at every distance from the centre, the price of floor space, land rent, building height, dwelling size and density. It then shows how each responds to population growth, income growth, commuting-cost changes (transit, remote work), farmland rent and zoning.

The strongest current use is a relative core-versus-ring view after commuting-cost or remote-work shocks. Several other uses can be added cheaply, and a few are outside what a single-centre equilibrium model can do. Sections 3 to 5 separate the three groups.

## The package

The package solves one equation: the city's population must equal the sum of households housed out to the boundary. Everything else follows from net income m = y − t·x at distance x and from utility u.

**Inputs.** Income y, commuting cost t, farmland rent r\_A, buildable angle θ, and either population L (closed city), utility u (open city), or both with a migration elasticity (partly open). Also housing budget share α, capital elasticity β (land share 1 − β), capital price i, and an optional height cap.

**Outputs.** At each distance: floor-space price p, dwelling size q, building height S, land rent r and density D. For the city: radius, boundary price (set only by r\_A and technology), u or L, and totals such as land rent, floor space and commuting cost.

**Structure.** Five small modules, each building on the one before.

| Module | Role |
| --- | --- |
| `primitives` | Preferences (Stone–Geary, with Cobb–Douglas as the special case) and housing technology with a height cap |
| `city` | Spec, `solve`, City profiles and aggregates for closed, open and partly open cities |
| `statics` | Elasticities, the note's analytic formulas, rotation pivots, location betas, shock responses, Monte Carlo |
| `valuation` | Present value of land rent along a scenario path |
| `tests` | 30 tests, including reproduction of the note's calibrated city |

**Verification.** The calibrated city matches the note: radius 33.03 miles, central density about 6,170 households per square mile, central rent 145 times farmland rent, edge commuting share 22%. The rent-integral identity holds to 1e-13. The note's closed-city formulas agree with finite differences to about 1e-5, for Cobb–Douglas and for a non-homothetic Stone–Geary case. An independent Opus review audited the economics and code; its corrections are adopted.

## Current use cases

Five uses are supported today, ranked by how well the evidence and the package back them.

1. **Commuting-cost and remote-work scenarios.** Shock t (and optionally the housing budget share α) in a closed city and read the percent change in price, rent and radius by distance. With commuting cost down 40%, the radius grows 37%, central prices fall about 18% and prices at 30 miles rise about 21%. This supports a relative core-versus-ring view, not a level forecast.
2. **Decomposing observed gradient changes into drivers.** Location betas give one exposure column per shock: population and farmland rent shift levels, income and commuting cost rotate the gradient. Regressing observed changes in rent or price at several distances on these columns shows which driver a metro's move resembles. Varying the migration elasticity shows how openness changes the answer.
3. **Zoning and supply-constraint pricing.** A height cap or a smaller buildable angle is one parameter and a re-solve. The result is the capped city's larger radius, lower utility and the land-value wedge by distance, a first look at what a rezoning is worth. Expect direction and relative size, not precise dollars.
4. **Model testing against real metros.** Compare model and observed moments: density gradient, central rent ratio, edge commuting share, radius, and the population elasticity of land rent (0.97 in the model against 0.72 in French data). In Cobb–Douglas, rent per dwelling equals α(y − t·x), an easy cross-section test.
5. **Scenario valuation with uncertainty bands.** `land_value` turns paths for population, income or commuting cost into present values by distance, and `propagate` puts Monte Carlo bands on any output. In a 200-draw run the radius band was 26 to 47 miles and the central rent ratio 69 to 253. Treat growth-premium magnitudes cautiously until conversion cost and an interest-rate link are added.

**One structural point governs all five.** The income rotation exists only when the city is mostly closed. As the migration elasticity rises, the pivot moves toward the centre and vanishes between 0.5 and 2 in our example, turning income growth into a level lift. Use a closed city for economy-wide shocks and a more open one for metro-specific shocks.

## Extensions that can be added

The easiest addition is a general commuting-cost function T(x), which enables radial transit and highway valuation. The partly open city, suggested by the review as the first build, is already done.

| Extension | Difficulty | What it unlocks | What it needs |
| --- | --- | --- | --- |
| General commuting cost T(x) | Low: about 30–40 lines | Radial transit or highway uplift by distance, concave rail costs | Net income y − T(x), boundary by root-find; the linear case must reproduce every current result |
| Interest-rate link | Low to medium | Rate shocks that move boundary price, heights, radius and capitalisation together | Capital price i = (ρ + δ) × construction cost tied to the valuation rate ρ |
| Supply-elasticity output and θ(x) | Low to medium | Comparison with Saiz-style housing supply elasticities; location-varying constraints | Output of dln(floor space)/dln p; angle varying with distance |
| Calibration module | Medium | Turns use case 4 into estimation of (γ, t, u) from observed gradients | Real metro data: tract density, rents, land values, commuting share |
| Declining cities (Glaeser–Gyourko) | Medium | Asymmetric adjustment: housing is added easily and removed slowly | A state variable for the existing stock and kinked supply, so a simple dynamic layer |
| Conversion cost and option value (Capozza–Helsley) | Medium to high | Pricing of unbuilt edge land and conversion timing | Conversion cost first, then a stochastic version with uncertainty |
| Multiple income groups with sorting | Medium to high | Who lives where; gentrification-type patterns | A new solver structure with group-specific bid prices |
| Endogenous amenities and employment | High | Amenity-driven sorting; polycentric cities | Leaves the single-centre model; see the next section |

**Order we would build.** Start with T(x) and the interest-rate link because they are small and remove known weaknesses. Then the calibration module, which needs data and is the gateway to real use. The conversion-cost work follows, since edge-land value is where the current valuation layer is weakest.

## What cannot be added within this framework

Four things are out of reach for a single-centre equilibrium model, however much code is added.

1. **Timing and price paths.** The model describes long-run equilibria. Adjustment speed depends on durability, expectations, financing and regulation, none of which it has. Scenario paths in `land_value` are a structured sensitivity tool, not a forecast.
2. **Office and commercial real estate.** Employment is fixed at the central business district, so there is no demand for office space to shock. This needs endogenous firm location and agglomeration, as in Lucas and Rossi-Hansberg, which is a different model.
3. **Specific transit projects that are not radial.** A single line in one direction, a ring road or station-specific access needs an angular or network access index. That is the quantitative spatial approach of Ahlfeldt and co-authors, a much larger build. Endogenous congestion (Duranton–Turner: road use rises about one-for-one with capacity) would also make t depend on population.
4. **Anything requiring the model to predict levels precisely.** Level effects are sensitive to calibration. The 0.97 land-rent elasticity to population is pinned near one regardless of the land share, so it cannot be tuned to the empirical 0.72.

Two items are harder than they look. Declining cities can be approximated with a stock state variable, but the model cannot capture the neighbourhood cycles that follow. Amenity-driven sorting can be added in a limited form, but explaining why central Paris is rich and central Detroit is poor needs amenity data and a richer model.

## Risks, caveats and next steps

The main risk is over-reading model magnitudes, so users should rely on signs and relative ordering and quote bands for levels. Five specific cautions apply.

- **Closed versus open matters.** An income rotation exists only for a mostly closed city, so every claim should state which case it assumes.
- **Two kinds of pivot.** The theorem's infinitesimal pivots are 6.9 and 13.2 miles, while the note's table values of 7.2, 12.6 and 16.6 are finite-shock crossings that depend on the size and sign of the shock. The note's table uses the theorem's symbols for the crossings and could be relabelled.
- **Interest rates.** In the closed Cobb–Douglas city, land rent at a given distance does not depend on the capital price. Rate effects on land value come only through capitalisation, so the package should not be used to forecast rate effects yet.
- **Comparisons across α.** Utility is ordinal and cannot be compared across different housing budget shares.
- **Edge leverage.** The very large exposure of differential rent near the boundary is accounting (r divided by r − r\_A), not new information.

**Recommended next steps.**

1. Add the general commuting-cost function T(x) and the interest-rate link.
2. Assemble one metro's tract-level density, rent and commuting data and build the calibration module against it.
3. Add conversion cost before using any edge-land valuation in a decision.
4. Decide whether to relabel the pivots in the note.

Sources: the project note `muth_mills_revisited.tex`, Brueckner (1987), and `docs/DESIGN.md` in the `muthmills` folder, which holds the full quantities table and the review corrections.
