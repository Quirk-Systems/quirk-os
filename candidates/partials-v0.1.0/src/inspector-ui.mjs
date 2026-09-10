/** Browser/DOM controller. Dependencies are injected so the same handlers can be tested locally. */
export function mountDecisionInspector(document, context, api) {
  const get=id=>document.getElementById(id);
  const form=get('decision-form'),status=get('status'),preview=get('preview'),output=get('decision-json'),download=get('download');
  const sources=[...document.querySelectorAll('input[name="source"]')];
  const responses=[...document.querySelectorAll('input[name="response"]')];
  const rationale=get('rationale'),nextMove=get('next-move'),finish=get('finish-condition');
  const drafts=new Map();let sourceRef=null,prepared=null;
  const say=text=>{status.textContent=text;};
  const invalidate=()=>{prepared=null;download.disabled=true;preview.hidden=true;output.value='';};
  try{api.assertDecisionContext(context);}catch{say('This comparison context is invalid. Rebuild it from the retained requests.');get('decision-fields').disabled=true;get('prepare').disabled=true;return;}
  if(!context.options.length){say('No proposed repairs are available in this comparison.');get('decision-fields').disabled=true;get('prepare').disabled=true;return;}
  const option=()=>context.options.find(x=>x.source_ref===sourceRef);
  const draft=()=>drafts.get(sourceRef);
  function remember() {
    if(sourceRef===null)return;
    const d=draft();d.rationale=rationale.value;
    if(d.response==='revised'){d.next=nextMove.value;d.finish=finish.value;}
  }
  function render() {
    const selected=option(),d=draft();
    get('decision-fields').disabled=!selected;
    if(!selected)return;
    get('chosen-source').textContent=selected.source_ref;
    responses.forEach(input=>{input.checked=input.value===d.response;});
    rationale.value=d.rationale;
    const deferred=d.response==='deferred';
    get('move-fields').hidden=deferred;
    nextMove.disabled=deferred;finish.disabled=deferred;
    nextMove.readOnly=d.response!=='revised';finish.readOnly=d.response!=='revised';
    nextMove.value=d.response==='revised'?d.next:selected.proposed_repair.acceptance_criteria[0];
    finish.value=d.response==='revised'?d.finish:selected.proposed_repair.acceptance_criteria.join(' ');
    get('move-help').textContent=d.response==='revised'?'Write the next move and what finished means.':'The proposed move is shown below. Choose “Revise it” to edit.';
    say('Choose your response, add a rationale, then preview the unsigned record.');
  }
  sources.forEach(input=>input.addEventListener('change',()=>{
    if(!input.checked)return;
    if(!context.options.some(row=>row.source_ref===input.value)){invalidate();say('That repair is not in this saved comparison. Rebuild the panel.');return;}
    remember();sourceRef=input.value;
    if(!drafts.has(sourceRef))drafts.set(sourceRef,{response:null,rationale:'',next:option().proposed_repair.acceptance_criteria[0],finish:option().proposed_repair.acceptance_criteria.join(' ')});
    invalidate();render();
  }));
  responses.forEach(input=>input.addEventListener('change',()=>{
    if(sourceRef===null||!input.checked)return;
    remember();draft().response=input.value;invalidate();render();
  }));
  for(const input of [rationale,nextMove,finish])input.addEventListener('input',()=>{remember();invalidate();say('Draft changed. Preview it again before exporting.');});
  form.addEventListener('submit',event=>{
    event.preventDefault();invalidate();
    if(sourceRef===null){say('Choose one proposed repair first.');sources[0].focus();return;}
    remember();const d=draft();
    if(!d.response){say('Choose whether to use, revise, or defer this move.');responses[0].focus();return;}
    try {
      prepared=api.buildUnsignedDecision(context,{source_ref:sourceRef,response:d.response,rationale:d.rationale,next_move:d.response==='deferred'?null:nextMove.value,finish_condition:d.response==='deferred'?null:finish.value,captured_at:api.now()});
      output.value=JSON.stringify(prepared,null,2);preview.hidden=false;download.disabled=false;
      say('Ready to export. This is an unsigned decision, not execution or approval.');
      get('preview-heading').focus();
    } catch(error){
      const fields=[['answer.rationale',rationale,'Add a rationale of 1–2,000 characters.'],['answer.next_move',nextMove,'Write a next move of 1–4,000 characters.'],['answer.finish_condition',finish,'Write a finish condition of 1–4,000 characters.']];
      const field=fields.find(([key])=>error.message.startsWith(key+':'));
      if(field){say(field[2]);field[1].focus();}
      else if(error.message.startsWith('answer.captured_at:'))say('The capture time is invalid or precedes the source. Check your device clock and preview again.');
      else say(error.message);
    }
  });
  download.addEventListener('click',()=>{
    if(!prepared)return;
    try{api.download(JSON.stringify(prepared,null,2)+'\n');say('Download requested. If your viewer blocks it, copy the JSON below.');}
    catch{say('This viewer could not download the file. Copy the JSON below instead.');}
  });
  say('Choose one proposed repair. Nothing is selected yet.');
}
