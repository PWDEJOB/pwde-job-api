create table public.profiles (
  id uuid not null,
  full_name text null,
  email text null,
  user_type text null,
  created_at timestamp with time zone null default CURRENT_TIMESTAMP,
  updated_at timestamp with time zone null default CURRENT_TIMESTAMP,
  avatar_url text null,
  resume_url text null,
  skills text null,
  front_id_url text null,
  back_id_url text null,
  employer_id text null,
  constraint profiles_pkey primary key (id),
  constraint profiles_id_fkey foreign KEY (id) references auth.users (id) on delete CASCADE
) TABLESPACE pg_default;

create table public.skills (
  id uuid not null default extensions.uuid_generate_v4 (),
  name text not null,
  category text null,
  created_at timestamp with time zone null default CURRENT_TIMESTAMP,
  constraint skills_pkey primary key (id),
  constraint skills_name_key unique (name)
) TABLESPACE pg_default;

create table public.user_skills (
  id uuid not null default extensions.uuid_generate_v4 (),
  user_id uuid null,
  skill_id uuid null,
  proficiency_level text null,
  created_at timestamp with time zone null default CURRENT_TIMESTAMP,
  constraint user_skills_pkey primary key (id),
  constraint user_skills_user_id_skill_id_key unique (user_id, skill_id),
  constraint user_skills_skill_id_fkey foreign KEY (skill_id) references skills (id) on delete CASCADE,
  constraint user_skills_user_id_fkey foreign KEY (user_id) references profiles (id) on delete CASCADE
) TABLESPACE pg_default;

create index IF not exists idx_user_skills_skill_id on public.user_skills using btree (skill_id) TABLESPACE pg_default;

create index IF not exists idx_user_skills_user_id on public.user_skills using btree (user_id) TABLESPACE pg_default;

create table public.notifications (
  id uuid not null default extensions.uuid_generate_v4 (),
  user_id uuid null,
  type text not null,
  title text not null,
  message text null,
  read boolean null default false,
  created_at timestamp with time zone null default CURRENT_TIMESTAMP,
  constraint notifications_pkey primary key (id),
  constraint notifications_user_id_fkey foreign KEY (user_id) references profiles (id) on delete CASCADE
) TABLESPACE pg_default;

create index IF not exists idx_notifications_user_id on public.notifications using btree (user_id) TABLESPACE pg_default;

create table public.messages (
  id uuid not null default extensions.uuid_generate_v4 (),
  sender_id uuid null,
  receiver_id uuid null,
  content text not null,
  read boolean null default false,
  created_at timestamp with time zone null default CURRENT_TIMESTAMP,
  constraint messages_pkey primary key (id),
  constraint messages_receiver_id_fkey foreign KEY (receiver_id) references profiles (id) on delete CASCADE,
  constraint messages_sender_id_fkey foreign KEY (sender_id) references profiles (id) on delete CASCADE
) TABLESPACE pg_default;

create index IF not exists idx_messages_receiver_id on public.messages using btree (receiver_id) TABLESPACE pg_default;

create index IF not exists idx_messages_sender_id on public.messages using btree (sender_id) TABLESPACE pg_default;

create table public.jobs (
  id uuid not null default extensions.uuid_generate_v4 (),
  employer_id uuid null,
  title text not null,
  description text null,
  requirements text null,
  location text null,
  job_type text null,
  salary_range text null,
  status text null default 'open'::text,
  created_at timestamp with time zone null default CURRENT_TIMESTAMP,
  updated_at timestamp with time zone null default CURRENT_TIMESTAMP,
  constraint jobs_pkey primary key (id),
  constraint jobs_employer_id_fkey foreign KEY (employer_id) references profiles (id) on delete CASCADE
) TABLESPACE pg_default;

create index IF not exists idx_jobs_employer_id on public.jobs using btree (employer_id) TABLESPACE pg_default;

create table public.job_skills (
  id uuid not null default extensions.uuid_generate_v4 (),
  job_id uuid null,
  skill_id uuid null,
  required_proficiency_level text null,
  created_at timestamp with time zone null default CURRENT_TIMESTAMP,
  constraint job_skills_pkey primary key (id),
  constraint job_skills_job_id_skill_id_key unique (job_id, skill_id),
  constraint job_skills_job_id_fkey foreign KEY (job_id) references jobs (id) on delete CASCADE,
  constraint job_skills_skill_id_fkey foreign KEY (skill_id) references skills (id) on delete CASCADE
) TABLESPACE pg_default;

create index IF not exists idx_job_skills_job_id on public.job_skills using btree (job_id) TABLESPACE pg_default;

create index IF not exists idx_job_skills_skill_id on public.job_skills using btree (skill_id) TABLESPACE pg_default;

create table public.job_applications (
  id uuid not null default extensions.uuid_generate_v4 (),
  job_id uuid null,
  applicant_id uuid null,
  status text null default 'pending'::text,
  applicant_name text null,
  applicant_email text null,
  created_at timestamp with time zone null default CURRENT_TIMESTAMP,
  updated_at timestamp with time zone null default CURRENT_TIMESTAMP,
  constraint job_applications_pkey primary key (id),
  constraint job_applications_job_id_applicant_id_key unique (job_id, applicant_id),
  constraint job_applications_applicant_id_fkey foreign KEY (applicant_id) references profiles (id) on delete CASCADE,
  constraint job_applications_job_id_fkey foreign KEY (job_id) references jobs (id) on delete CASCADE
) TABLESPACE pg_default;

create index IF not exists idx_job_applications_applicant_id on public.job_applications using btree (applicant_id) TABLESPACE pg_default;

create index IF not exists idx_job_applications_job_id on public.job_applications using btree (job_id) TABLESPACE pg_default;