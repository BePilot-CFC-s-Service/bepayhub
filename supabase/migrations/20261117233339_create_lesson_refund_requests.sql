create table public.lesson_refund_requests (
	lesson_id bigint primary key references public.lesson(id),
	payment_id bigint not null unique references public.payment(id),
	created_at timestamptz not null default now()
);

alter table public.lesson_refund_requests enable row level security;
revoke all on table public.lesson_refund_requests from public, anon, authenticated;
grant select, insert on table public.lesson_refund_requests to service_role;
