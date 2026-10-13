// Observable Framework configuration: https://observablehq.com/framework/config
export default {
  title: "Olist Analytics",
  root: "src",
  base: "/olist-analytics/",
  style: "style.css",
  pages: [
    {name: "Growth", path: "/growth"},
    {name: "Retention", path: "/retention"},
    {name: "Customers", path: "/customers"},
    {name: "Delivery & satisfaction", path: "/delivery"},
    {name: "Methodology", path: "/methodology"}
  ],
  pager: true,
  search: false,
  toc: false,
  head: '<meta name="description" content="E-commerce analytics on the Olist dataset: growth, retention, customer segments and delivery.">',
  footer:
    'Data: <a href="https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce">Brazilian E-Commerce Public Dataset by Olist</a> (CC BY-NC-SA 4.0). ' +
    'Code: <a href="https://github.com/mvakh975-wq/olist-analytics">github.com/mvakh975-wq/olist-analytics</a>.'
};
