import {IntakeError} from './intake.mjs';

// JSON.parse validates grammar first. This second pass checks object-key
// uniqueness (including escaped names) before parsed values are trusted.
export function parseUniqueJson(text){
  let parsed;
  try{parsed=JSON.parse(text);}catch{throw new IntakeError('INVALID_JSON','Input must contain valid JSON.');}
  let i=0;
  const space=()=>{while(/\s/.test(text[i]??'') && i<text.length)i++;};
  const string=()=>{
    const start=i++;
    while(i<text.length){const c=text[i++];if(c==='\\')i++;else if(c==='"')return JSON.parse(text.slice(start,i));}
  };
  function value(depth){
    if(depth>30)throw new IntakeError('INPUT_BOUND','JSON nesting exceeds the supported depth.');
    space();
    if(text[i]==='{'){
      i++;space();const keys=new Set();
      if(text[i]==='}'){i++;return;}
      while(true){
        space();const key=string();
        if(keys.has(key))throw new IntakeError('DUPLICATE_JSON_KEY','Duplicate object keys are not accepted.');
        keys.add(key);space();i++;value(depth+1);space();
        if(text[i++]==='}')return;
      }
    }
    if(text[i]==='['){
      i++;space();if(text[i]===']'){i++;return;}
      while(true){value(depth+1);space();if(text[i++]===']')return;}
    }
    if(text[i]==='"'){string();return;}
    while(i<text.length && !/[\s,\]}]/.test(text[i]))i++;
  }
  value(0);return parsed;
}
