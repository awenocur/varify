define(["underscore","marionette","../core"],function(t,e,i){var n=function(e,i,o){return o=o||[],e?(e[i]&&o.push(e[i]),e.children&&t.each(e.children,function(t){n(t,i,o)}),o):o},o=e.ItemView.extend({className:"context-item",template:"context/item",events:{"click .language":"clickShow","click .actions .remove":"clickRemove","click .state":"clickState","change .state input":"clickState","click .state input":"stopPropagation"},ui:{loader:".actions .icon-spinner",actions:".actions button",state:".state",check:".state input",language:".language"},modelEvents:{request:"showLoadView",sync:"hideLoadView",error:"hideLoadView",change:"renderLanguage","change:enabled":"renderState"},stopPropagation:function(t){t.preventDefault(),t.stopPropagation()},clickShow:function(){i.router.navigate("query",{trigger:!0}),i.trigger(i.CONCEPT_FOCUS,this.model.get("concept"))},clickRemove:function(){this.model.remove()&&this.$el.fadeOut({duration:400,easing:"easeOutExpo"})},clickState:function(e){e.preventDefault();var i=this;t.defer(function(){i.model.toggleEnabled()})},renderEnabled:function(){this.$el.removeClass("disabled"),this.ui.state.attr("title","Disable"),this.ui.check.prop("checked",!0),this.ui.check.attr("checked",!0)},renderDisabled:function(){this.$el.addClass("disabled"),this.ui.state.attr("title","Enable"),this.ui.check.prop("checked",!1),this.ui.check.attr("checked",!1)},renderState:function(){this.model.isEnabled()?this.renderEnabled():this.renderDisabled()},renderLanguage:function(){var t=n(this.model.toJSON(),"language").join(", ");this.ui.language.html(t)},showLoadView:function(){this.ui.loader.show(),this.ui.actions.hide()},hideLoadView:function(){this.ui.loader.hide(),this.ui.actions.show()},onRender:function(){this.ui.loader.hide(),this.renderLanguage(),this.renderState()}});return{ContextItem:o}});
//@ sourceMappingURL=item.js.map