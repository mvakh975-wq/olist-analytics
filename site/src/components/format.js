import * as d3 from "npm:d3";

export const integer = d3.format(",d");
export const pct = (value, digits = 1) => d3.format(`.${digits}%`)(value);
export const millionsBRL = (value) => `${d3.format(",.2f")(value / 1e6)} M BRL`;
export const brl = (value) => `${d3.format(",.0f")(value)} BRL`;
export const signed = (value, digits = 2) => d3.format(`+.${digits}f`)(value).replace("-", "−");
export const stars = (value) => d3.format(".2f")(value);
export const month = d3.utcFormat("%b %Y");

/** Dates arrive as ISO strings in the JSON aggregates; charts need Date objects. */
export const asDate = (value) => (value instanceof Date ? value : new Date(value));
