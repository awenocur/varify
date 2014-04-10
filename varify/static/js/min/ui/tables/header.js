define(["underscore","marionette"],function(e,t){var n=t.ItemView.extend({tagName:"thead",template:"varify/tables/header",events:{"click th":"onClick"},initialize:function(){this.data={};if(!(this.data.view=this.options.view))throw new Error("view model required")},_getConcept:function(e){var t=parseInt(e.getAttribute("data-concept-id"),10);return t!=null&&!isNaN(t)?t:parseInt(e.parentElement.getAttribute("data-concept-id"),10)},onClick:function(t){var n,r;n=this._getConcept(t.target);if(n==null||isNaN(n))throw new Error("Unrecognized concept ID on column");r=e.find(this.data.view.facets.models,function(e){return e.get("concept")===n}),r==null&&this.data.view.facets.add({concept:n}),e.each(this.data.view.facets.models,function(e){var t;e.get("concept")===n?(t=e.get("sort"),t!=null?t.toLowerCase()==="asc"?(e.set("sort","desc"),e.set("sort_index",0)):(e.unset("sort"),e.unset("sort_index")):(e.set("sort","asc"),e.set("sort_index",0))):(e.unset("sort"),e.unset("sort_index"))}),this.data.view.save()},onRender:function(){e.each(this.data.view.facets.models,function(e){var t,n,r;t=$("th[data-concept-id="+e.get("concept")+"] i");if(t!=null){t.removeClass("icon-sort icon-sort-up icon-sort-down"),n=(e.get("sort")||"").toLowerCase();switch(n){case"asc":r="icon-sort-up";break;case"desc":r="icon-sort-down";break;default:r="icon-sort"}t.addClass(r)}})}});return{Header:n}})