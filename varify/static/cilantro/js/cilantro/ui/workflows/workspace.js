var __hasProp={}.hasOwnProperty,__extends=function(t,e){function n(){this.constructor=t}for(var i in e)__hasProp.call(e,i)&&(t[i]=e[i]);return n.prototype=e.prototype,t.prototype=new n,t.__super__=e.prototype,t};define(["underscore","marionette","../core","../base","../query"],function(t,e,n,i,o){var r,s;return r=function(t){function e(){return s=e.__super__.constructor.apply(this,arguments)}return __extends(e,t),e.prototype.className="workspace-workflow",e.prototype.template="workflows/workspace",e.prototype.regions={queries:".query-region",publicQueries:".public-query-region",editQueryRegion:".save-query-modal",deleteQueryRegion:".delete-query-modal"},e.prototype.regionViews={queries:o.QueryList},e.prototype.initialize=function(){if(this.data={},n.isSupported("2.2.0")&&!(this.data.publicQueries=this.options.public_queries))throw new Error("public queries collection required");if(!(this.data.queries=this.options.queries))throw new Error("queries collection required");if(!(this.data.context=this.options.context))throw new Error("context model required");if(!(this.data.view=this.options.view))throw new Error("view model required");return this.on("router:load",function(){return n.panels.context.closePanel({full:!0}),n.panels.concept.closePanel({full:!0})})},e.prototype.onRender=function(){var t,e,i=this;return e=new this.regionViews.queries({editQueryRegion:this.editQueryRegion,deleteQueryRegion:this.deleteQueryRegion,collection:this.data.queries,context:this.data.context,view:this.data.view,editable:!0}),this.queries.show(e),n.isSupported("2.2.0")?(t=new this.regionViews.queries({collection:this.data.publicQueries,context:this.data.context,view:this.data.view,title:"Public Queries",emptyMessage:"There are no public queries. You can create a new, public query by navigating to the 'Results' page and clicking on the 'Save Query...' button. While filling out the query form, you can mark the query as public which will make it visible to all users and cause it to be listed here."}),this.data.queries.on("sync",function(){return i.data.publicQueries.fetch({add:!0,remove:!0,merge:!0})}),this.publicQueries.show(t)):void 0},e}(e.Layout),{WorkspaceWorkflow:r}});
//@ sourceMappingURL=workspace.js.map