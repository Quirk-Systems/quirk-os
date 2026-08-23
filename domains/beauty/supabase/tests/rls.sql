-- Run only in an isolated project after 0001_quirk_beauty_taste_engine.sql.
-- This script uses temporary auth users and rolls back all fixture data.

begin;

insert into auth.users (id, instance_id, aud, role, email, encrypted_password, email_confirmed_at, created_at, updated_at)
values
  ('11111111-1111-4111-8111-111111111111', '00000000-0000-0000-0000-000000000000', 'authenticated', 'authenticated', 'beauty-a@example.invalid', '', now(), now(), now()),
  ('22222222-2222-4222-8222-222222222222', '00000000-0000-0000-0000-000000000000', 'authenticated', 'authenticated', 'beauty-b@example.invalid', '', now(), now(), now())
on conflict (id) do nothing;

insert into quirk_beauty_private.taste_sessions (id, actor_id, purpose, context)
values
  ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa', '11111111-1111-4111-8111-111111111111', 'personal_beauty_recommendation', '{"fixture":"A"}'),
  ('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb', '22222222-2222-4222-8222-222222222222', 'personal_beauty_recommendation', '{"fixture":"B"}');

set local role authenticated;
set local "request.jwt.claim.sub" = '11111111-1111-4111-8111-111111111111';

-- User A sees exactly one session.
do $$
begin
  if (select count(*) from quirk_beauty_private.taste_sessions) <> 1 then
    raise exception 'RLS FAIL: user A session visibility';
  end if;
end $$;

-- User A can append an explicit choice to own session.
insert into quirk_beauty_private.taste_choices (
  id, session_id, actor_id, purpose, context_id, presented_option_keys,
  selected_option_key, abstained, source_type, captured_at
) values (
  'choice:rls-a', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
  '11111111-1111-4111-8111-111111111111', 'personal_beauty_recommendation',
  'context:rls', array['a','b'], 'a', false, 'explicit_human_choice', now()
);

-- Cross-user insertion must be rejected. The block succeeds only on an access/FK failure.
do $$
begin
  begin
    insert into quirk_beauty_private.taste_choices (
      id, session_id, actor_id, purpose, context_id, presented_option_keys,
      selected_option_key, abstained, source_type, captured_at
    ) values (
      'choice:rls-cross-user', 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb',
      '22222222-2222-4222-8222-222222222222', 'personal_beauty_recommendation',
      'context:rls', array['a','b'], 'a', false, 'explicit_human_choice', now()
    );
    raise exception 'RLS FAIL: cross-user insert unexpectedly succeeded';
  exception when insufficient_privilege or foreign_key_violation or check_violation then
    null;
  end;
end $$;

-- Authenticated users cannot write derived evidence or core mirrors.
do $$
begin
  begin
    insert into quirk_beauty_private.preference_evidence (
      id, session_id, actor_id, purpose, context_id, preferred_feature,
      contrasted_feature, source_choice_id, source_type, weight, confidence, recorded_at
    ) values (
      'evidence:rls-forbidden', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
      '11111111-1111-4111-8111-111111111111', 'personal_beauty_recommendation',
      'context:rls', 'finish=satin', 'finish=matte', 'choice:rls-a',
      'explicit_human_choice', 1, 0.7, now()
    );
    raise exception 'RLS FAIL: derived evidence write unexpectedly succeeded';
  exception when insufficient_privilege then
    null;
  end;
end $$;

reset role;
rollback;
