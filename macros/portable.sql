{# The few functions that differ between DuckDB (runs this repo locally) and Redshift (Kit's warehouse). #}

{% macro days_between(start_ts, end_ts) -%}
  {%- if target.type == 'redshift' -%}
    datediff(day, {{ start_ts }}, {{ end_ts }})
  {%- else -%}
    date_diff('day', {{ start_ts }}, {{ end_ts }})
  {%- endif -%}
{%- endmacro %}

{% macro quarter_label(ts) -%}
  cast(extract(year from {{ ts }}) as varchar) || '-Q' || cast(extract(quarter from {{ ts }}) as varchar)
{%- endmacro %}
