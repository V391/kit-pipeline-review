-- Every closed deal is counted in exactly one close quarter, and the counts match the deal table.
with mart as (select sum(deals_won + deals_lost) as n from {{ ref('mart_win_rate_by_close_quarter') }}),
     deals as (select count(*) as n from {{ ref('fct_deals') }} where is_closed)
select mart.n, deals.n from mart cross join deals where mart.n <> deals.n
