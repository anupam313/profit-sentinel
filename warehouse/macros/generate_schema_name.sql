{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- set client_schema = var('client_schema', target.schema) -%}
    {%- if custom_schema_name is none -%}
        {{ client_schema }}
    {%- else -%}
        {{ client_schema }}_{{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
