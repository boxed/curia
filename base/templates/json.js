{% load i18n %}{% load auth %}
parent.owner_info.document.body.innerHTML = "{% filter javascript_string_escape %}{{ owner_info }}{% endfilter %}";
document.body.innerHTML = "{% filter javascript_string_escape %}{{ main }}{% endfilter %}";
