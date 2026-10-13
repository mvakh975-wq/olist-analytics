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
  // link previews (LinkedIn, Telegram, e-mail) use the Open Graph tags
  head: [
    '<meta name="description" content="E-commerce analytics on the Olist dataset: growth, retention, customer segments and delivery.">',
    '<meta property="og:type" content="website">',
    '<meta property="og:title" content="Olist e-commerce analytics: growth, retention and delivery">',
    '<meta property="og:description" content="~98,000 orders from a Brazilian marketplace: why growth stalled, why almost nobody buys twice, and what late delivery does to reviews.">',
    '<meta property="og:url" content="https://mvakh975-wq.github.io/olist-analytics/">',
    '<meta property="og:image" content="https://raw.githubusercontent.com/mvakh975-wq/olist-analytics/main/docs/images/social.png">',
    '<meta property="og:image:width" content="1200">',
    '<meta property="og:image:height" content="630">',
    '<meta name="twitter:card" content="summary_large_image">'
  ].join("\n"),
  footer:
    'Data: <a href="https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce">Brazilian E-Commerce Public Dataset by Olist</a> (CC BY-NC-SA 4.0). ' +
    'Code: <a href="https://github.com/mvakh975-wq/olist-analytics">github.com/mvakh975-wq/olist-analytics</a>.'
};
