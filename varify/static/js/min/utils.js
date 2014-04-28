define(["underscore"],function(e){var t=function(e){return e<10?"text-warning":e>=30?"text-success":""},n=function(t){var n=[];if(t&&t.length){var r=e.groupBy(t,"type");for(var i in r)n.push({type:i,effects:r[i]})}return n},r=function(e){var t=[];t.push({type:"variant",phenotypes:e.phenotypes});for(var n=0;n<e.uniqueGenes.length;n++)t.push({type:"gene",phenotypes:e.uniqueGenes[n].phenotypes,gene:e.uniqueGenes[n]});return t},i=function(e){var t;switch(e){case"High":t=1;break;case"Moderate":t=2;break;case"Low":t=3;break;case"Modifier":t=4;break;default:t=5}return t},s=function(){return window.location.href.replace(/\/[^\/]*\/$/,"/")},o=function(e){if(e==null)return;var t=e.split("T");if(t.length!=2)return;var n=t[0].split("-"),r=t[1].split(":");if(n.length!==3&&r.length!==3)return;var i=parseInt(n[0],10),s=parseInt(n[1],10),o=parseInt(n[2],10),u=parseInt(r[0],10),a=parseInt(r[1],10),f=r[2].split("."),l=null,c=null;f.length===1?(l=parseInt(f[0],10),c=0):f.length===2&&(l=parseInt(f[0],10),c=parseInt(f[1],10));if(i&&s&&o&&u&&a&&l){var h=new Date;return h.setUTCFullYear(i),h.setUTCMonth(s-1),h.setUTCDate(o),h.setUTCHours(u),h.setUTCMinutes(a),h.setUTCSeconds(l,c),h}return},u=function(e){var t;switch(e){case 1:t="text-error";break;case 2:t="text-warning";break;default:t=""}return t},a=function(e){return e<30?"text-warning":e>=50?"text-success":""},f=function(t){var n=[],r;return t&&(r=t.get("json"))&&e.each(r.children,function(t){t.concept&&t.concept===2&&(n=e.pluck(t.value,"label"))}),n},l=function(e){return""+s()+e};return{depthClass:t,effectImpactPriority:i,getRootUrl:s,groupEffectsByType:n,groupPhenotypesByType:r,parseISO8601UTC:o,priorityClass:u,qualityClass:a,samplesInContext:f,toAbsolutePath:l}})