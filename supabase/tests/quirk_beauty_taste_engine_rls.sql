-- Transactional proof for the Quirk Beauty Taste Engine candidate projection.
-- Run only on an isolated Supabase development branch after the matching migration.
begin;

do $$ begin
 if has_schema_privilege('anon','beauty','usage') then raise exception 'QB-RLS-001 anon schema usage'; end if;
 if has_table_privilege('anon','beauty.taste_sessions','select') then raise exception 'QB-RLS-002 anon table access'; end if;
 if has_table_privilege('authenticated','beauty.taste_sessions','update') then raise exception 'QB-AUTH-001 client lifecycle update'; end if;
 if has_column_privilege('authenticated','beauty.taste_sessions','state','insert') then raise exception 'QB-AUTH-002 client state insertion'; end if;
 if not has_column_privilege('authenticated','beauty.taste_sessions','purpose','insert') then raise exception 'QB-AUTH-003 missing bounded session insert'; end if;
 if has_table_privilege('authenticated','beauty.preference_evidence','insert') then raise exception 'QB-AUTH-004 client derived-evidence insert'; end if;
 if not has_table_privilege('service_role','beauty.preference_evidence','insert') then raise exception 'QB-SERVICE-001 missing service writer'; end if;
end $$;

insert into auth.users(id,aud,role,email,raw_app_meta_data,raw_user_meta_data,created_at,updated_at) values
 ('11111111-1111-4111-8111-111111111111','authenticated','authenticated','qb-a@example.invalid','{"provider":"email","providers":["email"]}','{}',now(),now()),
 ('22222222-2222-4222-8222-222222222222','authenticated','authenticated','qb-b@example.invalid','{"provider":"email","providers":["email"]}','{}',now(),now())
on conflict(id) do nothing;

insert into beauty.taste_sessions(id,actor_id,purpose,context) values
 ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1','11111111-1111-4111-8111-111111111111','everyday-lip','{"lighting":"daylight"}'),
 ('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbb2','22222222-2222-4222-8222-222222222222','everyday-lip','{"lighting":"daylight"}');
insert into beauty.taste_options(id,session_id,actor_id,purpose,option_key,label,attributes) values
 ('a0000000-0000-4000-8000-000000000001','aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1','11111111-1111-4111-8111-111111111111','everyday-lip','rose-satin','Rose Satin','{"finish":"satin","tone":"muted"}'),
 ('a0000000-0000-4000-8000-000000000002','aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1','11111111-1111-4111-8111-111111111111','everyday-lip','berry-matte','Berry Matte','{"finish":"matte","tone":"vivid"}'),
 ('b0000000-0000-4000-8000-000000000001','bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbb2','22222222-2222-4222-8222-222222222222','everyday-lip','peach-gloss','Peach Gloss','{"finish":"gloss","tone":"warm"}'),
 ('b0000000-0000-4000-8000-000000000002','bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbb2','22222222-2222-4222-8222-222222222222','everyday-lip','plum-satin','Plum Satin','{"finish":"satin","tone":"cool"}');

set local role authenticated;
select set_config('request.jwt.claim.sub','11111111-1111-4111-8111-111111111111',true);
insert into beauty.taste_choices(id,session_id,actor_id,purpose,presented_option_keys,selected_option_key,abstained) values
 ('c0000000-0000-4000-8000-000000000001','aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1','11111111-1111-4111-8111-111111111111','everyday-lip',array['rose-satin','berry-matte'],'rose-satin',false);

do $$ declare rejected boolean:=false; begin
 begin
  insert into beauty.taste_choices(session_id,actor_id,purpose,presented_option_keys,selected_option_key,abstained) values
   ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1','11111111-1111-4111-8111-111111111111','everyday-lip',array['rose-satin','invented-option'],'rose-satin',false);
 exception when check_violation then rejected:=true; end;
 if not rejected then raise exception 'QB-CHOICE-001 invented option accepted'; end if;
end $$;

select set_config('request.jwt.claim.sub','22222222-2222-4222-8222-222222222222',true);
do $$ declare rejected boolean:=false; begin
 if exists(select 1 from beauty.taste_sessions where id='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1') then raise exception 'QB-RLS-003 actor B read actor A'; end if;
 begin
  insert into beauty.taste_choices(session_id,actor_id,purpose,presented_option_keys,selected_option_key,abstained) values
   ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1','22222222-2222-4222-8222-222222222222','everyday-lip',array['peach-gloss','plum-satin'],'peach-gloss',false);
 exception when others then rejected:=true; end;
 if not rejected then raise exception 'QB-SCOPE-001 cross-bound session'; end if;
end $$;
reset role;

insert into beauty.preference_evidence(id,session_id,actor_id,purpose,context_id,preferred_feature,contrasted_feature,source_choice_id,weight,confidence) values
 ('e0000000-0000-4000-8000-000000000001','aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1','11111111-1111-4111-8111-111111111111','everyday-lip','daylight','finish=satin','finish=matte','c0000000-0000-4000-8000-000000000001',0.75,0.80);
insert into beauty.recommendations(id,session_id,actor_id,purpose,option_key,score,confidence,factors,insufficient_evidence,expires_at) values
 ('d0000000-0000-4000-8000-000000000001','aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1','11111111-1111-4111-8111-111111111111','everyday-lip','rose-satin',0.75,0.80,'[{"feature":"finish=satin","effect":0.75}]',false,now()+interval '1 day'),
 ('d0000000-0000-4000-8000-000000000002','bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbb2','22222222-2222-4222-8222-222222222222','everyday-lip','peach-gloss',0.65,0.70,'[]',true,now()+interval '1 day');
