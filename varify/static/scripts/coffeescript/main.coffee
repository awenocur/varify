###
The 'main' script for bootstrapping the default Cilantro client. Projects can
use this directly or emulate the functionality in their own script.
###

require
    config:
        tpl:
            variable: 'data'

, [
    'cilantro',
    'project/ui',
    'project/csrf',
    'tpl!templates/varify/tables/header.html',
    'tpl!templates/varify/empty.html',
    'tpl!templates/varify/modals/result.html'
], (c, ui, csrf, header, empty, result) ->

    # Session options
    options =
        url: c.config.get('url')
        credentials: c.config.get('credentials')

    # Define custom templates
    c.templates.set('varify/tables/header', header)
    c.templates.set('varify/empty', empty)
    c.templates.set('varify/modals/result', result)

    # Globally disable stats on all fields
    c.config.set('fields.defaults.form.stats', false)

    # Disable charts for all the types they are enabled for in the default
    # Cilantro config.
    c.config.set('fields.types.number.form.chart', false)
    c.config.set('fields.types.date.form.chart', false)
    c.config.set('fields.types.time.form.chart', false)
    c.config.set('fields.types.datetime.form.chart', false)

    c.ready ->

        # Open the default session defined in the pre-defined configuration.
        # Initialize routes once data is confirmed to be available
        c.sessions.open(options).then ->

            # Define routes
            routes = [
               id: 'query'
               route: 'query/'
               view: new c.ui.QueryWorkflow
                   context: @data.contexts.session
                   concepts: @data.concepts.queryable
            ,
                id: 'results'
                route: 'results/'
                view: new ui.ResultsWorkflow
                    view: @data.views.session
                    context: @data.contexts.session
                    concepts: @data.concepts.viewable
                    # The differences in these names are noted
                    results: @data.preview
                    exporters: @data.exporter
                    queries: @data.queries
            ]

            # Query URLs supported as of 2.2.0
            if c.isSupported('2.2.0')
                routes.push
                    id: 'query-load'
                    route: 'results/:query_id/'
                    view: new c.ui.QueryLoader
                        queries: @data.queries
                        context: @data.contexts.session
                        view: @data.views.session

            # Workspace supported as of 2.1.0
            if c.isSupported('2.1.0')
                data =
                    queries: @data.queries
                    context: @data.contexts.session
                    view: @data.views.session

                # Public queries supported as of 2.2.0
                if c.isSupported('2.2.0')
                    data.public_queries = @data.public_queries

                routes.push
                    id: 'workspace'
                    route: 'workspace/'
                    view: new c.ui.WorkspaceWorkflow(data)

            # Register routes and start the session
            @start(routes)
