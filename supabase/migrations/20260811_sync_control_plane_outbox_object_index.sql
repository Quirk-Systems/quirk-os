-- Cover the projection_outbox object foreign key for object-scoped delivery and cleanup queries.
create index if not exists projection_outbox_object_id_idx
  on quirk_sync.projection_outbox(object_id);
