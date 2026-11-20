"""
Ten routine questions Sales and RevOps ask, each with the answer computed from the models.
The AI never sees `truth`: it gets the docs and the question, and writes SQL. score.py runs that SQL
and compares its answer with `truth`.
"""

QUESTIONS = [
    {"id": "q1", "ask": "What was our win rate in Q2 2026?", "kind": "rate",
     "truth": "select win_rate from main.mart_win_rate_by_close_quarter where quarter = '2026-Q2'"},
    {"id": "q2", "ask": "How many deals did we win in Q3 2026?", "kind": "count",
     "truth": "select deals_won from main.mart_win_rate_by_close_quarter where quarter = '2026-Q3'"},
    {"id": "q3", "ask": "Of all deals that ever reached Contract sent, what share went on to be won?", "kind": "rate",
     "truth": "select 1.0 * sum(deals_reached_to) / sum(deals_reached_from) from main.mart_stage_conversion where from_stage = 'Contract sent'"},
    {"id": "q4", "ask": "What was the median number of days from creation to win, for deals won in Q1 2026?", "kind": "days",
     "truth": "select median_days_to_win from main.mart_deal_velocity where quarter = '2026-Q1'"},
    {"id": "q5", "ask": "How much open pipeline (total amount) is sitting in Contract sent right now?", "kind": "amount",
     "truth": "select open_amount from main.mart_open_pipeline where stage = 'Contract sent'"},
    {"id": "q6", "ask": "What win rate did we report for Q2 2026 at that quarter's pipeline review?", "kind": "rate",
     "truth": "select win_rate_reported from main.mart_win_rate_reported_vs_now where quarter = '2026-Q2'"},
    {"id": "q7", "ask": "Which sales rep had the highest win rate in Q3 2026?", "kind": "text",
     "truth": "select owner_name from main.mart_owner_win_rate where quarter = '2026-Q3' order by win_rate desc limit 1"},
    {"id": "q8", "ask": "For the deals created in Q1 2026, what share have we won so far?", "kind": "rate",
     "truth": "select win_rate from main.mart_win_rate_by_created_cohort where cohort_quarter = '2026-Q1'"},
    {"id": "q9", "ask": "How many deals were pushed back to an earlier stage at least once?", "kind": "count",
     "truth": "select count(*) from main.fct_deals where was_moved_back"},
    {"id": "q10", "ask": "What was the total closed-won amount in Q3 2026?", "kind": "amount",
     "truth": "select won_amount from main.mart_win_rate_by_close_quarter where quarter = '2026-Q3'"},
]

# Questions no single mart answers directly: the AI has to know what a column means (stage ids vs
# labels, summing counts rather than averaging rates, percentage points). This is where docs matter.
HARD = [
    {"id": "h1", "ask": "Did our win rate go up or down from Q1 2026 to Q2 2026, and by how many percentage points? (Q2 minus Q1)", "kind": "points",
     "truth": "select (select win_rate from main.mart_win_rate_by_close_quarter where quarter = '2026-Q2') - (select win_rate from main.mart_win_rate_by_close_quarter where quarter = '2026-Q1')"},
    {"id": "h2", "ask": "How many deals are sitting in Contract sent right now that were created before Q4 2026?", "kind": "count",
     "truth": "select count(*) from main.fct_deals where stage_id = 'contractsent' and created_at < timestamp '2026-10-01'"},
    {"id": "h3", "ask": "Across all deals, what share of deals that reached Qualified to buy went on to Presentation scheduled?", "kind": "rate",
     "truth": "select 1.0 * sum(deals_reached_to) / sum(deals_reached_from) from main.mart_stage_conversion where from_stage = 'Qualified to buy'"},
    {"id": "h4", "ask": "What was the average amount of the deals we won in Q3 2026?", "kind": "amount",
     "truth": "select avg(amount) from main.fct_deals where is_won and closed_quarter = '2026-Q3'"},
    {"id": "h5", "ask": "How many deals did Sales rep B win in 2026 so far, across all quarters?", "kind": "count",
     "truth": "select sum(deals_won) from main.mart_owner_win_rate where owner_name = 'Sales rep B' and quarter like '2026-%'"},
    {"id": "h6", "ask": "What was the total amount of the deals we lost in Q3 2026?", "kind": "amount",
     "truth": "select sum(amount) from main.fct_deals where is_lost and closed_quarter = '2026-Q3'"},
    {"id": "h7", "ask": "How much has Q1 2026's win rate changed since we reported it, in percentage points (now minus reported)?", "kind": "points",
     "truth": "select change_since_reported from main.mart_win_rate_reported_vs_now where quarter = '2026-Q1'"},
    {"id": "h8", "ask": "What share of the deals created in Q3 2026 are still open?", "kind": "rate",
     "truth": "select share_still_open from main.mart_win_rate_by_created_cohort where cohort_quarter = '2026-Q3'"},
    {"id": "h9", "ask": "How many of the deals that closed in Q2 2026 had been pushed back to an earlier stage at least once?", "kind": "count",
     "truth": "select count(*) from main.fct_deals where closed_quarter = '2026-Q2' and was_moved_back"},
    {"id": "h10", "ask": "What is the median number of days to win, across all deals won in 2026 so far?", "kind": "days",
     "truth": "select percentile_cont(0.5) within group (order by days_to_close) from main.fct_deals where is_won and closed_quarter like '2026-%'"},
]
