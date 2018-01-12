# Metrics

_Generated at {{generated_at}} EST in {{finished_in}}s_

## Schemas

{{#schemas}}
* [{{schema_name}}](#{{schema_name_anchor}})
{{/schemas}}

{{#schemas}}

## {{schema_name}}

### Events

{{#events}}
* [{{event_text}}](#{{event_anchor}})
{{/events}}

{{#events}}
#### {{event_text}}

table: `{{event_name}}`

{{#properties}}
* __{{name}}__
{{/properties}}

```javascript
{{{sample_event}}}
```
{{/events}}

{{/schemas}}
