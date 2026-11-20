-- The win rate mart's won amount adds up to the deal table's, to the cent. Returns a row if not.
with mart as (select sum(won_amount) as total from {{ ref('mart_win_rate_by_close_quarter') }}),
     deals as (select sum(amount) as total from {{ ref('fct_deals') }} where is_won)
select mart.total as mart_total, deals.total as deals_total
from mart cross join deals
where abs(coalesce(mart.total, 0) - coalesce(deals.total, 0)) > 0.005
