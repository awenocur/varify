define(["underscore","marionette","./body","./header"],function(e,t,n,r){var i=t.CollectionView.extend({tagName:"table",className:"table table-striped",collectionEvents:{"change:currentpage":"showCurrentPage"},itemView:n.ResultBody,itemViewOptions:function(t){return e.defaults({collection:t.series},this.options)},initialize:function(){this.data={};if(!(this.data.view=this.options.view))throw new Error("view model required");this.header=new r.Header({view:this.data.view}),this.$el.append(this.header.render().el);var e=this;this.collection.on("reset",function(){e.collection.objectCount===0?e.$el.hide():(e.header.render(),e.$el.show())})},showCurrentPage:function(e,t){this.children.each(function(e){e.$el.toggle(e.model.id===t)})}});return{ResultTable:i}})