insert into beauty.recommendation_evidence_links(recommendation_id,evidence_id,session_id,actor_id,purpose) values
 ('d0000000-0000-4000-8000-000000000001','e0000000-0000-4000-8000-000000000001','aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1','11111111-1111-4111-8111-111111111111','everyday-lip');

do $$ declare rejected boolean:=false; begin
 begin
  insert into beauty.outcome_observations(session_id,actor_id,purpose,recommendation_id,option_key,outcome_kind,tested_in_real_world,note) values
   ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1','11111111-1111-4111-8111-111111111111','everyday-lip','d0000000-0000-4000-8000-000000000002','peach-gloss','preferred',true,'cross-scope');
 exception when foreign_key_violation then rejected:=true; end;
 if not rejected then raise exception 'QB-SCOPE-002 cross-actor recommendation reused'; end if;
end $$;
insert into beauty.outcome_observations(id,session_id,actor_id,purpose,recommendation_id,option_key,outcome_kind,tested_in_real_world,note) values
 ('f0000000-0000-4000-8000-000000000001','aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1','11111111-1111-4111-8111-111111111111','everyday-lip','d0000000-0000-4000-8000-000000000001','rose-satin','preferred',true,'Worn twice in daylight.');

do $$ declare rejected boolean:=false; begin
 begin
  insert into beauty.graph_update_proposals(session_id,actor_id,purpose,recommendation_id,outcome_id,expected_graph_revision,deltas,auto_apply,expires_at) values
   ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1','11111111-1111-4111-8111-111111111111','everyday-lip','d0000000-0000-4000-8000-000000000001','f0000000-0000-4000-8000-000000000001',7,'[{"feature":"finish=satin","delta":0.1}]',true,now()+interval '1 day');
 exception when check_violation then rejected:=true; end;
 if not rejected then raise exception 'QB-GATE-001 auto_apply accepted'; end if;
end $$;
insert into beauty.graph_update_proposals(id,session_id,actor_id,purpose,recommendation_id,outcome_id,expected_graph_revision,deltas,expires_at) values
 ('90000000-0000-4000-8000-000000000001','aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1','11111111-1111-4111-8111-111111111111','everyday-lip','d0000000-0000-4000-8000-000000000001','f0000000-0000-4000-8000-000000000001',7,'[{"feature":"finish=satin","delta":0.1}]',now()+interval '1 day');

do $$ declare rejected boolean:=false; begin
 begin
  insert into beauty.graph_update_decision_mirrors(session_id,actor_id,purpose,proposal_id,decision,human_confirmed,reason,core_decision_ref,decided_at,expires_at) values
   ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1','11111111-1111-4111-8111-111111111111','everyday-lip','90000000-0000-4000-8000-000000000001','approve',true,'expired','decision://qb/expired',now(),now());
 exception when check_violation then rejected:=true; end;
 if not rejected then raise exception 'QB-GATE-002 expired decision accepted'; end if;
end $$;
insert into beauty.graph_update_decision_mirrors(id,session_id,actor_id,purpose,proposal_id,decision,human_confirmed,reason,core_decision_ref,decided_at,expires_at) values
 ('91000000-0000-4000-8000-000000000001','aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1','11111111-1111-4111-8111-111111111111','everyday-lip','90000000-0000-4000-8000-000000000001','reject',true,'not enough evidence','decision://qb/reject',now(),now()+interval '1 day');

do $$ declare rejected boolean:=false; begin
 begin
  insert into beauty.graph_update_receipt_mirrors(session_id,actor_id,purpose,proposal_id,decision_mirror_id,core_receipt_ref,before_revision,after_revision,action_digest,receipt_envelope,applied_at) values
   ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1','11111111-1111-4111-8111-111111111111','everyday-lip','90000000-0000-4000-8000-000000000001','91000000-0000-4000-8000-000000000001','receipt://qb/rejected',7,8,'sha256:'||repeat('a',64),'{}',now());
 exception when check_violation then rejected:=true; end;
 if not rejected then raise exception 'QB-GATE-003 rejection emitted receipt'; end if;
end $$;

insert into beauty.graph_update_decision_mirrors(id,session_id,actor_id,purpose,proposal_id,decision,human_confirmed,reason,core_decision_ref,decided_at,expires_at) values
 ('91000000-0000-4000-8000-000000000002','aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1','11111111-1111-4111-8111-111111111111','everyday-lip','90000000-0000-4000-8000-000000000001','approve',true,'bounded approval','decision://qb/approve',now(),now()+interval '1 day');
insert into beauty.graph_update_receipt_mirrors(id,session_id,actor_id,purpose,proposal_id,decision_mirror_id,core_receipt_ref,before_revision,after_revision,action_digest,receipt_envelope,applied_at) values
 ('92000000-0000-4000-8000-000000000001','aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1','11111111-1111-4111-8111-111111111111','everyday-lip','90000000-0000-4000-8000-000000000001','91000000-0000-4000-8000-000000000002','receipt://qb/approved',7,8,'sha256:'||repeat('b',64),'{"effect":"preference-graph-revision-8"}',now());

do $$ begin
 if to_regclass('beauty.preference_graph') is not null then raise exception 'QB-BOUNDARY-001 projection created canonical graph'; end if;
end $$;
rollback;
