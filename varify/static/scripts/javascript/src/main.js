// Generated by CoffeeScript 1.7.1

/*
The 'main' script for bootstrapping the default Cilantro client. Projects can
use this directly or emulate the functionality in their own script.
 */
require({
  config: {
    tpl: {
      variable: 'data'
    }
  }
}, ['cilantro', 'project/ui', 'project/csrf', 'tpl!project/templates/tables/header.html', 'tpl!project/templates/empty.html', 'tpl!project/templates/modals/result.html', 'tpl!project/templates/controls/hgmd.html', 'tpl!project/templates/controls/sift.html', 'tpl!project/templates/controls/polyphen.html', 'tpl!project/templates/workflows/results.html'], function(c, ui, csrf, header, empty, result, hgmd, sift, polyphen, results) {
  var notify_required, options;
  options = {
    url: c.config.get('url'),
    credentials: c.config.get('credentials')
  };
  c.templates.set('varify/tables/header', header);
  c.templates.set('varify/empty', empty);
  c.templates.set('varify/modals/result', result);
  c.templates.set('varify/controls/hgmd', hgmd);
  c.templates.set('varify/controls/sift', sift);
  c.templates.set('varify/controls/polyphen', polyphen);
  c.templates.set('varify/workflows/results', results);
  c.config.set('fields.defaults.form.stats', false);
  c.config.set('fields.types.number.form.chart', false);
  c.config.set('fields.types.date.form.chart', false);
  c.config.set('fields.types.time.form.chart', false);
  c.config.set('fields.types.datetime.form.chart', false);
  c.config.set('fields.instances.27.form.controls', ['multiSelectionList']);
  c.config.set('fields.instances.28.form.controls', ['multiSelectionList']);
  c.config.set('fields.instances.29.form.controls', ['multiSelectionList']);
  c.config.set('fields.instances.61.form.controls', ['multiSelectionList']);
  c.config.set('fields.instances.64.form.controls', ['multiSelectionList']);
  c.config.set('fields.instances.75.form.controls', ['search']);
  c.config.set('fields.instances.68.form.controls', ['singleSelectionList']);
  c.controls.set('Hgmd', ui.HgmdSelector);
  c.controls.set('Sift', ui.SiftSelector);
  c.controls.set('PolyPhen', ui.PolyPhenSelector);
  c.config.set('fields.instances.110.form.controls', ['Hgmd']);
  c.config.set('fields.instances.58.form.controls', ['Sift']);
  c.config.set('fields.instances.56.form.controls', ['PolyPhen']);
  notify_required = (function(_this) {
    return function(concepts) {
      var message, names;
      if (c.data == null) {
        return;
      }
      names = _.map(concepts || [], function(concept) {
        var _ref;
        return (_ref = c.data.concepts.get(concept.concept)) != null ? _ref.get('name') : void 0;
      });
      if (names) {
        message = 'The following concepts are required: ' + names.join(', ');
      } else {
        message = 'There are 1 or more required concepts';
      }
      return c.notify({
        level: 'error',
        message: message
      });
    };
  })(this);
  c.config.set('query.concepts.required', [2]);
  c.on(c.CONTEXT_INVALID, notify_required);
  c.on(c.CONTEXT_REQUIRED, notify_required);
  return c.ready(function() {
    return c.sessions.open(options).then(function() {
      var data, routes;
      routes = [
        {
          id: 'query',
          route: 'query/',
          view: new c.ui.QueryWorkflow({
            context: this.data.contexts.session,
            concepts: this.data.concepts.queryable
          })
        }, {
          id: 'results',
          route: 'results/',
          view: new ui.ResultsWorkflow({
            view: this.data.views.session,
            context: this.data.contexts.session,
            concepts: this.data.concepts.viewable,
            results: this.data.preview,
            exporters: this.data.exporter,
            queries: this.data.queries
          })
        }
      ];
      if (c.isSupported('2.2.0')) {
        routes.push({
          id: 'query-load',
          route: 'results/:query_id/',
          view: new c.ui.QueryLoader({
            queries: this.data.queries,
            context: this.data.contexts.session,
            view: this.data.views.session
          })
        });
      }
      if (c.isSupported('2.1.0')) {
        data = {
          queries: this.data.queries,
          context: this.data.contexts.session,
          view: this.data.views.session
        };
        if (c.isSupported('2.2.0')) {
          data.public_queries = this.data.public_queries;
        }
        routes.push({
          id: 'workspace',
          route: 'workspace/',
          view: new c.ui.WorkspaceWorkflow(data)
        });
      }
      return this.start(routes);
    });
  });
});
