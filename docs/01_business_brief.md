# Business problem and decision

**Decision:** Where should a merchant-growth team allocate its next round of field research before committing acquisition resources?

**Audience:** Merchant acquisition manager, regional sales manager, and business analyst.

**Deliverable:** A ranked investigation shortlist, evidence for each market, a monitoring list, and a practical validation pilot.

This is an independent portfolio case study using PhonePe's public data. It is not employment at PhonePe, commissioned work, or evidence of realized business impact.

## Decision logic

1. Establish demand: current transaction volume, registered users, and growth.
2. Compare demand with acceptance registrations: users and transactions per registered merchant.
3. Exclude missing comparisons and very small bases from the main nationwide ranking.
4. Rank with a transparent score and test alternative weights and minimum sizes.
5. Investigate stable candidates before making an acquisition commitment.

## What this analysis cannot decide alone

It cannot prove how many shops are available to acquire, how many registrations are active, whether customers already pay those shops through another app, or whether the acquisition economics are attractive. No revenue forecast, ROI claim, or guaranteed uplift is produced.

## Project scope

- Source: official PhonePe Pulse, one pinned restated release.
- Trends: 2018 Q1–2026 Q2; decision snapshot: 2026 Q2.
- Grains: state-quarter, district-quarter, state-category-quarter.
- Tools: Python/Pandas, MySQL 8, SQL, basic statistics, Power BI, DAX, Git.
- All payment demand is PhonePe activity, not total Indian UPI activity.
