define(["underscore","./base"],function(t,e){var i=function(t){if(!t.href)return"Untitled";var e,i=t.href;return e="/"===i.charAt(i.length-1)?i.substr(0,i.length-1).split("/"):i.split("/"),e.length>0?e[e.length-1].toUpperCase():"Untitled "+i},n=e.Model.extend({idAttribute:"type"}),s=e.Collection.extend({model:n,parse:function(e){var n=[];return t.each(e._links,function(e,s){"self"!==s&&(e=t.extend({type:s},e),e.title||(e.title=i(e)),n.push(e))}),n}});return{ExporterModel:n,ExporterCollection:s}});
//@ sourceMappingURL=exporter.js.map