define(["underscore","marionette"],function(e,t){var n=t.ItemView.extend({tagName:"span",className:"muted",template:"varify/modals/phenotype/empty",serializeData:function(){return{name:this.options.name}}}),r=t.ItemView.extend({tagName:"li",template:"varify/modals/phenotype/diagnosesItem"}),i=t.CompositeView.extend({template:"varify/modals/phenotype/diagnoses",itemView:r,emptyView:n,itemViewContainer:"[data-target=items]",serializeData:function(){return{name:this.options.name}},itemViewOptions:function(){return{name:this.options.name}}});return{Diagnoses:i}})