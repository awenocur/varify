define([],function(){var t=function(t,e,i){var n=t.children(),o=n.size();return 0>e&&(e=Math.max(0,o+1+e)),t.append(i),o>e&&n.eq(e).before(n.last()),t};return{insertAt:t}});
//@ sourceMappingURL=dom.js.map